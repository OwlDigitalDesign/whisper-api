"""Load config from YAML: WHISPER_API_CONFIG, config.yaml in CWD/install dir, or /etc/whisper-api/config.yaml."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class Config:
    host: str = "0.0.0.0"
    port: int = 8000
    model: str = "small"
    device: str = "cpu"
    compute_type: str = "int8"
    cache_db_path: str = "/var/lib/whisper/cache.db"
    temp_dir: str = "/var/lib/whisper/tmp"
    request_timeout_seconds: int = 3600
    webhook_timeout_seconds: int = 10
    beam_size: int = 5
    language: Optional[str] = None
    vad_filter: bool = True

    @classmethod
    def from_dict(cls, d: dict) -> "Config":
        return cls(
            host=d.get("host", cls.host),
            port=int(d.get("port", cls.port)),
            model=d.get("model", cls.model),
            device=d.get("device", cls.device),
            compute_type=d.get("compute_type", cls.compute_type),
            cache_db_path=d.get("cache_db_path", cls.cache_db_path),
            temp_dir=d.get("temp_dir", cls.temp_dir),
            request_timeout_seconds=int(d.get("request_timeout_seconds", cls.request_timeout_seconds)),
            webhook_timeout_seconds=int(d.get("webhook_timeout_seconds", cls.webhook_timeout_seconds)),
            beam_size=int(d.get("beam_size", cls.beam_size)),
            language=d.get("language"),
            vad_filter=bool(d.get("vad_filter", cls.vad_filter)),
        )


_config: Optional[Config] = None


def _find_config_path() -> Optional[Path]:
    env_path = os.environ.get("WHISPER_API_CONFIG")
    if env_path and os.path.isfile(env_path):
        return Path(env_path)
    etc = Path("/etc/whisper-api/config.yaml")
    if etc.is_file():
        return etc
    cwd = Path.cwd()
    for p in (cwd / "config.yaml", cwd / "config.yaml.example"):
        if p.is_file():
            return p
    return None


def get_config() -> Config:
    global _config
    if _config is not None:
        return _config
    path = _find_config_path()
    if path:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        _config = Config.from_dict(data)
    else:
        _config = Config()
    return _config


def reset_config() -> None:
    """Reset cached config (e.g. for tests)."""
    global _config
    _config = None
