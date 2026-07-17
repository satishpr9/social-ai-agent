import os
from typing import TypedDict, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from app.agents.tools.search import search_web


class ResearchState(TypedDict):
    """
    State definition for the LangGraph research agent.
    """
    query: str
    raw_results: List[dict]
    deduplicated_results: List[dict]
    ranked_results: List[dict]
    summary: str


# ----------------------------------------------------
# Node Implementations
# ----------------------------------------------------

async def search_node(state: ResearchState) -> dict:
    """
    Searches the web for news related to the query topic.
    """
    query = state.get("query", "")
    results = await search_web(query=query)
    return {"raw_results": results}


async def deduplicate_node(state: ResearchState) -> dict:
    """
    Filters out duplicate results based on URL match or title similarity.
    """
    raw_results = state.get("raw_results", [])
    seen_urls = set()
    seen_titles = set()
    deduped = []

    for item in raw_results:
        url = item.get("url", "").lower().strip()
        title = item.get("title", "").lower().strip()
        
        # Deduplicate based on exact URL or exact title matches
        if url and url in seen_urls:
            continue
        if title and title in seen_titles:
            continue
            
        seen_urls.add(url)
        seen_titles.add(title)
        deduped.append(item)

    return {"deduplicated_results": deduped}


async def rank_node(state: ResearchState) -> dict:
    """
    Ranks deduplicated news items by relevance to the query.
    Falls back to keyword scoring if no LLM API key is present.
    """
    deduped = state.get("deduplicated_results", [])
    query = state.get("query", "").lower()
    openai_key = os.environ.get("OPENAI_API_KEY")

    # 1. Attempt LLM ranking if API Key is present
    if openai_key:
        try:
            # We initialize a light, fast model for ranking
            llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_key, temperature=0)
            
            prompt = ChatPromptTemplate.from_template(
                "You are an AI research ranker. Rate the relevance of each article snippet to the query: '{query}'.\n"
                "Return a score from 1 to 10 for each snippet (10 is highly relevant, 1 is irrelevant).\n"
                "Respond with only the list of integers separated by commas in the exact order supplied.\n\n"
                "Snippets:\n{snippets}"
            )
            
            snippets_str = "\n".join([
                f"{i}. Title: {item['title']}\nSnippet: {item['snippet']}" 
                for i, item in enumerate(deduped)
            ])
            
            chain = prompt | llm
            response = await chain.ainvoke({"query": query, "snippets": snippets_str})
            
            # Parse scores (e.g. "8, 9, 3")
            scores = [int(s.strip()) for s in response.content.split(",") if s.strip().isdigit()]
            
            # Pair and sort
            scored_items = []
            for idx, item in enumerate(deduped):
                score = scores[idx] if idx < len(scores) else 5 # default to 5 if parsing mismatch
                scored_items.append((score, item))
                
            scored_items.sort(key=lambda x: x[0], reverse=True)
            ranked = [item for _, item in scored_items]
            return {"ranked_results": ranked}
            
        except Exception:
            # Fall back to heuristic ranking on error
            pass

    # 2. Local Heuristic Ranking Fallback
    scored_items = []
    query_words = set(query.split())
    for item in deduped:
        score = 0
        title = item.get("title", "").lower()
        snippet = item.get("snippet", "").lower()
        
        # Award points for keyword matching
        for word in query_words:
            if word in title:
                score += 5
            if word in snippet:
                score += 2
                
        # Small reward for longer snippet (contains more information)
        score += min(len(snippet) // 50, 3)
        scored_items.append((score, item))

    # Sort descending by score
    scored_items.sort(key=lambda x: x[0], reverse=True)
    ranked = [item for _, item in scored_items]
    return {"ranked_results": ranked}


async def summarize_node(state: ResearchState) -> dict:
    """
    Compiles the ranked research items into a unified Markdown summary report.
    Falls back to a structured template format if no LLM API key is present.
    """
    ranked = state.get("ranked_results", [])
    query = state.get("query", "")
    openai_key = os.environ.get("OPENAI_API_KEY")

    # 1. Attempt LLM Summarization
    if openai_key and ranked:
        try:
            llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_key, temperature=0.3)
            prompt = ChatPromptTemplate.from_template(
                "You are an expert market analyst writing a briefing report.\n"
                "Compile a professional Markdown summary of the following research articles regarding '{query}'.\n"
                "Focus on extracting trends, key statistics, and actionable insights.\n"
                "Cite the sources by their URLs.\n\n"
                "Research Articles:\n{articles}"
            )
            
            articles_str = "\n\n".join([
                f"Title: {item['title']}\nSource: {item['url']}\nContent: {item['snippet']}" 
                for item in ranked
            ])
            
            chain = prompt | llm
            response = await chain.ainvoke({"query": query, "articles": articles_str})
            return {"summary": response.content}
        except Exception:
            pass

    # 2. Local Formatting Fallback
    markdown = f"# AI Research Report: {query}\n\n"
    markdown += "This report compiles current news items and highlights key insights.\n\n"
    markdown += "## Key Findings\n\n"
    
    for i, item in enumerate(ranked[:3]): # Top 3 items
        markdown += f"### {i+1}. {item['title']}\n"
        markdown += f"- **Source**: [{item['source']}]({item['url']})\n"
        markdown += f"- **Summary**: {item['snippet']}\n\n"
        
    markdown += "\n---\n*Report compiled autonomously via local research agent.*"
    return {"summary": markdown}


# ----------------------------------------------------
# State Graph Construction
# ----------------------------------------------------

workflow = StateGraph(ResearchState)

# Add nodes
workflow.add_node("search", search_node)
workflow.add_node("deduplicate", deduplicate_node)
workflow.add_node("rank", rank_node)
workflow.add_node("summarize", summarize_node)

# Set execution flow edges
workflow.set_entry_point("search")
workflow.add_edge("search", "deduplicate")
workflow.add_edge("deduplicate", "rank")
workflow.add_edge("rank", "summarize")
workflow.add_edge("summarize", END)

# Compile the graph
research_agent = workflow.compile()
