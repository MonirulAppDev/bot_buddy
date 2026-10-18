from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.smm_v2 import router as smm_v2_router
from app.api.v1.orders import router as orders_router
from app.api.v1.personas import router as personas_router
from app.api.v1.services import router as services_router
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    await init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Dummy Social Media & Facebook Engagement Simulator API (Followers, Views, Likes, Comments, Reactions)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(services_router, prefix=settings.API_V1_STR)
app.include_router(personas_router, prefix=settings.API_V1_STR)
app.include_router(orders_router, prefix=settings.API_V1_STR)
app.include_router(smm_v2_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs",
        "smm_api_v2_url": "/api/v2"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}
