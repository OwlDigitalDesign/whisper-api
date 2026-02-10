FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Define HOME and cache directories
ENV HOME=/app
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV TORCH_HOME=/app/.cache/torch

# Non-root User
RUN addgroup --system api && adduser --system --ingroup api api

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App src code
COPY src ./src
COPY config.yaml ./config.yaml

# Create cache directories and set permissions
RUN mkdir -p /app/.cache/huggingface /app/.cache/torch /app/.cache/tmp \
 && chown -R api:api /app

USER api

EXPOSE 8000
CMD ["python", "src/run_server.py"]

