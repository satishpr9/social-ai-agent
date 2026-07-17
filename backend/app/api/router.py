from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.n8n import router as n8n_router

api_router = APIRouter()

# Register endpoint groups
api_router.include_router(
    health_router,
    prefix="/v1",
    tags=["Health"]
)

api_router.include_router(
    auth_router,
    prefix="/v1/auth",
    tags=["Authentication"]
)

api_router.include_router(
    users_router,
    prefix="/v1/users",
    tags=["Users"]
)

api_router.include_router(
    approvals_router,
    prefix="/v1/approvals",
    tags=["Approvals"]
)

api_router.include_router(
    n8n_router,
    prefix="/v1/n8n",
    tags=["n8n Integration"]
)