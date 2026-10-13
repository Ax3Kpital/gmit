import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.db.models.user import User, UserSession
from app.core.security import hash_password, verify_password, generate_session_token
from app.core.config import settings


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email, User.is_active == True).first()


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_session(db: Session, user: User, user_agent: str | None = None) -> str:
    token = generate_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.session_expire_hours)
    session = UserSession(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
        user_agent=user_agent,
    )
    db.add(session)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return token


def get_session(db: Session, token: str) -> UserSession | None:
    now = datetime.now(timezone.utc)
    session = (
        db.query(UserSession)
        .filter(UserSession.token == token, UserSession.expires_at > now)
        .first()
    )
    if session:
        session.last_used_at = now
        db.commit()
    return session


def delete_session(db: Session, token: str) -> None:
    db.query(UserSession).filter(UserSession.token == token).delete()
    db.commit()


def create_user(db: Session, email: str, password: str) -> User:
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
