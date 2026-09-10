# Warehouse AI Video Intelligence

A small end-to-end prototype for analysing warehouse videos with a vision-language model and turning the observations into structured event logs.

The notebook takes a warehouse video, sends it to Gemini for temporal analysis, validates the returned events, maps detected behaviours to handling rules, and provides a simple command-line assistant for querying the results.

## What it does

```text
Warehouse Video
      ↓
Video metadata + upload
      ↓
Gemini VLM analysis
      ↓
Structured event JSON
      ↓
Schema + timestamp validation
      ↓
Handling rules
      ↓
warehouse_event_log.json
      ↓
Local event queries / Gemini reasoning
```

The system is intentionally restricted to a fixed set of warehouse behaviours rather than asking the model to classify anything it wants.

## Supported behaviours

The current implementation looks for:

- `product_dropped`
- `product_dragged`
- `product_thrown`
- `product_rolling`
- `rough_handling`
- `improper_stacking`
- `unstable_stacking`
- `product_outside_designated_area`
- `improper_equipment_usage`
- `unsafe_loading_sequence`

Each detected event can contain:

- Event ID
- Start and end timestamps
- Behaviour(s)
- Risk level
- Risk score
- Confidence
- Visual evidence
- Potential consequence
- Recommended action
- Event status
- Mapped warehouse handling rules

## Why the validation layer is there

The model output is treated as untrusted data.

Before the event log is used, the notebook checks things such as:

- required fields are present
- behaviour names belong to the predefined list
- risk score is between 0 and 100
- confidence is between 0 and 1
- status and risk level use valid values
- timestamps are inside the actual video duration
- `end_time` is not before `start_time`

The real video duration is obtained with OpenCV and is also passed to the model, which helps avoid timestamps that fall outside the uploaded video.

## Grounding / hallucination handling

The assistant does not send every question to Gemini.

Questions that can be answered directly from the event log are handled locally. For example:

- event count
- detected behaviours
- HIGH-risk events
- highest-risk event
- incident timeline
- details of a specific event

There is also a small protection layer for information that the video/event log does not provide, such as:

- SKU
- product price
- monetary loss
- exact product weight
- exact drop height
- injury information
- identity/responsibility

For these questions, the assistant returns:

> I could not find this information in the available event logs.

Only questions that actually require reasoning are passed to Gemini.

## Event status

The notebook distinguishes between:

- `observed_behaviour` — something visible in the video
- `potential_risk` — the behaviour creates a possible operational risk
- `confirmed_damage` — actual product damage is visibly confirmed

The analysis prompt explicitly prevents the model from claiming confirmed damage unless it is clearly visible.

## Tech stack

- Python
- Google Gemini API
- `google-genai`
- OpenCV
- JSON
- Google Colab

The notebook currently uses:

```text
gemini-3.1-flash-lite
```

## Running the notebook

### 1. Open the notebook

Open `Warehouse_AI_Video_Intelligence_Notebook(1).ipynb` in Google Colab.

### 2. Install dependencies

The notebook installs the required packages automatically:

```bash
pip install -q -U google-genai opencv-python
```

### 3. Provide a Gemini API key

The notebook first looks for `GEMINI_API_KEY` in Colab userdata or environment variables.

If it is not found, it asks for the key interactively.

For Colab, adding the key to Secrets as `GEMINI_API_KEY` is the cleaner option.

### 4. Upload a warehouse video

Run the upload cell and select the video you want to analyse.

The notebook then reads the video's FPS, frame count and duration before uploading it to Gemini.

### 5. Run the analysis

Gemini returns the analysis as JSON. The notebook parses the response and validates every event.

The resulting event log is saved as:

```text
warehouse_event_log.json
```

### 6. Use the assistant

After the analysis, the notebook starts a simple interactive prompt.

Example:

```text
You: How many events were detected?

You: Which events are HIGH risk?

You: Give me the timeline of all incidents.

You: Tell me everything about EVT_001.

You: How could EVT_001 have been prevented?
```

Type `exit` to stop.

## Example event structure

A detected event follows this general structure:

```json
{
  "event_id": "EVT_001",
  "start_time": "00:12",
  "end_time": "00:18",
  "behavior": ["product_dragged"],
  "risk_level": "HIGH",
  "risk_score": 85,
  "evidence": "A package is visibly dragged across the floor.",
  "potential_consequence": ["product_damage"],
  "recommended_action": "Use suitable handling equipment instead of dragging products.",
  "confidence": 0.95,
  "status": "potential_risk"
}
```

The exact values depend on the uploaded video.

## Query routing

The assistant follows a simple three-step path:

1. **Local lookup**  
   Try to answer from the generated event log.

2. **Unavailable-data check**  
   If the question asks for information that is not available, return the grounded fallback response.

3. **Gemini reasoning**  
   If the question needs interpretation or reasoning, send the event data and question to Gemini.

This keeps straightforward queries independent of another API call and reduces unnecessary model usage.

## Reliability choices

A few implementation choices are deliberate:

- Gemini SDK retries are limited to one attempt.
- Automatic function calling is disabled.
- The VLM response is requested as JSON.
- Model temperature is kept low (`0.1`).
- Video timestamps are checked against the actual video duration.
- Event fields are validated before being used.
- Reasoning is grounded on the generated event log rather than the original video.
- API failures such as rate limits and temporary unavailability are handled with readable messages.

## Limitations

This is a prototype, not a production warehouse monitoring system.

In particular:

- Detection quality depends on the uploaded video's camera angle, resolution and visibility.
- The model only detects the predefined behaviour categories.
- No object tracking or dedicated action-detection model is used.
- The system does not independently verify physical damage.
- The generated risk score is model-produced and should not be treated as a calibrated safety metric.
- The current assistant is a notebook-based CLI rather than a deployed application.
- Event storage is currently a local JSON file.

For a production version, the validation and event pipeline could be separated into services, with persistent storage, monitoring, authentication and a proper review interface added around it.

## Project structure

```text
.
├── Warehouse_AI_Video_Intelligence_Notebook(1).ipynb
├── warehouse_event_log.json        # generated after analysis
└── README.md
```

## Demo questions

### Event-log queries

```text
What risky behaviours were detected in this video?
How many events were detected?
Which events are HIGH risk?
Which event has the highest risk score?
Give me the timeline of all incidents.
Tell me everything about EVT_001.
```

### Reasoning queries

```text
Why was EVT_001 classified as HIGH risk?
What visual evidence supports this classification?
How could EVT_001 have been prevented?
What should the warehouse supervisor do?
Did actual product damage occur or was it only a potential risk?
```

### Grounding tests

```text
What was the monetary value of the product?
What was the exact weight of the product?
What was the product SKU?
Was anyone injured?
```

These should return the unavailable-data response when the requested information is not present in the event log.
