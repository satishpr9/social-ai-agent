from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import RoleChecker
from app.schemas.proposal import ProposalCreateRequest, ProposalResponse
from app.repositories.lead import LeadRepository
from app.services.proposal import ProposalService

router = APIRouter()

# Instantiate RBAC checkers
require_editor_or_admin = Depends(RoleChecker(["admin", "editor"]))


@router.post(
    "",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[require_editor_or_admin]
)
async def generate_sales_proposal(
    proposal_in: ProposalCreateRequest,
    db: AsyncSession = Depends(get_db)
) -> ProposalResponse:
    """
    Compile a customized PDF sales proposal for a lead, store it in MinIO,
    and return a secure, temporary S3 download link.
    """
    # 1. Fetch Lead details
    lead_repo = LeadRepository(db)
    lead = await lead_repo.get_lead_by_id(proposal_in.lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CRM Lead prospect not found."
        )

    # 2. Map Pydantic items to dictionaries for ReportLab table compiler
    serialized_items = [
        {"name": item.name, "type": item.type, "price": item.price}
        for item in proposal_in.items
    ]

    # 3. Generate PDF and upload to Object Storage
    proposal_service = ProposalService(db)
    try:
        download_url = await proposal_service.create_and_upload_proposal(
            lead=lead,
            items=serialized_items,
            total_price=proposal_in.total_price
        )
        return {"download_url": download_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Proposal compilation failed: {str(e)}"
        )
ActiveUser = "User"
