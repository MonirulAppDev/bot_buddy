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


class BulkImportFBAccountsRequest(BaseModel):
    raw_data: str = Field(..., description="Multi-line cookie strings or name|cookies")


class BatchLikeRequest(BaseModel):
    post_url: str = Field(..., example="https://www.facebook.com/photo?fbid=122103658497500888&set=a.122095228263500888")
    quantity: int = Field(default=5, ge=1, le=50, example=10)
    exclude_fb_user_id: str | None = Field(default=None, description="Exclude user's own profile so you don't like with yourself")
    delay_seconds: float = Field(default=2.5, ge=1.0, le=30.0)
    headless: bool = Field(default=True)


@router.post("/bulk-import", status_code=status.HTTP_201_CREATED)
async def bulk_import_fb_accounts(payload: BulkImportFBAccountsRequest, db: AsyncSession = Depends(get_db)):
    """Import multiple fake/dummy Facebook account cookies at once."""
    lines = [line.strip() for line in payload.raw_data.strip().splitlines() if line.strip()]
    imported = []

    for idx, line in enumerate(lines, 1):
        account_name = f"Fake Account #{idx}"
        cookie_str = line

        if "|" in line:
            parts = line.split("|", 1)
            account_name = parts[0].strip()
            cookie_str = parts[1].strip()

        match = re.search(r"c_user=(\d+)", cookie_str)
        fb_uid = match.group(1) if match else None

        if fb_uid or "c_user" in cookie_str:
            acc = FBAccount(
                account_name=account_name,
                cookie_data=cookie_str,
                fb_user_id=fb_uid,
                status="active"
            )
            db.add(acc)
            imported.append(account_name)

    await db.commit()
    return {
        "success": True,
        "total_imported": len(imported),
        "accounts": imported,
        "message": f"Successfully imported {len(imported)} fake Facebook accounts!"
    }


@router.post("/batch-like")
async def execute_batch_like_on_fb(payload: BatchLikeRequest, db: AsyncSession = Depends(get_db)):
    """Execute likes on post sequentially using only fake accounts (excludes user's own profile)."""
    from app.services.facebook_bot import execute_batch_facebook_likes

    query = select(FBAccount).where(FBAccount.status == "active")
    if payload.exclude_fb_user_id:
        query = query.where(FBAccount.fb_user_id != payload.exclude_fb_user_id)

    result = await db.execute(query.order_by(FBAccount.total_likes_given.asc()))
    accounts = result.scalars().all()

    if not accounts:
        raise HTTPException(
            status_code=400,
            detail="No fake accounts available in account pool. Please import or add fake Facebook accounts first."
        )

    accounts_payload = [
        {
            "id": acc.id,
            "account_name": acc.account_name,
            "cookie_data": acc.cookie_data,
            "fb_user_id": acc.fb_user_id
        }
        for acc in accounts
    ]

    batch_res = await execute_batch_facebook_likes(
        post_url=payload.post_url,
        account_list=accounts_payload,
        quantity=min(payload.quantity, len(accounts)),
        delay_seconds=payload.delay_seconds,
        headless=payload.headless
    )

    # Update database totals
    for log in batch_res["logs"]:
        if log["status"] == "SUCCESS" and log.get("account_id"):
            acc = await db.get(FBAccount, log["account_id"])
            if acc:
                acc.total_likes_given += 1
    await db.commit()

    return batch_res


@router.post("/auto-create-bot")
async def auto_create_fb_bot(headless: bool = False, db: AsyncSession = Depends(get_db)):
    """Attempt automated Facebook registration bot using Playwright."""
    from app.services.fb_account_creator import attempt_fb_registration

    res = await attempt_fb_registration(headless=headless)
    if res.get("success") and res.get("c_user"):
        # Save newly created account into pool
        acc = FBAccount(
            account_name=res.get("account_name", "Auto-Created Bot"),
            cookie_data=f"c_user={res['c_user']};",
            fb_user_id=res["c_user"],
            status="active"
        )
        db.add(acc)
        await db.commit()

    return res

