import uuid
from typing import List, Dict, Any
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.lead import LeadRepository
from app.models.lead import Lead
from app.schemas.crm import LeadCreate
from app.services.analytics import AnalyticsService
from app.services.email import EmailService
from app.core.config import settings


class CRMService:
    """
    Business service layer orchestrating lead pipeline captures, profile metadata merges,
    marketing attribution tracking, and transactional owner alerts.
    """
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = LeadRepository(db)

    async def capture_lead(
        self,
        lead_in: LeadCreate,
        background_tasks: BackgroundTasks | None = None
    ) -> Lead:
        """
        Registers a lead. Gracefully handles email duplicates by updating UTM source attributes.
        Triggers analytics logs and admin email alerts.
        """
        email_clean = lead_in.email.strip().lower()
        existing_lead = await self.repo.get_lead_by_email(email_clean)

        if existing_lead:
            # Merge Profile Metadata: fill empty fields if new values are supplied
            if lead_in.full_name and not existing_lead.full_name:
                existing_lead.full_name = lead_in.full_name
            if lead_in.company and not existing_lead.company:
                existing_lead.company = lead_in.company
            
            # Update Attribution: log the latest UTM tags
            existing_lead.utm_source = lead_in.utm_source or existing_lead.utm_source
            existing_lead.utm_medium = lead_in.utm_medium or existing_lead.utm_medium
            existing_lead.utm_campaign = lead_in.utm_campaign or existing_lead.utm_campaign
            
            lead = await self.repo.update_lead(existing_lead)
        else:
            # Create a completely new lead card
            new_lead = Lead(
                email=email_clean,
                full_name=lead_in.full_name,
                company=lead_in.company,
                status="new",
                source_platform=lead_in.source_platform,
                source_post_id=lead_in.source_post_id,
                utm_source=lead_in.utm_source,
                utm_medium=lead_in.utm_medium,
                utm_campaign=lead_in.utm_campaign
            )
            lead = await self.repo.create_lead(new_lead)

        # ----------------------------------------------------
        # Integration 1: Log Conversion Analytics Event (Module 14)
        # ----------------------------------------------------
        analytics_service = AnalyticsService(self.db)
        # Enforce valid platform string mapping default
        platform = lead_in.source_platform or "linkedin"
        if platform not in ["linkedin", "twitter", "facebook", "instagram"]:
            platform = "linkedin"

        try:
            # Capture as conversion link click metric
            await analytics_service.track_event(
                post_id=lead_in.source_post_id,
                metric_type="clicks",
                platform=platform,
                value=1
            )
        except Exception:
            # Fail silently to avoid breaking lead capturing if analytics fails
            pass

        # ----------------------------------------------------
        # Integration 2: Send Admin Alert Notification Email (Module 15)
        # ----------------------------------------------------
        if background_tasks:
            email_service = EmailService()
            subject = f"CRM Alert: New Lead Captured ({lead.email})"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <body>
                <div style="font-family: sans-serif; padding: 20px; color: #1e293b;">
                    <h2 style="color: #4f46e5;">New Prospect Captured!</h2>
                    <p>Our automated social media marketing campaigns have generated a new conversion.</p>
                    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 15px 0;">
                    <p><strong>Email Address:</strong> {lead.email}</p>
                    <p><strong>Full Name:</strong> {lead.full_name or 'N/A'}</p>
                    <p><strong>Company Name:</strong> {lead.company or 'N/A'}</p>
                    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 15px 0;">
                    <h3>Attribution Parameters:</h3>
                    <p><strong>Platform Source:</strong> {lead.source_platform or 'Direct'}</p>
                    <p><strong>UTM Source:</strong> {lead.utm_source or 'N/A'}</p>
                    <p><strong>UTM Campaign:</strong> {lead.utm_campaign or 'N/A'}</p>
                </div>
            </body>
            </html>
            """
            background_tasks.add_task(
                email_service.send_email,
                to_email=settings.EMAILS_FROM_EMAIL,
                subject=subject,
                html_content=html_body
            )

        # Commit transactions atomically
        await self.db.commit()
        return lead

    async def update_lead_status(
        self,
        lead_id: uuid.UUID,
        status: str,
        full_name: str | None = None,
        company: str | None = None
    ) -> Lead:
        """
        Updates pipeline status and details of a lead.
        """
        lead = await self.repo.get_lead_by_id(lead_id)
        if not lead:
            raise ValueError("Lead prospect not found.")

        valid_states = ["new", "contacted", "converted", "lost"]
        status_clean = status.strip().lower()
        if status_clean not in valid_states:
            raise ValueError(f"Invalid status state. Must be one of {valid_states}.")

        lead.status = status_clean
        if full_name is not None:
            lead.full_name = full_name
        if company is not None:
            lead.company = company

        await self.repo.update_lead(lead)
        await self.db.commit()
        return lead

    async def list_all_leads(self) -> List[Lead]:
        """
        Retrieves all leads in the CRM database.
        """
        return await self.repo.get_leads_list()

    async def list_leads_by_status(self, status: str) -> List[Lead]:
        """
        Retrieves leads filtered by conversion state.
        """
        return await self.repo.get_leads_by_status(status.strip().lower())
