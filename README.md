# Faster Whisper API

REST API for Faster Whisper: sync and async transcription with MD5 cache, video-to-audio via ffmpeg, and webhook callback for async jobs. Designed for LXC/Proxmox and n8n integration.

---

## Quick reference

| Item | Value |
|------|--------|
| **Install path** | `/opt/whisper-api` |
| **Config (production)** | `/etc/whisper-api/config.yaml` |
| **Data (cache, temp)** | `/var/lib/whisper/` |
| **Service** | `whisper-api.service` |
| **User** | `whisper` (system, no login) |
| **Port** | `8000` (configurable) |

---

## Repo layout and config files

- **`config.yaml`** (committed): default config for development. Used by `./start.sh`; paths are local to the repo (e.g. `./.cache/cache.db`, `./.cache/tmp`).
- **`config.yaml.example`** (committed): production template (paths under `/var/lib/whisper`). Copy to `config.production.yaml`, edit, then run `./setup.sh`; setup copies `config.production.yaml` to `/etc/whisper-api/config.yaml`.
- **`config.production.yaml`** (not committed, in `.gitignore`): your production config. Create with `cp config.yaml.example config.production.yaml`, edit it, then run `sudo ./setup.sh`.

---

## Run from repo (no install)

From the repo root (e.g. `~/dev/whisper-api`):

```bash
./install-deps.sh   # optional: install Python 3.9+, ffmpeg, venv (run with sudo if needed)
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt   # optional: local venv
./start.sh
```

Uses `config.yaml` in the repo; cache and temp go under `./.cache/`. No sudo or systemd required.

---

## Configuration

Config is read (in order) from: `WHISPER_API_CONFIG` env, `config.yaml` in current directory, `/etc/whisper-api/config.yaml`.

### Options

| Option | Type | Default | Description |
|-------|------|---------|--------------|
| `host` | string | `"0.0.0.0"` | Bind address for the API server |
| `port` | int | `8000` | TCP port |
| `model` | string | `"small"` | Whisper model: `tiny`, `base`, `small`, `medium`, `large-v3`, etc. |
| `device` | string | `"cpu"` | `cpu` or `cuda` |
| `compute_type` | string | `"int8"` | `int8` (recommended on CPU), `float32`, or GPU types |
| `cache_db_path` | string | `"/var/lib/whisper/cache.db"` | SQLite cache file (MD5 → transcription) |
| `temp_dir` | string | `"/var/lib/whisper/tmp"` | Directory for temporary uploads (cleaned after each request) |
| `request_timeout_seconds` | int | `3600` | Keep-alive / long request timeout (uvicorn) |
| `webhook_timeout_seconds` | int | `10` | Timeout for POST to webhook URL (async endpoint) |
| `beam_size` | int | `5` | Whisper beam size |
| `language` | string \| null | `null` | Force language (e.g. `"en"`) or auto-detect |
| `vad_filter` | bool | `true` | Use VAD to filter silence |

After editing production config, restart: `sudo systemctl restart whisper-api.service`.

---

## API endpoints

Base URL: `http://<host>:8000` (or your configured host/port).

### GET /health

Health check. Returns JSON with `status`, `config_loaded`, `ffmpeg_available`, `model_loaded` (and `model_error` if model failed to load).

```bash
curl http://localhost:8000/health
```

### POST /transcribe (synchronous)

Upload an audio or video file; get transcription in the response. Uses cache by file MD5 unless `force=true`.

- **Content-Type**: `multipart/form-data`
- **Body**: field `file` (audio or video)
- **Query**: `force` (optional): `true` to ignore cache and re-transcribe

**Response (JSON)**: `text`, `segments` (list of `{ "start", "end", "text" }`), `language`, `from_cache`.

```bash
curl -X POST "http://localhost:8000/transcribe" -F "file=@/path/to/audio.mp3"
curl -X POST "http://localhost:8000/transcribe?force=true" -F "file=@/path/to/video.mp4"
```

### POST /transcribe-async (asynchronous)

Same input as `/transcribe`, plus form fields `job_id` and `webhook_url`. Returns **202 Accepted** and processes in the background; when done, POSTs the result to `webhook_url`.

- **Body**: `file`, `job_id`, `webhook_url`
- **Query**: `force` (optional)

**Response (202)**: `job_id`, `status: "accepted"`, `message: "Processing in background"`.

**Webhook payload**: On success: `job_id`, `status: "completed"`, `text`, `segments`, `language`, `from_cache`. On error: `job_id`, `status: "failed"`, `error`.

```bash
curl -X POST "http://localhost:8000/transcribe-async" \
  -F "file=@/path/to/long-audio.mp3" \
  -F "job_id=my-job-123" \
  -F "webhook_url=https://your-n8n.com/webhook/whisper-done"
```

---

## n8n usage

- **Synchronous**: HTTP Request → POST to `http://<whisper-host>:8000/transcribe`, body = file, long timeout (e.g. 600 s).
- **Asynchronous**: HTTP Request → POST to `http://<whisper-host>:8000/transcribe-async` with form fields `file`, `job_id` (e.g. `{{ $execution.id }}`), `webhook_url` (n8n Webhook node URL). When done, the API calls your webhook.

---

## Service management (production)

| Action | Command |
|--------|---------|
| Start | `sudo systemctl start whisper-api.service` |
| Stop | `sudo systemctl stop whisper-api.service` |
| Restart | `sudo systemctl restart whisper-api.service` |
| Enable at boot | `sudo systemctl enable whisper-api.service` |
| Status | `sudo systemctl status whisper-api.service` |
| Logs (follow) | `sudo journalctl -u whisper-api.service -f` |

---

## Installation (production from source)

1. Clone or copy the repo (e.g. to `~/dev/whisper-api`).
2. Optional: copy and edit production config:
   ```bash
   cp config.yaml.example config.production.yaml
   # edit config.production.yaml (port, model, paths, etc.)
   ```
3. Install system deps (optional; setup can run it):
   ```bash
   sudo ./install-deps.sh
   ```
4. Run setup:
   ```bash
   sudo ./setup.sh
   ```
   This creates user `whisper`, directories `/opt/whisper-api`, `/var/lib/whisper`, `/etc/whisper-api`, copies `src/` and requirements to `/opt/whisper-api`, creates venv and installs Python deps, installs the systemd unit. If `config.production.yaml` exists, it is copied to `/etc/whisper-api/config.yaml`; otherwise `config.yaml.example` is copied there.
5. Enable and start:
   ```bash
   sudo systemctl enable --now whisper-api.service
   ```

---

## Requirements

- **Python** 3.9+
- **ffmpeg** in PATH (for video → audio extraction)
- **Config**: `/etc/whisper-api/config.yaml` in production, or `config.yaml` in repo / `WHISPER_API_CONFIG` for development

First run downloads the Whisper model (see `model` in config). For 12 GB RAM (CPU), use `small` or `medium` with `compute_type: int8` and `device: cpu`. For **GPU** (NVIDIA CUDA), set `device: "cuda"` and `compute_type: "float16"` (or `int8`) in config; requires CUDA and a GPU-enabled faster-whisper install.

---

## File layout

**Repo root**: `config.yaml`, `config.yaml.example`, `config.production.yaml` (gitignored), `requirements.txt`, `install-deps.sh`, `start.sh`, `setup.sh`, `whisper-api.service`, `README.md`, `.gitignore`.

**`src/`** (copied to `/opt/whisper-api/` by setup): `main.py`, `config.py`, `cache.py`, `transcribe.py`, `routes.py`, `run_server.py`.

**Production**: Config in `/etc/whisper-api/config.yaml`; cache and temp in `/var/lib/whisper/`.
