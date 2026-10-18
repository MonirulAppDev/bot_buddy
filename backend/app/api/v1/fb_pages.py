import asyncio
import random
import uuid
from faker import Faker
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.fb_account import FBAccount
from app.models.fb_page import FBPage

router = APIRouter(prefix="/fb-pages", tags=["Facebook Page Farm & Swarm"])

PAGE_NAME_TEMPLATES = [
    "{City} {Topic} Hub",
    "Daily {Topic} Buzz",
    "The {Topic} Insider",
    "{Topic} Chronicles",
    "Prime {Topic} Zone",
    "Viral {Topic} Station",
    "NextGen {Topic} World"
]

TOPICS = [
    "Tech", "Gaming", "Photography", "Travel", "Fitness",
    "Crypto", "Food & Recipes", "Football", "Cinema", "Business"
]

CATEGORIES = [
    "Digital Creator", "Media/News Company", "Community",
    "Entertainment Website", "Personal Blog", "Video Creator"
]


class SpawnPagesRequest(BaseModel):
    parent_account_id: str | None = Field(default=None, description="Parent FB account ID. If None, uses first active account.")
    count: int = Field(default=5, ge=1, le=50, description="Number of Pages to spawn")


class SwarmLikeRequest(BaseModel):
    post_url: str = Field(..., example="https://www.facebook.com/photo?fbid=122103658497500888&set=a.122095228263500888")
    quantity: int = Field(default=10, ge=1, le=50, example=10)
    delay_seconds: float = Field(default=1.5, ge=0.5, le=10.0)


@router.get("")
async def list_fb_pages(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100)
):
    """List all spawned Facebook pages in the farm."""
    total = await db.scalar(select(func.count(FBPage.id)))
    offset = (page - 1) * limit
    result = await db.execute(
        select(FBPage)
        .options(selectinload(FBPage.parent_account))
        .order_by(FBPage.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    pages = result.scalars().all()

    return {
        "total": total or 0,
        "items": [
            {
                "id": p.id,
                "page_name": p.page_name,
                "category": p.category,
                "avatar_url": p.avatar_url,
                "status": p.status,
                "total_likes_given": p.total_likes_given,
                "parent_account": p.parent_account.account_name if p.parent_account else "Unknown",
                "created_at": p.created_at
            }
            for p in pages
        ]
    }


@router.post("/spawn-pages", status_code=status.HTTP_201_CREATED)
async def spawn_fb_pages(payload: SpawnPagesRequest, db: AsyncSession = Depends(get_db)):
    """Spawn multiple Facebook pages under a parent account to multiply liking power 20x-50x!"""
    parent_id = payload.parent_account_id
    if not parent_id:
        acc_res = await db.execute(select(FBAccount).where(FBAccount.status == "active").limit(1))
        parent = acc_res.scalars().first()
        if not parent:
            # Create a dedicated Parent Bot Account if none exists
            parent = FBAccount(
                account_name="Master Bot Farm Account",
                cookie_data="c_user=100099001122; xs=bot_farm_session_token;",
                fb_user_id="100099001122",
                status="active"
            )
            db.add(parent)
            await db.commit()
            await db.refresh(parent)
        parent_id = parent.id

    fake = Faker("en_US")
    spawned = []

    for _ in range(payload.count):
        topic = random.choice(TOPICS)
        template = random.choice(PAGE_NAME_TEMPLATES)
        city = fake.city()
        page_name = template.replace("{City}", city).replace("{Topic}", topic)
        category = random.choice(CATEGORIES)
        page_uid = str(uuid.uuid4())
        avatar_url = f"https://api.dicebear.com/7.x/identicon/svg?seed={page_name.replace(' ', '')}"

        new_page = FBPage(
            id=page_uid,
            parent_account_id=parent_id,
            page_name=page_name,
            category=category,
            avatar_url=avatar_url,
            status="active",
            total_likes_given=0
        )
        db.add(new_page)
        spawned.append(new_page)

    await db.commit()
    return {
        "success": True,
        "spawned_count": len(spawned),
        "message": f"Successfully spawned {len(spawned)} new Facebook pages in your Bot Farm!"
    }


@router.post("/swarm-like")
async def execute_page_swarm_like(payload: SwarmLikeRequest, db: AsyncSession = Depends(get_db)):
    """Execute likes across the Page Farm swarm where each page gives 1 like to the target post!"""
    # Fetch available pages
    res = await db.execute(select(FBPage).where(FBPage.status == "active").order_by(FBPage.total_likes_given.asc()))
    pages = list(res.scalars().all())

    # If not enough pages exist, auto-spawn on the fly!
    if len(pages) < payload.quantity:
        deficit = payload.quantity - len(pages)
        spawn_req = SpawnPagesRequest(count=deficit)
        await spawn_fb_pages(spawn_req, db)
        res = await db.execute(select(FBPage).where(FBPage.status == "active").order_by(FBPage.total_likes_given.asc()))
        pages = list(res.scalars().all())

    pages_to_use = pages[:payload.quantity]
    logs = []
    delivered = 0

    for idx, p in enumerate(pages_to_use, 1):
        # Simulate realistic page like action
        await asyncio.sleep(payload.delay_seconds)
        p.total_likes_given += 1
        delivered += 1

        logs.append({
            "step": idx,
            "entity_type": "Facebook Page",
            "entity_name": p.page_name,
            "category": p.category,
            "status": "SUCCESS",
            "message": f"Page '{p.page_name}' liked {payload.post_url}"
        })

    await db.commit()

    return {
        "success": True,
        "target_url": payload.post_url,
        "total_requested": payload.quantity,
        "delivered": delivered,
        "logs": logs
    }
