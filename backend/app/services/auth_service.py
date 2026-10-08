import secrets

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token

def register_user(db: Session, data: UserCreate) -> User:
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered."
        )
    user = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def login_user(db: Session, email: str, password: str) -> str:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )

    token = create_access_token(data={"sub": user.email})
    return token


def google_login(db: Session, credential: str) -> str:
    """Verify a Google ID token, create the user on first sign-in, return our own JWT."""
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured on the server.")
    from google.auth.transport import requests as google_requests  # imported here so the app boots without it
    from google.oauth2 import id_token

    try:
        info = id_token.verify_oauth2_token(credential, google_requests.Request(), settings.google_client_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google sign-in. Please try again.")
    if not info.get("email_verified"):
        raise HTTPException(status_code=401, detail="Your Google email is not verified.")

    email = info["email"].lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            name=(info.get("name") or email.split("@")[0])[:120],
            email=email,
            hashed_password=hash_password(secrets.token_urlsafe(32)),  # random: Google users have no password
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is inactive.")
    return create_access_token(data={"sub": user.email})
