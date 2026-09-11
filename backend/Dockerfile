# Minimal image for the Fragility Passport backend. Built by docker-compose.yml
# (context: ./backend) — not part of the original scaffold, added because
# docker-compose needs something to build.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
