import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.lead import Lead


class LeadRepository:
    """
    Repository class encapsulating database operations for Leads.
    """
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_lead_by_id(self, lead_id: uuid.UUID) -> Lead | None:
        """
        Retrieves a lead by UUID.
        """
        stmt = select(Lead).filter(Lead.id == lead_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_lead_by_email(self, email: str) -> Lead | None:
        """
        Retrieves a lead by unique email.
        """
        stmt = select(Lead).filter(Lead.email == email.strip().lower())
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_lead(self, lead: Lead) -> Lead:
        """
        Persists a new lead.
        """
        self.db.add(lead)
        await self.db.flush()
        return lead

    async def update_lead(self, lead: Lead) -> Lead:
        """
        Updates an existing lead's fields.
        """
        self.db.add(lead)
        await self.db.flush()
        return lead

    async def get_leads_list(self) -> List[Lead]:
        """
        Retrieves all leads chronologically.
        """
        stmt = select(Lead).order_by(Lead.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_leads_by_status(self, status: str) -> List[Lead]:
        """
        Retrieves leads filtered by conversion pipeline status.
        """
        stmt = select(Lead).filter(Lead.status == status).order_by(Lead.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
