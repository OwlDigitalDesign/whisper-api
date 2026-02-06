"""FastAPI app and lifespan."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import get_config
from routes import router

# Will be set in lifespan
_whisper_model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _whisper_model
    import routes as routes_mod

    get_config()
    try:
        cfg = get_config()
        from faster_whisper import WhisperModel

        _whisper_model = WhisperModel(
            cfg.model,
            device=cfg.device,
            compute_type=cfg.compute_type,
            download_root=None,
            local_files_only=False,
        )
        routes_mod.model_loaded = True
        routes_mod.model_error = None
    except Exception as e:
        routes_mod.model_loaded = False
        routes_mod.model_error = str(e)
    yield
    _whisper_model = None


app = FastAPI(lifespan=lifespan)
app.include_router(router)
