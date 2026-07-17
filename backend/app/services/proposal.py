from io import BytesIO
from datetime import datetime, timezone
import uuid
from typing import List, Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.services.storage import StorageService
from app.models.lead import Lead


class ProposalService:
    """
    Sales Proposal Generation engine drawing ReportLab PDF layout streams
    and committing binaries to S3 Object Storage channels.
    """
    def __init__(self, db_session: Any) -> None:
        self.db = db_session
        self.storage = StorageService()

    def generate_proposal_pdf(
        self,
        lead_email: str,
        lead_name: str | None,
        company: str | None,
        items: List[Dict[str, str]],
        total_price: str
    ) -> bytes:
        """
        Compiles a professional sales proposal PDF document in-memory
        utilizing ReportLab flowables.
        """
        buffer = BytesIO()
        
        # 1. Initialize Document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )
        
        styles = getSampleStyleSheet()
        
        # 2. Design Custom Premium Styles
        title_style = ParagraphStyle(
            name="TitleStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#4f46e5"), # Premium Indigo
            alignment=1, # Center
            spaceAfter=15
        )
        
        subtitle_style = ParagraphStyle(
            name="SubtitleStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#64748b"), # Slate Grey
            alignment=1,
            spaceAfter=30
        )

        h2_style = ParagraphStyle(
            name="H2Style",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#1e293b"), # Charcoal Black
            spaceBefore=15,
            spaceAfter=10
        )

        body_style = ParagraphStyle(
            name="BodyStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155") # Dark Slate
        )

        th_style = ParagraphStyle(
            name="THStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=colors.HexColor("#ffffff") # White text for table headers
        )

        story = []

        # 3. Write Document Header
        story.append(Paragraph("Social AI Agent Marketing Proposal", title_style))
        story.append(Paragraph("Custom Autopilot Campaign Strategy & Automation Quote", subtitle_style))
        story.append(Spacer(1, 15))

        # 4. Write Client Details Card
        client_name = lead_name or "Valued Client"
        client_company = company or "N/A"
        date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
        
        client_details = f"""
        <b>Prepared For:</b> {client_name}<br/>
        <b>Company:</b> {client_company}<br/>
        <b>Email Address:</b> {lead_email}<br/>
        <b>Date Generated:</b> {date_str}<br/>
        <b>Proposal Validity:</b> 30 Days from issue
        """
        story.append(Paragraph("Proposal Details", h2_style))
        story.append(Paragraph(client_details, body_style))
        story.append(Spacer(1, 20))

        # 5. Write Scope Section
        story.append(Paragraph("Campaign Autopilot Scope", h2_style))
        scope_text = """
        • <b>AI Research Crawler Agent:</b> Autonomously crawls web articles and researches topics.<br/>
        • <b>SEO Blog Writing Agent:</b> Drafts search-optimized content articles under 160-char descriptions.<br/>
        • <b>Multi-Channel Formatting:</b> Tailors formatted copy for LinkedIn, X (Twitter), Facebook, and Instagram.<br/>
        • <b>Human-in-the-Loop Gateway:</b> Gated approvals interface with full scheduling hooks.<br/>
        • <b>Unified Analytics:</b> Real-time views, likes, and link click timeseries performance tracking.
        """
        story.append(Paragraph(scope_text, body_style))
        story.append(Spacer(1, 20))

        # 6. Build Pricing Quote Grid
        story.append(Paragraph("Investment Quote", h2_style))
        
        # Build Table Data
        table_data = [[
            Paragraph("Service / Package Item", th_style), 
            Paragraph("Type", th_style), 
            Paragraph("Subtotal", th_style)
        ]]
        
        for item in items:
            table_data.append([
                Paragraph(item.get("name", ""), body_style),
                Paragraph(item.get("type", "One-Time"), body_style),
                Paragraph(item.get("price", "$0"), body_style)
            ])
            
        # Append Total Row
        table_data.append([
            Paragraph("<b>Total Estimated Quote</b>", body_style),
            Paragraph("", body_style),
            Paragraph(f"<b>{total_price}</b>", body_style)
        ])

        # Style reportlab Table
        col_widths = [260, 120, 120]
        quote_table = Table(table_data, colWidths=col_widths)
        quote_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4f46e5")), # Header background
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.HexColor("#f8fafc"), colors.HexColor("#ffffff")]), # Alternating rows
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")), # Light borders
            ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor("#4f46e5")), # Bold line above total row
            ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
            ('TOPPADDING', (0, -1), (-1, -1), 10),
        ]))
        
        story.append(quote_table)
        story.append(Spacer(1, 25))

        # 7. Write Terms / Next Steps
        story.append(Paragraph("Next Steps", h2_style))
        next_steps = """
        To accept this proposal and boot your campaign autopilot agents, click the sign-up link inside our client onboarding portal. If you have questions regarding the campaign configurations or pricing adjustments, contact your dedicated account director.
        """
        story.append(Paragraph(next_steps, body_style))

        # 8. Compile PDF Document
        doc.build(story)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    async def create_and_upload_proposal(
        self,
        lead: Lead,
        items: List[Dict[str, str]],
        total_price: str
    ) -> str:
        """
        Generates the proposal PDF, uploads it to MinIO, and returns the pre-signed download URL.
        """
        # Generate PDF Bytes
        pdf_bytes = self.generate_proposal_pdf(
            lead_email=lead.email,
            lead_name=lead.full_name,
            company=lead.company,
            items=items,
            total_price=total_price
        )

        # Unique name for proposal file
        filename = f"proposal_{lead.id}_{uuid.uuid4().hex[:8]}.pdf"

        # Initialize storage bucket and upload
        await self.storage.init_bucket()
        await self.storage.upload_file(file_data=pdf_bytes, file_name=filename)

        # Get pre-signed S3 download URL
        download_url = await self.storage.get_presigned_url(file_name=filename)
        return download_url
