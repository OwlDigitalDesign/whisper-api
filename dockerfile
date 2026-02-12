FROM python:3.10-slim

# Avoid interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System dependencies (ffmpeg is CRITICAL)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Copy dependencies first (better layer caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Required directories (prevents permission denied issues)
RUN mkdir -p /.cache /home/whisper && \
    chmod -R 777 /.cache /home/whisper

# Environment variables used by the project
ENV WHISPER_CACHE_DIR=/.cache
ENV HF_HOME=/.cache

EXPOSE 8000

CMD ["./start.sh"]
