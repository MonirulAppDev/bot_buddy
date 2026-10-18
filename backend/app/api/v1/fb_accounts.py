import re
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.fb_account import FBAccount
from app.services.facebook_bot import execute_real_facebook_like

router = APIRouter(prefix="/fb-accounts", tags=["Real Facebook Accounts"])


class AddFBAccountRequest(BaseModel):
    account_name: str = Field(..., example="My Main FB Account")
    cookie_data: str = Field(..., example="c_user=100012345678; xs=abcdef123456; fr=...")


class ExecuteRealLikeRequest(BaseModel):
    post_url: str = Field(..., example="https://www.facebook.com/photo?fbid=122103658497500888&set=a.122095228263500888")
    cookie_data: str | None = Field(default=None, description="Optional custom cookie string. If not provided, uses an active saved FB account.")
    headless: bool = Field(default=True, description="Run headless browser or visible browser window")


@router.get("")
async def list_fb_accounts(db: AsyncSession = Depends(get_db)):
    """List connected real Facebook accounts."""
    result = await db.execute(select(FBAccount).order_by(FBAccount.created_at.desc()))
    accounts = result.scalars().all()
    return [
        {
            "id": acc.id,
            "account_name": acc.account_name,
            "fb_user_id": acc.fb_user_id,
            "status": acc.status,
            "total_likes_given": acc.total_likes_given,
            "created_at": acc.created_at
        }
        for acc in accounts
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_fb_account(payload: AddFBAccountRequest, db: AsyncSession = Depends(get_db)):
    """Save a real Facebook account session cookie for automated liking/engaging."""
    # Extract c_user if present
    match = re.search(r"c_user=(\d+)", payload.cookie_data)
    fb_uid = match.group(1) if match else None

    if not fb_uid and "c_user" not in payload.cookie_data:
        raise HTTPException(
            status_code=400,
            detail="Invalid cookie format. Cookie must contain 'c_user=...; xs=...;' (Find this in your browser DevTools -> Application -> Cookies for facebook.com)"
        )

    acc = FBAccount(
        account_name=payload.account_name,
        cookie_data=payload.cookie_data.strip(),
        fb_user_id=fb_uid,
        status="active"
    )
    db.add(acc)
    await db.commit()
    await db.refresh(acc)

    return {
        "id": acc.id,
        "account_name": acc.account_name,
        "fb_user_id": acc.fb_user_id,
        "status": acc.status,
        "message": "Facebook account cookies saved successfully!"
    }


@router.post("/execute-like")
async def execute_like_on_fb(payload: ExecuteRealLikeRequest, db: AsyncSession = Depends(get_db)):
    """Trigger real automated browser like on a real Facebook post."""
    cookie_to_use = payload.cookie_data

    if not cookie_to_use:
        # Pick first active account from DB
        result = await db.execute(select(FBAccount).where(FBAccount.status == "active").limit(1))
        account = result.scalar_one_or_none()
        if not account:
            raise HTTPException(
                status_code=400,
                detail="No Facebook account connected. Please provide 'cookie_data' or add an account first."
            )
        cookie_to_use = account.cookie_data

    result = await execute_real_facebook_like(
        post_url=payload.post_url,
        cookie_str=cookie_to_use,
        headless=payload.headless
    )

    return result
