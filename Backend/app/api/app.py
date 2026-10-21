from fastapi import FastAPI

from Backend.app.api.routes import router


def create_app():
    app = FastAPI(title="X-reg", version="1.0.0")
    app.include_router(router)
    return app