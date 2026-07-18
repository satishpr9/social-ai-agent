import os
import re
from typing import TypedDict, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END


class SEOState(TypedDict):
    """
    State definition for the LangGraph SEO Content Agent.
    """
    research_report: str
    generated_title: str
    generated_slug: str
    generated_blog_content: str
    seo_keywords: List[str]
    meta_description: str
    image_prompt: str


# ----------------------------------------------------
# Helper Functions
# ----------------------------------------------------

def slugify(text: str) -> str:
    """
    Converts a string into a URL-friendly slug.
    Example: "Next.js 15 & FastAPI: The Best Stack!" -> "nextjs-15-fastapi-the-best-stack"
    """
    # Convert to lowercase and strip whitespace
    slug = text.lower().strip()
    # Remove special characters like & or commas
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    # Replace spaces and multiple hyphens with a single hyphen
    slug = re.sub(r'[\s-]+', '-', slug)
    # Trim leading/trailing hyphens
    return slug.strip('-')


# ----------------------------------------------------
# Node Implementations
# ----------------------------------------------------

async def generate_blog_node(state: SEOState) -> dict:
    """
    Generates a detailed, professional markdown blog post from the research report.
    Falls back to a structured markdown template if no LLM API key is present.
    """
    report = state.get("research_report", "")
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    # 1. Attempt LLM Generation
    if gemini_key and report:
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=gemini_key, temperature=0.7)
            prompt = ChatPromptTemplate.from_template(
                "You are an expert technical blogger and copywriter.\n"
                "Write an engaging, authoritative, and SEO-friendly blog post in Markdown format "
                "based on the following research briefing. Integrate the sources naturally.\n\n"
                "Research Brief:\n{report}"
            )
            chain = prompt | llm
            response = await chain.ainvoke({"report": report})
            return {"generated_blog_content": response.content}
        except Exception:
            pass

    # 2. Local Formatting Fallback
    blog = f"""# The Future of Automation: Integrating Modern Workflows

In today's fast-paced digital economy, organizations must automate marketing and indexing operations to remain competitive. Below we examine key insights gathered from recent industry research.

## Analysis of Recent Trends

The research indicates rapid transitions in marketing technology setups. Specifically:

{report}

## Strategic Takeaways

1. **Automation ROI**: Leveraging multi-agent workflows dramatically decreases content creation cycles.
2. **Quality Gateways**: Retaining human-in-the-loop approvals prevents automated drift and maintains editorial high standards.
3. **Pluggable Architecture**: Designing software modules with clean boundaries (FastAPI backend and Next.js interfaces) ensures long-term system scalability.

---
*Published by the Autonomous Content Creator.*
"""
    return {"generated_blog_content": blog}


async def generate_title_slug_node(state: SEOState) -> dict:
    """
    Generates a catchy blog title and constructs a URL-safe slug.
    """
    blog_content = state.get("generated_blog_content", "")
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    title = "Leveraging LangGraph and FastAPI for Automated Social Marketing"

    # 1. Attempt LLM Title Generation
    if gemini_key and blog_content:
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=gemini_key, temperature=0.8)
            prompt = ChatPromptTemplate.from_template(
                "Read the following blog post and suggest a single, catchy, SEO-friendly headline/title.\n"
                "Respond with only the title string and nothing else.\n\n"
                "Blog Post:\n{blog}"
            )
            chain = prompt | llm
            response = await chain.ainvoke({"blog": blog_content[:2000]})
            title = response.content.strip().replace('"', '')
        except Exception:
            pass

    # Generate slug using our regex helper
    slug = slugify(title)
    return {
        "generated_title": title,
        "generated_slug": slug
    }


async def generate_seo_metadata_node(state: SEOState) -> dict:
    """
    Generates SEO keywords, a meta description (under 160 characters),
    and a descriptive image generation prompt.
    """
    blog_content = state.get("generated_blog_content", "")
    title = state.get("generated_title", "")
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    # Default fallbacks
    keywords = ["automation", "fastapi", "nextjs", "saas", "ai marketing"]
    meta_description = f"Read about {title}. Discover how multi-agent orchestrations are redefining SEO content automation pipelines."
    image_prompt = "A high-tech digital workspace with abstract glowing network connections linking modern code interfaces. Hyper-detailed, 3D render, dark mode aesthetic."

    # 1. Attempt LLM Metadata Generation
    if gemini_key and blog_content:
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=gemini_key, temperature=0.5)
            prompt = ChatPromptTemplate.from_template(
                "Based on the following blog title and content, generate SEO metadata:\n"
                "Title: {title}\n\n"
                "Provide your response in the exact format:\n"
                "KEYWORDS: comma-separated list of 5 keywords\n"
                "DESCRIPTION: one-sentence meta description (under 160 characters)\n"
                "IMAGE: descriptive DALL-E prompt for a high-quality blog banner image\n\n"
                "Blog Content:\n{blog}"
            )
            chain = prompt | llm
            response = await chain.ainvoke({"title": title, "blog": blog_content[:2000]})
            
            # Parse responses
            content = response.content
            keywords_match = re.search(r"KEYWORDS:\s*(.*)", content, re.IGNORECASE)
            desc_match = re.search(r"DESCRIPTION:\s*(.*)", content, re.IGNORECASE)
            image_match = re.search(r"IMAGE:\s*(.*)", content, re.IGNORECASE)
            
            if keywords_match:
                keywords = [k.strip() for k in keywords_match.group(1).split(",")]
            if desc_match:
                meta_description = desc_match.group(1).strip()
            if image_match:
                image_prompt = image_match.group(1).strip()
                
        except Exception:
            pass

    return {
        "seo_keywords": keywords,
        "meta_description": meta_description[:160], # Hard constraint
        "image_prompt": image_prompt
    }


# ----------------------------------------------------
# State Graph Construction
# ----------------------------------------------------

workflow = StateGraph(SEOState)

# Add nodes
workflow.add_node("generate_blog", generate_blog_node)
workflow.add_node("generate_title_slug", generate_title_slug_node)
workflow.add_node("generate_seo_metadata", generate_seo_metadata_node)

# Set execution flow edges
workflow.set_entry_point("generate_blog")
workflow.add_edge("generate_blog", "generate_title_slug")
workflow.add_edge("generate_title_slug", "generate_seo_metadata")
workflow.add_edge("generate_seo_metadata", END)

# Compile the graph
seo_agent = workflow.compile()
