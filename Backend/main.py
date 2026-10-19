import logging

import uvicorn

from app.config import get_settings
from app.db.session import init_db
from app.api.app import create_app


__all__ = ["app", "create_app"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


if __name__ == "__main__":
    settings = get_settings()
    init_db()
    config = uvicorn.Config(
        "app.api.app:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info",
    )
    uvicorn.Server(config).run()
