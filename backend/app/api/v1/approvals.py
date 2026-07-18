import uuid
from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.post import (
    SocialPostCreate,
    ApprovalActionRequest,
    ApprovalRequestResponse
)
from app.services.approval import ApprovalService
from app.services.email import EmailService
from app.core.security import create_access_token

router = APIRouter()

# Instantiate RBAC checkers
require_editor_or_admin = Depends(RoleChecker(["admin", "editor"]))


@router.post(
    "/submit",
    response_model=ApprovalRequestResponse,
    status_code=status.HTTP_201_CREATED
)
async def submit_post(
    post_in: SocialPostCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ApprovalRequestResponse:
    """
    Submit a newly generated blog post for editor/admin review.
    Creates both the post and the linked approval request.
    Dispatches a review notification email in the background.
    """
    approval_service = ApprovalService(db)
    approval = await approval_service.submit_post_for_approval(
        post_in=post_in,
        user_id=current_user.id
    )

    # Generate a secure access token for direct email validation (valid for 3 days)
    access_token = create_access_token(
        subject=str(current_user.id),
        role=current_user.role,
        expires_delta=timedelta(days=3)
    )

    # Dispatch email notification in the background
    email_service = EmailService()
    background_tasks.add_task(
        email_service.send_approval_email,
        to_email=settings.EMAILS_FROM_EMAIL,
        approval_id=approval.id,
        post_title=post_in.title,
        submitter_name=current_user.email,
        platforms=post_in.platforms,
        token=access_token
    )

    return approval


@router.get(
    "/pending",
    response_model=List[ApprovalRequestResponse],
    dependencies=[require_editor_or_admin]
)
async def list_pending_approvals(
    db: AsyncSession = Depends(get_db)
) -> List[ApprovalRequestResponse]:
    """
    List all pending content approval requests. Restricted to Admin/Editor.
    """
    approval_service = ApprovalService(db)
    pending = await approval_service.get_pending_requests()
    return pending


@router.post(
    "/{approval_id}/approve",
    response_model=ApprovalRequestResponse
)
async def approve_post(
    approval_id: uuid.UUID,
    action_in: ApprovalActionRequest,
    current_user: User = Depends(RoleChecker(["admin", "editor"])),
    db: AsyncSession = Depends(get_db)
) -> ApprovalRequestResponse:
    """
    Approve content for publishing. Restricted to Admin/Editor.
    """
    approval_service = ApprovalService(db)
    try:
        updated_request = await approval_service.approve_request(
            approval_id=approval_id,
            reviewer_id=current_user.id,
            comments=action_in.comments
        )
        return updated_request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{approval_id}/reject",
    response_model=ApprovalRequestResponse
)
async def reject_post(
    approval_id: uuid.UUID,
    action_in: ApprovalActionRequest,
    current_user: User = Depends(RoleChecker(["admin", "editor"])),
    db: AsyncSession = Depends(get_db)
) -> ApprovalRequestResponse:
    """
    Reject content, reverting it to draft state. Requires feedback comments. Restricted to Admin/Editor.
    """
    approval_service = ApprovalService(db)
    try:
        updated_request = await approval_service.reject_request(
            approval_id=approval_id,
            reviewer_id=current_user.id,
            comments=action_in.comments
        )
        return updated_request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{approval_id}/review-email",
    response_class=HTMLResponse
)
async def review_post_email(
    approval_id: uuid.UUID,
    token: str,
    db: AsyncSession = Depends(get_db)
) -> HTMLResponse:
    """
    GET endpoint rendering a beautiful Kinetic Brutalism micro-frontend approval screen.
    Uses query token authentication to validate action requests.
    """
    approval_service = ApprovalService(db)
    approval = await approval_service.repo.get_approval_by_id(approval_id)
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found."
        )

    # 1. Handle already processed requests
    if approval.status != "pending":
        status_color = "#2563EB" if approval.status == "approved" else "#DC2626"
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Campaign Review Gate</title>
            <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
            <style>
                body {{
                    background: #FFF1F2;
                    color: #881337;
                    font-family: 'Space Grotesk', sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    margin: 0;
                }}
                .card {{
                    background: #FFFFFF;
                    border: 3px solid #881337;
                    box-shadow: 8px 8px 0px #881337;
                    padding: 40px;
                    max-width: 480px;
                    text-align: center;
                }}
                h1 {{ font-size: 28px; margin-bottom: 20px; text-transform: uppercase; }}
                p {{ font-size: 16px; line-height: 1.5; }}
                .status-badge {{
                    display: inline-block;
                    background: {status_color};
                    color: #FFFFFF;
                    padding: 8px 16px;
                    font-weight: bold;
                    text-transform: uppercase;
                    border: 2px solid #881337;
                    margin-top: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Review Gate Alert</h1>
                <p>This campaign review request has already been processed.</p>
                <div class="status-badge">Status: {approval.status}</div>
            </div>
        </body>
        </html>
        """)

    # 2. Render review page
    platforms_badges = "".join([
        f'<span class="badge">{p.upper()}</span>' for p in approval.post.platforms
    ])

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Campaign Approval: {approval.post.title}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
        <!-- Markdown Parser CDN -->
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <style>
            :root {{
                --color-primary: #E11D48;
                --color-on-primary: #FFFFFF;
                --color-secondary: #FB7185;
                --color-accent: #2563EB;
                --color-background: #FFF1F2;
                --color-foreground: #881337;
                --color-border: #881337;
            }}
            body {{
                background-color: var(--color-background);
                color: var(--color-foreground);
                font-family: 'DM Sans', sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
            }}
            .wrapper {{
                max-width: 800px;
                width: 100%;
                margin-top: 20px;
            }}
            /* Kinetic Brutalist Header */
            header {{
                background-color: var(--color-primary);
                color: var(--color-on-primary);
                border: 3px solid var(--color-border);
                box-shadow: 6px 6px 0px var(--color-border);
                padding: 20px;
                margin-bottom: 30px;
                text-transform: uppercase;
            }}
            header h1 {{
                font-family: 'Space Grotesk', sans-serif;
                margin: 0;
                font-size: 26px;
                font-weight: 700;
            }}
            header p {{
                margin: 5px 0 0 0;
                font-size: 14px;
                font-weight: 500;
                letter-spacing: 1px;
            }}
            /* Dashboard Card */
            .card {{
                background-color: #FFFFFF;
                border: 3px solid var(--color-border);
                box-shadow: 8px 8px 0px var(--color-border);
                padding: 30px;
                margin-bottom: 30px;
            }}
            h2 {{
                font-family: 'Space Grotesk', sans-serif;
                margin-top: 0;
                font-size: 22px;
                text-transform: uppercase;
                border-bottom: 2px solid var(--color-border);
                padding-bottom: 10px;
            }}
            .meta-info {{
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                margin-bottom: 20px;
                font-size: 14px;
            }}
            .meta-info div {{
                background-color: #FFFFFF;
                border: 2px solid var(--color-border);
                padding: 6px 12px;
                font-weight: 500;
            }}
            .badge {{
                display: inline-block;
                background-color: var(--color-accent);
                color: #FFFFFF;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: bold;
                border: 1px solid var(--color-border);
                margin-right: 5px;
            }}
            /* Content Preview Box */
            .preview-box {{
                background-color: #FAFAFA;
                border: 2px solid var(--color-border);
                padding: 20px;
                max-height: 500px;
                overflow-y: auto;
                font-size: 15px;
                line-height: 1.6;
            }}
            /* Kinetic Action Buttons */
            .actions {{
                display: flex;
                flex-direction: column;
                gap: 20px;
                margin-top: 35px;
            }}
            .btn-row {{
                display: flex;
                gap: 15px;
            }}
            button {{
                font-family: 'Space Grotesk', sans-serif;
                font-weight: 700;
                font-size: 16px;
                text-transform: uppercase;
                padding: 15px 30px;
                border: 3px solid var(--color-border);
                cursor: pointer;
                transition: all 150ms ease;
            }}
            .btn-approve {{
                background-color: #10B981;
                color: #FFFFFF;
                box-shadow: 4px 4px 0px var(--color-border);
                flex: 1;
            }}
            .btn-approve:hover {{
                box-shadow: 1px 1px 0px var(--color-border);
                transform: translate(3px, 3px);
            }}
            .btn-reject {{
                background-color: var(--color-primary);
                color: #FFFFFF;
                box-shadow: 4px 4px 0px var(--color-border);
                width: 180px;
            }}
            .btn-reject:hover {{
                box-shadow: 1px 1px 0px var(--color-border);
                transform: translate(3px, 3px);
            }}
            textarea {{
                width: 100%;
                box-sizing: border-box;
                border: 2px solid var(--color-border);
                padding: 12px;
                font-family: 'DM Sans', sans-serif;
                font-size: 14px;
                resize: vertical;
                margin-top: 5px;
            }}
            /* Notification Modals */
            .toast {{
                display: none;
                background-color: #FFFFFF;
                border: 3px solid var(--color-border);
                box-shadow: 6px 6px 0px var(--color-border);
                padding: 20px;
                text-align: center;
                margin-top: 20px;
                font-weight: bold;
                text-transform: uppercase;
            }}
        </style>
    </head>
    <body>
        <div class="wrapper">
            <header>
                <h1>Campaign Review Gate</h1>
                <p>AUTOPILOT CONTENT HUMAN-IN-THE-LOOP INTERFACE</p>
            </header>

            <div class="card">
                <h2>Campaign Post Details</h2>
                <div class="meta-info">
                    <div><strong>Title:</strong> {approval.post.title}</div>
                    <div><strong>Target Platforms:</strong> {platforms_badges}</div>
                </div>

                <h2>Generated Deliverables (Markdown Preview)</h2>
                <div class="preview-box" id="markdown-preview"></div>
            </div>

            <div class="card">
                <h2>Review Actions</h2>
                <div class="actions">
                    <div class="btn-row">
                        <button class="btn-approve" onclick="submitReview('approve')">Approve & Publish</button>
                    </div>
                    
                    <hr style="border: 0; border-top: 2px solid var(--color-border); margin: 15px 0;">
                    
                    <div>
                        <label style="font-weight: bold; text-transform: uppercase;">Rejection Comments (Required for rejection):</label>
                        <textarea id="rejection-feedback" rows="3" placeholder="Provide feedback detailing edits or reasons for rejection..."></textarea>
                        <button class="btn-reject" style="margin-top: 10px;" onclick="submitReview('reject')">Reject Draft</button>
                    </div>
                </div>
                
                <div class="toast" id="toast-message"></div>
            </div>
        </div>

        <script>
            // Parse Markdown report to HTML using marked.js
            const rawMarkdown = `{approval.post.content}`;
            document.getElementById('markdown-preview').innerHTML = marked.parse(rawMarkdown);

            const token = "{token}";
            const approvalId = "{approval_id}";

            async function submitReview(action) {{
                const toast = document.getElementById('toast-message');
                const feedbackText = document.getElementById('rejection-feedback').value;

                if (action === 'reject' && !feedbackText.trim()) {{
                    toast.style.display = 'block';
                    toast.style.borderColor = 'var(--color-primary)';
                    toast.style.color = 'var(--color-primary)';
                    toast.innerText = 'Error: Feedback comments are required for rejection!';
                    return;
                }}

                toast.style.display = 'block';
                toast.style.borderColor = 'var(--color-border)';
                toast.style.color = 'var(--color-foreground)';
                toast.innerText = 'Submitting decision to autopilot...';

                try {{
                    const response = await fetch(`/api/v1/approvals/${{approvalId}}/${{action}}`, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer ' + token
                        }},
                        body: JSON.stringify({{ comments: feedbackText || 'Approved via email gateway.' }})
                    }});

                    if (response.ok) {{
                        toast.style.borderColor = '#10B981';
                        toast.style.color = '#10B981';
                        toast.innerText = action === 'approve' 
                            ? 'Success: Campaign post approved! Dispatched to n8n publisher.'
                            : 'Success: Campaign rejected. Post reverted to draft.';
                        
                        // Disable buttons to prevent double click
                        document.querySelectorAll('button').forEach(btn => btn.disabled = true);
                    }} else {{
                        const err = await response.json();
                        toast.style.borderColor = 'var(--color-primary)';
                        toast.style.color = 'var(--color-primary)';
                        toast.innerText = 'Failure: ' + (err.detail || 'Failed to submit review.');
                    }}
                }} catch (e) {{
                    toast.style.borderColor = 'var(--color-primary)';
                    toast.style.color = 'var(--color-primary)';
                    toast.innerText = 'Connection Error: ' + e;
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
