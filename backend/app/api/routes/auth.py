"""
Authentication API Routes.
Handles user registration, login, and token management.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...db.models import User
from ...core.security import hash_password, verify_password, create_access_token
from ...core.rate_limiter import rate_limiter
from ...utils.logger import log

router = APIRouter(prefix="/auth", tags=["authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    rate_limiter.check_or_raise(f"register_{request.email}")

    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered.")

    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        display_name=request.display_name or request.email.split("@")[0],
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    log.info(f"User registered: {user.id}")

    return TokenResponse(access_token=token, user_id=user.id, email=user.email)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login and get access token."""
    rate_limiter.check_or_raise(f"login_{request.email}")

    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    token = create_access_token(data={"sub": str(user.id)})
    log.info(f"User logged in: {user.id}")

    return TokenResponse(access_token=token, user_id=user.id, email=user.email)
