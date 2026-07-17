import pytest
from unittest.mock import patch, MagicMock

from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_public_capture_lead_endpoint(client) -> None:
    """
    Integration test: Submits a new lead form via the public capture endpoint.
    Mocks out email and analytics to prevent network connections.
    """
    payload = {
        "email": "lead_prospect@corp.com",
        "full_name": "Satish CRM Test",
        "company": "FastAPI Inc",
        "source_platform": "linkedin",
        "utm_source": "linkedin_ad",
        "utm_medium": "banner",
        "utm_campaign": "brand_awareness"
    }

    # Patch outbound integrations to prevent actual network calls during tests
    with patch("app.services.crm.AnalyticsService.track_event") as mock_track, \
         patch("app.services.email.EmailService.send_email") as mock_send_email:
        
        mock_track.return_value = None
        mock_send_email.return_value = True

        response = await client.post("/v1/crm/leads", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "lead_prospect@corp.com"
        assert data["status"] == "new"
        assert data["utm_source"] == "linkedin_ad"
        assert "id" in data


@pytest.mark.asyncio
async def test_duplicate_lead_capture_merging(client) -> None:
    """
    Integration test: Submits duplicate email leads, verifying profile merging
    rather than duplicate creations.
    """
    # 1. First capture
    lead1 = {
        "email": "merge_test@corp.com",
        "full_name": None,
        "company": "Initial Company",
        "utm_source": "google"
    }
    
    with patch("app.services.crm.AnalyticsService.track_event"), \
         patch("app.services.email.EmailService.send_email"):
        res1 = await client.post("/v1/crm/leads", json=lead1)
        assert res1.status_code == 201

        # 2. Second capture (duplicate email)
        lead2 = {
            "email": "merge_test@corp.com",
            "full_name": "Merged Name",
            "company": "Updated Company", # (preserved since old wasn't blank)
            "utm_source": "newsletter"
        }
        res2 = await client.post("/v1/crm/leads", json=lead2)
        assert res2.status_code == 201
        
        data = res2.json()
        assert data["email"] == "merge_test@corp.com"
        assert data["full_name"] == "Merged Name" # Filled the blank field
        assert data["utm_source"] == "newsletter" # Updated with latest source


@pytest.mark.asyncio
async def test_crm_leads_rbac_gating(client, db_session) -> None:
    """
    Integration test: Verifies that only admin/editor roles can view CRM leads list.
    """
    # Create mock users directly in the database
    from app.models.user import User
    from app.core.security import get_password_hash
    import uuid

    admin_id = uuid.uuid4()
    client_id = uuid.uuid4()

    admin_user = User(
        id=admin_id,
        email="admin_editor@agent.com",
        hashed_password=get_password_hash("password"),
        role="admin",
        is_active=True
    )
    client_user = User(
        id=client_id,
        email="client_prospect@agent.com",
        hashed_password=get_password_hash("password"),
        role="client",
        is_active=True
    )
    db_session.add(admin_user)
    db_session.add(client_user)
    await db_session.flush()

    # 1. Request without token (anonymous)
    anon_response = await client.get("/v1/crm/leads")
    assert anon_response.status_code == 401

    # 2. Request with Client Role (unauthorized)
    client_token = create_access_token(subject=client_id, role="client")
    client_headers = {"Authorization": f"Bearer {client_token}"}
    client_response = await client.get("/v1/crm/leads", headers=client_headers)
    assert client_response.status_code == 403 # Gated by RBAC checker!

    # 3. Request with Admin Role (authorized)
    admin_token = create_access_token(subject=admin_id, role="admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    admin_response = await client.get("/v1/crm/leads", headers=admin_headers)
    assert admin_response.status_code == 200
    assert isinstance(admin_response.json(), list)
