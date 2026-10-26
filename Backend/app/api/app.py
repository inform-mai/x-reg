from fastapi import FastAPI

from app.api.routes import router

from app.core.logger import setup_logging

def create_app() -> FastAPI:
    setup_logging()  # <-- Настраиваем логи при создании приложения
    app = FastAPI(title="X-reg", version="1.0.0")
    app.include_router(router)
    return app

