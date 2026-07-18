import asyncio
import logging
import smtplib
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Any
import httpx

from app.core.config import settings

logger = logging.getLogger("app.services.email")


class EmailService:
    """
    Transactional email service implementing pluggable Resend API/SMTP pathways,
    HTML templating, and asynchronous background worker threads.
    """
    async def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Sends an email. Uses Resend REST API if key is present,
        otherwise falls back to standard SMTP in a worker thread.
        """
        # If in testing mode and credentials are mock/empty, bypass network IO
        if settings.ENVIRONMENT == "testing" or (not settings.RESEND_API_KEY and not settings.SMTP_PASSWORD):
            logger.info(f"Bypassing active email dispatch in test/local mode for: {to_email}")
            return True

        # 1. Attempt Resend REST API Client
        if settings.RESEND_API_KEY:
            logger.info(f"Dispatching email to {to_email} via Resend REST API.")
            payload = {
                "from": f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>",
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }
            headers = {
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json"
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        "https://api.resend.com/emails",
                        json=payload,
                        headers=headers
                    )
                    if response.status_code in [200, 201, 202]:
                        logger.info("Email successfully sent via Resend API.")
                        return True
                    else:
                        logger.error(f"Resend API error: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"Failed to connect to Resend API: {e}. Attempting SMTP fallback.")

        # 2. SMTP Thread-Safe Fallback
        logger.info(f"Dispatching email to {to_email} via standard SMTP.")
        
        def _send_smtp_sync():
            msg = MIMEMultipart()
            msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                if settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAILS_FROM_EMAIL, to_email, msg.as_string())

        try:
            # Shift blocking smtplib operations to a threadpool to keep event loop free
            await asyncio.to_thread(_send_smtp_sync)
            logger.info("Email successfully sent via SMTP.")
            return True
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")
            return False

    async def send_approval_email(
        self,
        to_email: str,
        approval_id: uuid.UUID,
        post_title: str,
        submitter_name: str,
        platforms: List[str],
        token: str
    ) -> bool:
        """
        Formats and sends an HTML approval notification email to editors/admins.
        """
        review_url = f"{settings.BACKEND_URL}/api/v1/approvals/{approval_id}/review-email?token={token}"
        platforms_str = ", ".join([p.capitalize() for p in platforms])
        subject = f"Review Required: '{post_title}'"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; background-color: #f8fafc; color: #1e293b; padding: 20px; }}
                .container {{ max-width: 600px; background-color: #ffffff; padding: 30px; border-radius: 12px; border: 1px border #e2e8f0; }}
                .btn {{ display: inline-block; padding: 12px 24px; background-color: #4f46e5; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 15px; }}
                .footer {{ font-size: 11px; color: #64748b; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Content Approval Pending</h2>
                <p>Hello,</p>
                <p>An AI marketing campaign has generated new social content requiring your editorial review before publishing.</p>
                <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;">
                <p><strong>Post Title:</strong> {post_title}</p>
                <p><strong>Target Platforms:</strong> {platforms_str}</p>
                <p><strong>Created By:</strong> {submitter_name}</p>
                <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;">
                <p>Please click the button below to view the post, make adjustments, and approve or reject it from the dashboard:</p>
                <a href="{review_url}" class="btn">Review Content</a>
                <p class="footer">This is an automated notification from the Social Media Marketing AI Agent.</p>
            </div>
        </body>
        </html>
        """
        return await self.send_email(to_email=to_email, subject=subject, html_content=html_content)

    async def send_performance_report(
        self,
        to_email: str,
        user_name: str,
        views: int,
        likes: int,
        clicks: int,
        platform_data: List[Dict[str, Any]]
    ) -> bool:
        """
        Formats and sends a weekly campaign performance report HTML email.
        """
        subject = "Weekly Campaign Performance Report"
        
        # Build platform breakdown rows
        rows_html = ""
        for p in platform_data:
            rows_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-transform: capitalize;"><strong>{p['platform']}</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;">{p['views']:,}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;">{p['likes']:,}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;">{p['clicks']:,}</td>
            </tr>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; background-color: #f8fafc; color: #1e293b; padding: 20px; }}
                .container {{ max-width: 600px; background-color: #ffffff; padding: 30px; border-radius: 12px; border: 1px solid #e2e8f0; }}
                .stat-grid {{ display: grid; grid-template-cols: repeat(3, 1fr); gap: 15px; margin: 25px 0; }}
                .stat-card {{ background-color: #f1f5f9; padding: 15px; border-radius: 8px; text-align: center; }}
                .stat-val {{ font-size: 20px; font-weight: bold; color: #4f46e5; }}
                .footer {{ font-size: 11px; color: #64748b; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Campaign Performance Report</h2>
                <p>Hello {user_name},</p>
                <p>Here is your weekly summary of performance metrics aggregated across all active campaigns.</p>
                
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="stat-val">{views:,}</div>
                        <div style="font-size: 11px; color: #64748b;">Views</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-val">{likes:,}</div>
                        <div style="font-size: 11px; color: #64748b;">Likes</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-val">{clicks:,}</div>
                        <div style="font-size: 11px; color: #64748b;">Link Clicks</div>
                    </div>
                </div>

                <h3>Platform Breakdown</h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 10px;">
                    <thead>
                        <tr style="background-color: #f8fafc; text-align: left;">
                            <th style="padding: 8px; border-bottom: 2px solid #e2e8f0;">Platform</th>
                            <th style="padding: 8px; border-bottom: 2px solid #e2e8f0; text-align: right;">Views</th>
                            <th style="padding: 8px; border-bottom: 2px solid #e2e8f0; text-align: right;">Likes</th>
                            <th style="padding: 8px; border-bottom: 2px solid #e2e8f0; text-align: right;">Clicks</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>

                <p class="footer">This report was compiled autonomously by the Social Media Marketing AI Agent SaaS.</p>
            </div>
        </body>
        </html>
        """
        return await self.send_email(to_email=to_email, subject=subject, html_content=html_content)
