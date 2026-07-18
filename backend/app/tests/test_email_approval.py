import pytest
import uuid
from app.core.security import create_access_token
from app.models.approval import ApprovalRequest
from app.models.post import SocialPost


@pytest.mark.asyncio
async def test_email_review_rendering_endpoint(client, db_session) -> None:
    """
    Unit test: Verifies that the direct email review GET route renders the
    HTML approval screen correctly and that the page loads the token.
    """
    # 1. Setup mock user and draft post
    email = "editor_reviewer@socialagent.ai"
    password = "secure_password_123"
    
    register_payload = {
        "email": email,
        "password": password,
        "full_name": "Editor Reviewer"
    }
    register_response = await client.post("/v1/users/register", json=register_payload)
    assert register_response.status_code == 201
    user_id = uuid.UUID(register_response.json()["id"])

    # 2. Persist post and approval records
    post = SocialPost(
        user_id=user_id,
        title="Email Review Test Post",
        content="### 💼 LinkedIn Draft\nLinkedIn caption contents here.\n---\n### 🐦 Twitter/X Thread Draft\nTwitter caption.",
        platforms=["linkedin", "twitter"],
        status="pending_approval"
    )
    db_session.add(post)
    await db_session.flush()

    approval = ApprovalRequest(
        post_id=post.id,
        requested_by=user_id,
        status="pending"
    )
    db_session.add(approval)
    await db_session.flush()
    await db_session.commit()

    # 3. Create secure token
    token = create_access_token(subject=str(user_id), role="editor")

    # 4. Trigger review rendering GET route
    response = await client.get(
        f"/v1/approvals/{approval.id}/review-email",
        params={"token": token}
    )

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    
    html_body = response.text
    assert "Campaign Review Gate" in html_body
    assert "Email Review Test Post" in html_body
    assert "LinkedIn Draft" in html_body
    assert "Twitter/X Thread Draft" in html_body
    assert f'const token = "{token}";' in html_body
    assert f'const approvalId = "{approval.id}";' in html_body
