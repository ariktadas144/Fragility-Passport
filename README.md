# Fragility Passport

**An AI-Powered Warehouse Video Intelligence System**

Fragility Passport is an intelligent CCTV system that monitors how products are handled in a warehouse, understands handling rules specific to each product, and instantly generates actionable incidents when safety protocols are violated.

Unlike generic object detection, Fragility Passport understands the *context* of a product. It connects raw computer vision data to a product-specific handling contract, evaluates the risk, alerts supervisors, and automatically compiles evidence into detailed reports to prevent downstream supply chain damage.

## 📖 The Core Concept: The "Fragility Passport"

Instead of applying uniform rules to an entire warehouse, each product has a "handling contract" or "passport".

For example, a delicate **KD Panel (SKU: ABC-123)** might have a passport that specifies:
- Maximum Tilt: 40°
- Required Orientation: UPRIGHT
- Dragging: NOT ALLOWED
- Throwing: NOT ALLOWED

When the AI detects a "Throwing" behavior, the backend cross-references the product's Fragility Passport. If throwing is not allowed, it registers a **High-Risk Contract Violation**, instantly alerting warehouse supervisors.

## 🚀 Key Features

- **Product-Specific Rule Checking:** Dynamically checks handling behaviors against predefined fragility rules.
- **Risk Engine:** Calculates risk scores based on behavior severity, AI confidence, and passport violations.
- **Actionable Incident Creation:** Transforms raw AI detections into persistent, trackable database events.
- **Evidence Management:** Captures and stores timestamped video frames and clips of violations.
- **Supervisor Dashboard & Alerts:** Real-time dashboard for live monitoring and incident acknowledgment.
- **Automated Incident Reports:** Generates evidence-backed reports with incident metadata, frames, and AI reasoning.
- **VLM & AI Assistant Integration:** Allows supervisors to naturally query warehouse incident data (e.g., *"Which dock had the most high-risk events today?"*).

## 🏗️ Architecture

The system is divided into five major layers:

1. **Camera Layer:** Captures raw warehouse footage.
2. **Video & CV Layer:** YOLO object detection and ByteTrack for tracking trajectories.
3. **AI Understanding Layer:** Custom models and Vision-Language Models (VLM) for behavior reasoning.
4. **Backend Layer:** FastAPI-driven central nervous system holding the Risk Engine, Fragility Passports, and Event Management.
5. **User Application:** Frontend dashboard, AI Assistant, and automated report generation.

### End-to-End Workflow
```text
Video → Object Detection → Behavior AI → Passport Lookup → Risk Engine → Database Storage → Alert & Dashboard → Report
```

## 🛠️ Technology Stack

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite/PostgreSQL
- **Machine Learning:** YOLO (Fine-tuned), ByteTrack, OpenCV, custom VLM integration
- **Frontend:** React (Dashboard, Video Player, Analytics Charts)
- **Deployment:** Docker, Docker Compose, GitHub Actions

## 📂 Project Structure

```text
├── backend/            # FastAPI app, APIs, Services, Database Models, Risk Engine
├── data/               # Seed data, raw videos, processed evidence (frames/clips)
├── demo/               # Demo videos, scenarios, and configurations
├── docs/               # System architecture and API contracts
├── frontend/           # React dashboard and AI assistant UI
├── ml/                 # Detection, tracking, behavior analysis, and VLM logic
├── reports/            # PDF report templates and generated outputs
└── scripts/            # Setup and database seeding scripts
```

## ⚙️ Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.10+
- Node.js 18+

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ariktadas144/Fragility-Passport.git
   cd "Fragility Passport"
   ```

2. **Backend Setup:**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

3. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

*(Alternatively, use `docker-compose up -d` to spin up the entire stack).*

## 📡 API Overview

The backend serves as the core integration layer, exposing routes like:
- `POST /events` - Ingests ML detections and triggers the Risk Engine.
- `GET /events/{event_id}` - Fetches detailed incident data and evidence.
- `GET /dashboard/summary` - Provides aggregations for frontend charts.
- `GET /passports/{product_id}` - Looks up handling rules for a specific product.
- `POST /alerts/{id}/acknowledge` - Supervisor acknowledges an active alert.
- `GET /reports/{event_id}` - Generates an evidence-backed incident report.

## 🤝 Workstreams

This project is built collaboratively across specialized domains:
1. **Data Science / ML:** Custom CV training, object tracking, and behavior detection.
2. **VLM & AI Assistant:** High-level video sequence reasoning and natural language querying.
3. **Frontend:** Real-time dashboards, charts, and video monitoring UI.
4. **Backend & Data Pipeline:** The central integration layer (FastAPI), managing databases, risk logic, and APIs.

## 🔒 Privacy & Compliance

Fragility Passport focuses on identifying **process problems**, not individuals. Tracking IDs are anonymized, and incidents are aggregated by dock, shift, and behavior to provide systemic insights without compromising worker privacy.
