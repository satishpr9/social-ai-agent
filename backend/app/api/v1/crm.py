import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.crm import LeadCreate, LeadUpdate, LeadResponse
from app.services.crm import CRMService

router = APIRouter()

# Instantiate RBAC checkers for dashboard operations
require_editor_or_admin = Depends(RoleChecker(["admin", "editor"]))


@router.post(
    "/leads",
    response_model=LeadResponse,
    status_code=status.HTTP_201_CREATED
)
async def public_capture_lead(
    lead_in: LeadCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> LeadResponse:
    """
    Public conversion endpoint to capture new prospects from landing pages
    or social CTA links. Registers conversions and owner email alerts.
    """
    crm_service = CRMService(db)
    lead = await crm_service.capture_lead(
        lead_in=lead_in,
        background_tasks=background_tasks
    )
    return lead


@router.get(
    "/leads",
    response_model=List[LeadResponse],
    dependencies=[require_editor_or_admin]
)
async def list_crm_leads(
    status: str | None = None,
    db: AsyncSession = Depends(get_db)
) -> List[LeadResponse]:
    """
    List captured leads. Filterable by pipeline status. Restricted to Admin/Editor.
    """
    crm_service = CRMService(db)
    if status:
        return await crm_service.list_leads_by_status(status)
    return await crm_service.list_all_leads()


@router.put(
    "/leads/{lead_id}",
    response_model=LeadResponse
)
async def update_lead_details(
    lead_id: uuid.UUID,
    lead_in: LeadUpdate,
    current_user: User = Depends(RoleChecker(["admin", "editor"])),
    db: AsyncSession = Depends(get_db)
) -> LeadResponse:
    """
    Update lead contact metadata or transition pipeline state. Restricted to Admin/Editor.
    """
    crm_service = CRMService(db)
    try:
        updated_lead = await crm_service.update_lead_status(
            lead_id=lead_id,
            status=lead_in.status or "new",
            full_name=lead_in.full_name,
            company=lead_in.company
        )
        return updated_lead
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
ActiveUser = "User"
