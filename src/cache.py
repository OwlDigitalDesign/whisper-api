"""SQLite cache: get/set transcription result by file MD5."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

from config import get_config


def _conn() -> sqlite3.Connection:
    cfg = get_config()
    path = Path(cfg.cache_db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cache (
            md5 TEXT PRIMARY KEY,
            result TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def get(md5: str) -> Optional[dict[str, Any]]:
    """Return cached result for this MD5, or None."""
    conn = _conn()
    try:
        row = conn.execute("SELECT result FROM cache WHERE md5 = ?", (md5,)).fetchone()
        if row is None:
            return None
        return json.loads(row[0])
    finally:
        conn.close()


def set(md5: str, result: dict[str, Any]) -> None:
    """Store result for this MD5."""
    conn = _conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO cache (md5, result) VALUES (?, ?)",
            (md5, json.dumps(result)),
        )
        conn.commit()
    finally:
        conn.close()
