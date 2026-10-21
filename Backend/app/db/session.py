from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Backend.app.db.models import Base
from Backend.app.config import get_settings


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        kwargs = {"pool_pre_ping": True}
        _engine = create_engine(settings.database_url, **kwargs)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False)
    return _SessionLocal


def init_db():
    Base.metadata.create_all(get_engine())


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
