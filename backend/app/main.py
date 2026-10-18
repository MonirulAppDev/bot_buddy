import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.smm_v2 import router as smm_v2_router
from app.api.v1.auth import router as auth_router
from app.api.v1.fb_accounts import router as fb_accounts_router
from app.api.v1.fb_pages import router as fb_pages_router
from app.api.v1.orders import router as orders_router
from app.api.v1.personas import router as personas_router
from app.api.v1.services import router as services_router
from app.api.v1.view_booster import router as view_booster_router
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

# Mount Static Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(services_router, prefix=settings.API_V1_STR)
app.include_router(personas_router, prefix=settings.API_V1_STR)
app.include_router(orders_router, prefix=settings.API_V1_STR)
app.include_router(fb_accounts_router, prefix=settings.API_V1_STR)
app.include_router(fb_pages_router, prefix=settings.API_V1_STR)
app.include_router(view_booster_router, prefix=settings.API_V1_STR)
app.include_router(smm_v2_router)


@app.get("/", tags=["Dashboard"], include_in_schema=False)
async def root():
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", tags=["Dashboard"], include_in_schema=False)
async def dashboard_page():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Dashboard index.html not found"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

