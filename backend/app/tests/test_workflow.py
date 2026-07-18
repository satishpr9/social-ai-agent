import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.future import select

from app.models.post import SocialPost


@pytest.mark.asyncio
async def test_workflow_generation_endpoint(client, db_session) -> None:
    """
    Integration test: Runs the full content generation pipeline endpoint,
    mocking the LangGraph agent calls to run completely offline.
    """
    # 1. Register and login to get auth credentials
    email = "agent_tester@socialagent.ai"
    password = "secure_password_123"
    
    register_payload = {
        "email": email,
        "password": password,
        "full_name": "Agent Tester"
    }
    register_response = await client.post("/v1/users/register", json=register_payload)
    assert register_response.status_code == 201

    login_data = {
        "username": email,
        "password": password
    }
    login_response = await client.post("/v1/auth/login", data=login_data)
    assert login_response.status_code == 200
    token_data = login_response.json()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 2. Mock the LangGraph agent graph executions
    mock_research_report = "This is a comprehensive research report about FastAPI testing."
    mock_seo_state = {
        "generated_title": "Mastering FastAPI Unit Testing",
        "generated_slug": "mastering-fastapi-unit-testing",
        "generated_blog_content": "Detailed blog content about writing pytest for FastAPI...",
        "seo_keywords": ["fastapi", "testing", "pytest"],
        "meta_description": "Learn how to write unit and integration tests in FastAPI.",
        "image_prompt": "An artistic render of Python testing scripts running."
    }
    mock_social_state = {
        "linkedin_post": "Check out my new article on FastAPI Testing!",
        "twitter_thread": [
            "1/3 Let's discuss testing in FastAPI.",
            "2/3 We cover pytest setup.",
            "3/3 link in bio."
        ],
        "facebook_post": "Facebook draft content.",
        "instagram_caption": "Instagram caption."
    }

    # Execute request with mocked graph states
    with (
        patch("app.services.workflow.research_agent.ainvoke", new_callable=AsyncMock) as mock_res,
        patch("app.services.workflow.seo_agent.ainvoke", new_callable=AsyncMock) as mock_seo,
        patch("app.services.workflow.social_agent.ainvoke", new_callable=AsyncMock) as mock_soc
    ):
        mock_res.return_value = {"summary": mock_research_report}
        mock_seo.return_value = mock_seo_state
        mock_soc.return_value = mock_social_state

        generate_payload = {
            "topic": "FastAPI Testing",
            "platforms": ["linkedin", "twitter"]
        }

        # 3. Post to workflows generate route
        response = await client.post(
            "/v1/workflows/generate",
            json=generate_payload,
            headers=headers
        )

        assert response.status_code == 201
        res_data = response.json()
        assert "post_id" in res_data
        assert res_data["title"] == "Mastering FastAPI Unit Testing"
        assert res_data["status"] == "draft"
        assert "Content successfully generated" in res_data["message"]

        # 4. Verify DB persistence using db_session
        stmt = select(SocialPost).filter(SocialPost.title == "Mastering FastAPI Unit Testing")
        db_result = await db_session.execute(stmt)
        post = db_result.scalars().first()

        assert post is not None
        assert post.title == "Mastering FastAPI Unit Testing"
        assert post.status == "draft"
        assert post.platforms == ["linkedin", "twitter"]
        assert "Detailed blog content" in post.content
        assert "🔍 SEO & Metadata Insights" in post.content
        assert "💼 LinkedIn Draft" in post.content
        assert "🐦 Twitter/X Thread Draft" in post.content
        
        # Verify mock invocations
        mock_res.assert_called_once_with({"query": "FastAPI Testing"})
        mock_seo.assert_called_once_with({"research_report": mock_research_report})
        mock_soc.assert_called_once_with({
            "blog_title": "Mastering FastAPI Unit Testing",
            "blog_content": "Detailed blog content about writing pytest for FastAPI..."
        })

