# session.py - всё, что связано с подключением к базе данных.
# Здесь создаются:
#   engine (движок)       - объект, который знает, КАК подключиться к БД (адрес из DATABASE_URL)
#                           и держит пул готовых соединений;
#   фабрика сессий        - "конструктор", который по запросу создаёт новые сессии;
#   сессия (Session)      - рабочий сеанс с БД: через неё делают запросы (select),
#                           добавляют/меняют/удаляют объекты, а потом фиксируют (commit)
#                           или отменяют (rollback) изменения.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Backend.app.db.models import Base
from Backend.app.config import get_settings


# Глобальные переменные-"кэши". Изначально None, создаются один раз при первом обращении
# (ленивая инициализация), а дальше переиспользуются - так в приложении всего один engine.
_engine = None
_SessionLocal = None


# Возвращает engine. При первом вызове:
#   - берёт настройки (get_settings читает DATABASE_URL из .env),
#   - создаёт engine через create_engine.
#   pool_pre_ping=True - перед выдачей соединения из пула проверять, что оно живое
#   (если БД перезапускалась, "мёртвое" соединение заменится новым, а не упадёт с ошибкой).
def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        kwargs = {"pool_pre_ping": True}
        _engine = create_engine(settings.database_url, **kwargs)
    return _engine


# Возвращает фабрику сессий (sessionmaker), привязанную к engine.
# autoflush=False - изменения не отправляются в БД автоматически перед каждым запросом,
# а только при явном flush() или commit().
# Вызов get_session_factory()() (две пары скобок) = взять фабрику и создать из неё новую сессию.
def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False)
    return _SessionLocal


# Создаёт в БД все таблицы, описанные в models.py (по Base.metadata), если их ещё нет.
# Уже существующие таблицы не трогает и не изменяет.
# Вызывается один раз при запуске приложения в main.py.
def init_db():
    Base.metadata.create_all(get_engine())


# Генератор сессии - используется как зависимость FastAPI: Depends(get_session).
# На КАЖДЫЙ HTTP-запрос создаётся своя отдельная сессия:
#   1. session = ... - открыть новую сессию;
#   2. yield session - отдать её обработчику запроса (функция-генератор "замирает" здесь,
#      пока обработчик работает);
#   3. если обработчик завершился без ошибок - session.commit(): сохранить изменения в БД;
#   4. если произошла ошибка - session.rollback(): отменить все изменения этого запроса,
#      чтобы в БД не осталось "половины" операции, и пробросить ошибку дальше (raise);
#   5. finally - в любом случае закрыть сессию и вернуть соединение в пул.
def get_session():
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
