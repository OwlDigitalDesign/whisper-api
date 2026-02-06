"""Entrypoint: read config and run uvicorn."""
from __future__ import annotations

import logging
import uvicorn

from config import get_config

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    cfg = get_config()
    uvicorn.run(
        "main:app",
        host=cfg.host,
        port=cfg.port,
        timeout_keep_alive=cfg.request_timeout_seconds,
        reload=False,
    )
