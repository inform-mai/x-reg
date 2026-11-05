import uvicorn

from app.config import get_settings
from app.db.session import init_db
from app.api.app import create_app
from app.core.logger import setup_logging

__all__ = ["app", "create_app"]

# Инициализируем настройку логов
setup_logging()

if __name__ == "__main__":
    settings = get_settings()
    init_db()
    config = uvicorn.Config(
        "app.api.app:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
    )
    uvicorn.Server(config).run()