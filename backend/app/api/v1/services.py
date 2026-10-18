from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceResponse, ServiceUpdate

router = APIRouter(prefix="/services", tags=["Services"])

DEFAULT_SERVICES = [
    {
        "name": "Facebook Post Likes [Instant / Drip-Feed]",
        "platform": "facebook",
        "service_type": "like",
        "rate_per_1000": 1.20,
        "min_quantity": 10,
        "max_quantity": 20000,
        "description": "Standard Facebook post likes from high-quality realistic dummy profiles."
    },
    {
        "name": "Facebook Post Love Reactions ❤️ [Authentic Pacing]",
        "platform": "facebook",
        "service_type": "love_react",
        "rate_per_1000": 1.50,
        "min_quantity": 10,
        "max_quantity": 15000,
        "description": "Heart / Love reactions with Gaussian human-like delays."
    },
    {
        "name": "Facebook Video & Reel Views [High Retention]",
        "platform": "facebook",
        "service_type": "view",
        "rate_per_1000": 0.80,
        "min_quantity": 100,
        "max_quantity": 100000,
        "description": "Synthetic watch time and video view simulation."
    },
    {
        "name": "Facebook Page & Profile Followers",
        "platform": "facebook",
        "service_type": "follower",
        "rate_per_1000": 2.50,
        "min_quantity": 25,
        "max_quantity": 50000,
        "description": "Natural drip-feed profile followers with localized dummy profiles."
    },
    {
        "name": "Facebook Smart Custom Comments [Spintax Supported]",
        "platform": "facebook",
        "service_type": "comment",
        "rate_per_1000": 4.00,
        "min_quantity": 5,
        "max_quantity": 5000,
        "description": "Contextual comments parsed via Spintax or custom templates."
    }
]


@router.get("", response_model=list[ServiceResponse])
async def list_services(db: AsyncSession = Depends(get_db)):
    """List all available engagement services. Auto-seeds defaults if empty."""
    result = await db.execute(select(Service).order_by(Service.id.asc()))
    services = list(result.scalars().all())

    if not services:
        for item in DEFAULT_SERVICES:
            srv = Service(**item)
            db.add(srv)
        await db.commit()
        result = await db.execute(select(Service).order_by(Service.id.asc()))
        services = list(result.scalars().all())

    return services


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(payload: ServiceCreate, db: AsyncSession = Depends(get_db)):
    """Add a new custom service."""
    service = Service(**payload.model_dump())
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: int, db: AsyncSession = Depends(get_db)):
    """Get single service details."""
    service = await db.get(Service, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service
