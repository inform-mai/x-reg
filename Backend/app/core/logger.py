import logging
import sys
from logging.handlers import RotatingFileHandler
import os


def setup_logging():
    """
    Настраивает логирование для всего приложения.
    Выводит логи в консоль и в файл app.log с автоматической ротацией.
    """
    # Создаем папку для логов, если её нет
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Формат логов: Дата Время | Уровень | Имя модуля | Сообщение
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # 1. Хендлер для вывода в консоль (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # 2. Хендлер для вывода в файл (с ротацией: макс 5 МБ, храним 3 старых файла)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # Получаем корневой логгер и очищаем старые хендлеры (чтобы не дублировать логи)
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Добавляем наши хендлеры
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Устанавливаем общий уровень логирования (INFO)
    root_logger.setLevel(logging.INFO)

    # Отключаем слишком подробные логи от сторонних библиотек (например, uvicorn.access)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)