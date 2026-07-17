import os
import logging
from typing import Any
from langchain_community.tools import DuckDuckGoSearchRun

logger = logging.getLogger("app.agents.tools.search")


async def search_web(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """
    Search the web for news.
    Attempts Tavily if API key is present, falls back to DuckDuckGo,
    and defaults to deterministic mock results if offline.
    """
    # 1. Attempt Tavily
    tavily_key = os.environ.get("TAVILY_API_KEY")
    if tavily_key:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=tavily_key)
            # Fetch search results
            response = client.search(q=query, max_results=max_results, topic="news")
            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", "No Title"),
                    "url": item.get("url", "No URL"),
                    "snippet": item.get("content", ""),
                    "source": "tavily"
                })
            if results:
                logger.info(f"Tavily search returned {len(results)} items.")
                return results
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}. Falling back to DuckDuckGo.")

    # 2. Attempt DuckDuckGo
    try:
        ddg = DuckDuckGoSearchRun()
        ddg_result = ddg.run(query)
        # DuckDuckGo tool returns a plain string, we split it or wrap it
        if ddg_result:
            logger.info("DuckDuckGo search completed successfully.")
            return [{
                "title": f"Web Search Result: {query}",
                "url": "https://duckduckgo.com",
                "snippet": ddg_result,
                "source": "duckduckgo"
            }]
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed: {e}. Falling back to Mock data.")

    # 3. Mock Fallback
    logger.info("Using mock research data fallback.")
    return [
        {
            "title": f"Breaking: Artificial Intelligence in Social Media Marketing for {query}",
            "url": "https://example.com/ai-marketing-trends",
            "snippet": f"A comprehensive study showing how AI agents are transforming {query} by automating SEO optimization, blog writing, and publishing schedules.",
            "source": "mock_news_1"
        },
        {
            "title": f"How SaaS Companies are leveraging {query} in 2026",
            "url": "https://example.com/saas-automation",
            "snippet": f"Industry leaders describe how combining n8n visual workflows and LangGraph multi-agent configurations increases marketing ROI for campaigns about {query}.",
            "source": "mock_news_2"
        },
        {
            "title": f"The rise of Autonomous Content Creation in {query}",
            "url": "https://example.com/content-automation",
            "snippet": f"A detailed analysis of auto-publishing tools and SEO agents, demonstrating that human-in-the-loop workflows outperform purely autonomous setups for {query}.",
            "source": "mock_news_3"
        }
    ]
