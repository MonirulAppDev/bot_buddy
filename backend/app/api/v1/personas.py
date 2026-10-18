from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.persona import Persona
from app.schemas.persona import PersonaGenerateRequest, PersonaResponse
from app.services.persona_generator import generate_personas_batch

router = APIRouter(prefix="/personas", tags=["Personas"])


@router.get("", response_model=dict)
async def list_personas(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    platform: str | None = None
):
    """List generated dummy personas with pagination."""
    query = select(Persona)
    if platform:
        query = query.where(Persona.platform == platform)
    
    total = await db.scalar(select(func.count(Persona.id)))
    offset = (page - 1) * limit
    result = await db.execute(query.order_by(Persona.created_at.desc()).offset(offset).limit(limit))
    items = result.scalars().all()

    return {
        "items": [PersonaResponse.model_validate(p) for p in items],
        "total": total or 0,
        "page": page,
        "limit": limit
    }


@router.post("/generate", response_model=list[PersonaResponse], status_code=status.HTTP_201_CREATED)
async def generate_personas(
    payload: PersonaGenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate and persist a batch of realistic dummy social personas."""
    personas = generate_personas_batch(
        count=payload.count,
        locale=payload.locale,
        platform=payload.platform
    )
    db.add_all(personas)
    await db.commit()
    return [PersonaResponse.model_validate(p) for p in personas]


@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(persona_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve persona details."""
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return PersonaResponse.model_validate(persona)
