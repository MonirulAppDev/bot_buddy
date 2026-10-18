from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, generate_api_key
from app.services.auth_service import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password
)

router = APIRouter(prefix="/auth", tags=["Authentication & User Management"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, example="reseller_pro")
    email: str = Field(..., example="reseller@example.com")
    password: str = Field(..., min_length=6, example="password123")


class LoginRequest(BaseModel):
    username: str = Field(..., example="admin")
    password: str = Field(..., example="admin123456")


class AddFundsRequest(BaseModel):
    amount: float = Field(..., ge=1.0, le=10000.0, example=50.0)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new SMM panel user with free starting balance and API Key."""
    # Check existing
    res = await db.execute(select(User).where((User.username == payload.username) | (User.email == payload.email)))
    if res.scalars().first():
        raise HTTPException(status_code=400, detail="Username or Email already registered.")

    new_user = User(
        username=payload.username.strip(),
        email=payload.email.strip().lower(),
        hashed_password=hash_password(payload.password),
        api_key=generate_api_key(),
        balance=25.00,  # $25 Free Starting Credit
        role="user"
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = create_access_token({"sub": new_user.id, "username": new_user.username, "role": new_user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "balance": new_user.balance,
            "api_key": new_user.api_key,
            "role": new_user.role
        }
    }


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with username/password to get JWT access token."""
    res = await db.execute(select(User).where(User.username == payload.username.strip()))
    user = res.scalars().first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated.")

    token = create_access_token({"sub": user.id, "username": user.username, "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "balance": user.balance,
            "spent": user.spent,
            "api_key": user.api_key,
            "role": user.role
        }
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current logged-in profile details, balance, and SMM API Key."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "balance": round(current_user.balance, 2),
        "spent": round(current_user.spent, 2),
        "api_key": current_user.api_key,
        "role": current_user.role,
        "created_at": current_user.created_at
    }


@router.post("/regenerate-api-key")
async def regenerate_key(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Generate a new SMM API v2 key for reseller automation."""
    current_user.api_key = generate_api_key()
    await db.commit()
    return {"api_key": current_user.api_key, "message": "New API key generated successfully!"}


@router.post("/add-funds")
async def add_funds(
    payload: AddFundsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Simulate funding user account wallet balance."""
    current_user.balance += payload.amount
    await db.commit()
    return {
        "new_balance": round(current_user.balance, 2),
        "message": f"Successfully credited ${payload.amount:.2f} to your account!"
    }
