# Basis: Python mit pip
FROM python:3.11-slim

# Abhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis
WORKDIR /app

# Code und requirements reinziehen
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app app
COPY sql sql

ENV PYTHONPATH=/app

# Port für NiceGUI
EXPOSE 8080

# Startbefehl
CMD ["python", "app/main.py"]
