import os
import re
from typing import TypedDict, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END


class SocialState(TypedDict):
    """
    State definition for the LangGraph Social Media Agent.
    """
    blog_title: str
    blog_content: str
    linkedin_post: str
    twitter_thread: List[str]
    facebook_post: str
    instagram_caption: str


# ----------------------------------------------------
# Custom Thread Splitting Helper (For X/Twitter)
# ----------------------------------------------------

def split_text_into_tweets(text: str, max_chars: int = 240) -> List[str]:
    """
    Helper algorithm that splits raw text into a list of sentences,
    then aggregates them into individual tweets under 280 characters.
    """
    # Clean up markdown styling
    clean_text = re.sub(r'#+\s*', '', text) # Remove headers formatting
    clean_text = re.sub(r'\*+', '', clean_text) # Remove bold/italic stars
    
    # Split into sentences or paragraphs
    sentences = re.split(r'(?<=[.!?])\s+', clean_text.strip())
    
    tweets = []
    current_tweet = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # If a single sentence exceeds the limit, truncate it
        if len(sentence) > max_chars:
            sentence = sentence[:max_chars - 3] + "..."
            
        # Check if adding this sentence exceeds our tweet chunk limit
        if len(current_tweet) + len(sentence) + 1 > max_chars:
            tweets.append(current_tweet.strip())
            current_tweet = sentence
        else:
            if current_tweet:
                current_tweet += " " + sentence
            else:
                current_tweet = sentence
                
    if current_tweet:
        tweets.append(current_tweet.strip())
        
    # Append thread indices (e.g. "1/4")
    total_tweets = len(tweets)
    indexed_tweets = []
    for idx, tweet in enumerate(tweets):
        indexed_tweets.append(f"{tweet} ({idx + 1}/{total_tweets})")
        
    return indexed_tweets


# ----------------------------------------------------
# Node Implementations (Parallel)
# ----------------------------------------------------

async def start_node(state: SocialState) -> dict:
    """
    Entrypoint coordinator node. Merely passes inputs down
    to parallel channels.
    """
    return {}


async def generate_linkedin_node(state: SocialState) -> dict:
    """
    Transforms the blog content into a professional LinkedIn update.
    """
    title = state.get("blog_title", "")
    content = state.get("blog_content", "")
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if gemini_key:
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=gemini_key, temperature=0.7)
            prompt = ChatPromptTemplate.from_template(
                "Write a professional LinkedIn post summarizing the key insights of this blog post:\n"
                "Title: {title}\n"
                "Content:\n{content}\n\n"
                "Use spacing, clean bullet points, a call to action, and 3 professional hashtags. "
                "Keep the tone encouraging, technical, and authoritative."
            )
            chain = prompt | llm
            response = await chain.ainvoke({"title": title, "content": content[:2000]})
            return {"linkedin_post": response.content}
        except Exception:
            pass

    # Local Fallback
    post = f"🚀 New Article Published: {title}\n\n"
    post += "SaaS automation is transitioning rapidly! In our latest article, we analyze the integration of clean architectures, multi-agent frameworks, and transaction scaling.\n\n"
    post += "Key Takeaways:\n"
    post += "• Build robust settings using Pydantic validation\n"
    post += "• Orchestrate multi-step systems with LangGraph\n"
    post += "• Retain human-in-the-loop validation for maximum ROI\n\n"
    post += "Read the full breakdown here! 👇\n"
    post += "#SaaS #SoftwareArchitecture #AIEngineering #LangGraph"
    return {"linkedin_post": post}


async def generate_twitter_node(state: SocialState) -> dict:
    """
    Transforms the blog content into an X (Twitter) thread.
    Each tweet is strictly validated to be under 280 characters.
    """
    title = state.get("blog_title", "")
    content = state.get("blog_content", "")
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if gemini_key:
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=gemini_key, temperature=0.6)
            prompt = ChatPromptTemplate.from_template(
                "Read this blog post: '{title}'. Write a Twitter/X thread summarizing it.\n"
                "Format your output as individual tweets separated by '---' on new lines.\n"
                "Do not include any headers like 'Tweet 1:'. Just output the raw tweet text.\n"
                "Each tweet must be strictly under 240 characters (leaving space for numberings).\n"
                "Include relevant emojis and hashtags.\n\n"
                "Content:\n{content}"
            )
            chain = prompt | llm
            response = await chain.ainvoke({"title": title, "content": content[:2000]})
            
            # Parse and index
            raw_tweets = [t.strip() for t in response.content.split("---") if t.strip()]
            total = len(raw_tweets)
            formatted_thread = []
            for idx, tweet in enumerate(raw_tweets):
                # Ensure safety limit
                tweet_text = tweet
                if len(tweet_text) > 250:
                    tweet_text = tweet_text[:247] + "..."
                formatted_thread.append(f"{tweet_text} ({idx + 1}/{total})")
            return {"twitter_thread": formatted_thread}
        except Exception:
            pass

    # Heuristic Fallback
    summary_sentence = f"We just published our guide on: {title}. Here is a thread breaking down the core concepts:"
    thread_body = split_text_into_tweets(content[:1500])
    # Prepend intro tweet
    thread = [f"📢 {summary_sentence} (1/{len(thread_body) + 1})"]
    for idx, tweet in enumerate(thread_body):
        # Adjust indices
        clean_tweet = tweet.rsplit(" (", 1)[0]
        thread.append(f"• {clean_tweet} ({idx + 2}/{len(thread_body) + 1})")
        
    return {"twitter_thread": thread}


async def generate_facebook_node(state: SocialState) -> dict:
    """
    Transforms the blog content into an engaging Facebook update.
    """
    title = state.get("blog_title", "")
    content = state.get("blog_content", "")
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if gemini_key:
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=gemini_key, temperature=0.8)
            prompt = ChatPromptTemplate.from_template(
                "Write an engaging, conversational Facebook post for this article:\n"
                "Title: {title}\n"
                "Content:\n{content}\n\n"
                "Use friendly language, relevant emojis, space out paragraphs, and include a clear call-to-action link."
            )
            chain = prompt | llm
            response = await chain.ainvoke({"title": title, "content": content[:2000]})
            return {"facebook_post": response.content}
        except Exception:
            pass

    # Local Fallback
    post = f"💡 Want to build production-ready AI SaaS products? 🚀\n\n"
    post += f"Our latest article, '{title}', walks through setting up type-safe configurations, multi-service docker containers, and robust database layers!\n\n"
    post += "Whether you are a senior architect or a developer expanding your toolkit, these core design patterns are key to scaling business APIs.\n\n"
    post += "Check out the full article and let us know your thoughts in the comments! 🔗 [Link in bio]\n\n"
    post += "#AISaaS #FastAPI #NextJS #IndieHacker #MarketingAutomation"
    return {"facebook_post": post}


async def generate_instagram_node(state: SocialState) -> dict:
    """
    Transforms the blog content into an Instagram caption.
    """
    title = state.get("blog_title", "")
    content = state.get("blog_content", "")
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if gemini_key:
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=gemini_key, temperature=0.7)
            prompt = ChatPromptTemplate.from_template(
                "Create a compelling Instagram caption for a post about this article:\n"
                "Title: {title}\n"
                "Content:\n{content}\n\n"
                "Start with a strong hook, use spacing, add relevant emojis, and end with a block of 10 relevant hashtags."
            )
            chain = prompt | llm
            response = await chain.ainvoke({"title": title, "content": content[:2000]})
            return {"instagram_caption": response.content}
        except Exception:
            pass

    # Local Fallback
    caption = f"🔥 Building a Multi-Agent AI SaaS! 🔥\n\n"
    caption += "How do you coordinate multiple AI agents in production without creating spaghetti code? 💻\n\n"
    caption += "We describe how using LangGraph state charts keeps agents modular, testable, and robust. By defining states, nodes, and edges, you gain full control over LLM execution.\n\n"
    caption += "👉 Swipe left to see the system architecture!\n"
    caption += "🔗 Click the link in our bio to read the full guide.\n\n"
    caption += ".\n.\n.\n"
    caption += "#tech #artificialintelligence #saas #developer #python #fastapi #langgraph #automation #marketingtools #webdev"
    return {"instagram_caption": caption}


# ----------------------------------------------------
# State Graph Construction (Parallel Execution)
# ----------------------------------------------------

workflow = StateGraph(SocialState)

# Add nodes
workflow.add_node("start", start_node)
workflow.add_node("linkedin", generate_linkedin_node)
workflow.add_node("twitter", generate_twitter_node)
workflow.add_node("facebook", generate_facebook_node)
workflow.add_node("instagram", generate_instagram_node)

# Set execution flow - branching in parallel from start_node
workflow.set_entry_point("start")
workflow.add_edge("start", "linkedin")
workflow.add_edge("start", "twitter")
workflow.add_edge("start", "facebook")
workflow.add_edge("start", "instagram")

# Rejoin all channels at the END node
workflow.add_edge("linkedin", END)
workflow.add_edge("twitter", END)
workflow.add_edge("facebook", END)
workflow.add_edge("instagram", END)

# Compile the graph
social_agent = workflow.compile()
