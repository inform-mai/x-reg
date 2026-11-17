import logging
import sys
from logging.handlers import RotatingFileHandler
from app.config import get_settings
import os


def setup_logging():
    """
    Настраивает логирование для всего приложения.
    Выводит логи в консоль и в файл app.log с автоматической ротацией.
    """
    settings = get_settings()
    log_dir = settings.log_dir
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Формат логов: Дата Время | Уровень | Имя модуля | Сообщение
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")


    # Хендлер для вывода в файл (с ротацией: макс 5 МБ, храним 3 старых файла)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=20 * 1024 * 1024,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # Получаем корневой логгер и очищаем старые хендлеры (чтобы не дублировать логи)
    root_logger = logging.getLogger()

    root_logger.addHandler(file_handler)

    # Устанавливаем общий уровень логирования (INFO)
    root_logger.setLevel(logging.INFO)

    # Отключаем слишком подробные логи от сторонних библиотек (например, uvicorn.access)
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)