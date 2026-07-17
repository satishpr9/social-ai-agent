import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.router import api_router
from app.core.config import settings
from app.services.n8n import publish_scheduled_posts_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Launch the background scheduler task
    scheduler_task = asyncio.create_task(publish_scheduled_posts_loop())
    yield
    # Shutdown: Cancel the scheduler task to ensure clean termination
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.include_router(api_router)


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

