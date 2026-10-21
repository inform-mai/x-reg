from fastapi import Depends
from sqlalchemy.orm import Session

from Backend.app.db.models import User
from Backend.app.db.repo import UserRepo
from Backend.app.db.session import get_session
from Backend.app.config import Settings, get_settings



def get_current_user(
    db: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> User:
    return UserRepo(db).get_or_create_dev_user(
        email=settings.dev_user_email,
        full_name=settings.dev_user_full_name,
    )
