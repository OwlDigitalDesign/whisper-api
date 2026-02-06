"""API routes: /health, /transcribe, /transcribe-async."""
from __future__ import annotations

import logging
import shutil
import threading
import time
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from config import get_config
from transcribe import transcribe_file

router = APIRouter()
logger = logging.getLogger(__name__)

# Set by main.py lifespan when model is loaded (or fails)
model_loaded: bool = False
model_error: Optional[str] = None


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


@router.get("/health")
def health():
    cfg = get_config()
    return {
        "status": "ok",
        "config_loaded": True,
        "ffmpeg_available": _ffmpeg_available(),
        "model_loaded": model_loaded,
        **({"model_error": model_error} if model_error else {}),
    }


@router.post("/transcribe")
async def transcribe_sync(
    file: UploadFile = File(...),
    force: bool = False,
):
    cfg = get_config()
    temp_dir = Path(cfg.temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    path = temp_dir / (file.filename or "upload")
    try:
        content = await file.read()
        path.write_bytes(content)
        result = transcribe_file(path, force=force)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass


def _run_async_transcribe(file_path: Path, force: bool, job_id: str, webhook_url: str) -> None:
    cfg = get_config()
    logger.info("Async job %s: starting Whisper transcription (file=%s, force=%s)", job_id, file_path.name, force)
    start = time.monotonic()
    try:
        result = transcribe_file(file_path, force=force)
        elapsed = time.monotonic() - start
        logger.info("Async job %s: Whisper completed in %.1fs (from_cache=%s)", job_id, elapsed, result.get("from_cache", False))
        payload = {"job_id": job_id, "status": "completed", **result}
    except Exception as e:
        elapsed = time.monotonic() - start
        logger.warning("Async job %s: Whisper failed after %.1fs: %s", job_id, elapsed, e)
        payload = {"job_id": job_id, "status": "failed", "error": str(e)}
    finally:
        try:
            if file_path.exists():
                file_path.unlink()
        except OSError:
            pass
    timeout = cfg.webhook_timeout_seconds
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(webhook_url, json=payload)
        if resp.status_code >= 200 and resp.status_code < 300:
            logger.info("Async job %s: webhook delivered to %s (HTTP %d)", job_id, webhook_url, resp.status_code)
        else:
            logger.warning(
                "Async job %s: webhook returned HTTP %d for %s (body: %s)",
                job_id, resp.status_code, webhook_url, resp.text[:200] if resp.text else "",
            )
    except Exception as e:
        logger.warning("Async job %s: webhook failed: %s", job_id, e)


@router.post("/transcribe-async")
async def transcribe_async(
    file: UploadFile = File(...),
    job_id: str = Form(...),
    webhook_url: str = Form(...),
    force: bool = False,
):
    cfg = get_config()
    temp_dir = Path(cfg.temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    path = temp_dir / (file.filename or "upload")
    content = await file.read()
    path.write_bytes(content)
    thread = threading.Thread(
        target=_run_async_transcribe,
        args=(path, force, job_id, webhook_url),
    )
    thread.start()
    return JSONResponse(
        status_code=202,
        content={
            "job_id": job_id,
            "status": "accepted",
            "message": "Processing in background",
        },
    )
