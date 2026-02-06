"""Video->audio (ffmpeg), MD5, cache, faster-whisper transcription."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional

from cache import get as cache_get, set as cache_set
from config import get_config

# Video extensions that need ffmpeg extraction
VIDEO_EXTENSIONS = frozenset({".mp4", ".webm", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".m4v"})


def _file_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def _extract_audio_ffmpeg(video_path: Path, out_dir: Path) -> Path:
    out_path = out_dir / "audio.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path), "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(out_path)],
        check=True,
        capture_output=True,
    )
    return out_path


def _run_whisper(audio_path: Path) -> dict[str, Any]:
    cfg = get_config()
    from faster_whisper import WhisperModel

    model = WhisperModel(
        cfg.model,
        device=cfg.device,
        compute_type=cfg.compute_type,
        download_root=None,
        local_files_only=False,
    )
    segments_gen, info = model.transcribe(
        str(audio_path),
        beam_size=cfg.beam_size,
        language=cfg.language,
        vad_filter=cfg.vad_filter,
    )
    segments_list = [{"start": s.start, "end": s.end, "text": s.text} for s in segments_gen]
    text = " ".join(s["text"] for s in segments_list).strip()
    language = info.language or ""
    return {"text": text, "segments": segments_list, "language": language}


def transcribe_file(file_path: Path, force: bool = False) -> dict[str, Any]:
    """
    Transcribe an audio or video file. Uses cache by original file MD5 unless force=True.
    Returns dict with text, segments, language, from_cache.
    """
    cfg = get_config()
    md5 = _file_md5(file_path)
    if not force:
        cached = cache_get(md5)
        if cached is not None:
            return cached

    temp_dir = Path(cfg.temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    work_dir: Optional[Path] = None
    audio_path: Path = file_path
    try:
        if _is_video(file_path):
            work_dir = Path(tempfile.mkdtemp(prefix="whisper_", dir=temp_dir))
            audio_path = _extract_audio_ffmpeg(file_path, work_dir)
        data = _run_whisper(audio_path)
        result = {**data, "from_cache": False}
        cache_set(md5, result)
        return result
    finally:
        if work_dir is not None and work_dir.exists():
            try:
                shutil.rmtree(work_dir)
            except OSError:
                pass
