from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.user import UserCreate, UserOut, Token, UserLogin, GoogleLogin
from app.services.auth_service import register_user, login_user, google_login

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register", response_model=UserOut, status_code=201, summary="Create an account")
def register(data: UserCreate, db: Session = Depends(get_db)):
    return register_user(db, data)

@router.post("/login", response_model=Token, summary="Log in and receive a JWT")
def login(data: UserLogin, db: Session = Depends(get_db)):
    token = login_user(db, data.email, data.password)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/google", response_model=Token, summary="Sign in with a Google ID token")
def google(data: GoogleLogin, db: Session = Depends(get_db)):
    return {"access_token": google_login(db, data.credential), "token_type": "bearer"}
