import os
from apify_client import ApifyClient
from dotenv import load_dotenv
from typing import List

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

load_dotenv()

class CommentFilterResult(BaseModel):
    kept_indices: List[int] = Field(description="Strict list of indices (0-based) for comments that are highly relevant, valuable, or objective.")

def filter_comments_with_ai(comments: List[dict]) -> List[dict]:
    """Filters a list of comments using gpt-5-mini."""
    if not comments:
        return []
        
    comments_text = ""
    for idx, c in enumerate(comments):
        text = str(c.get('text', '')).replace('\n', ' ').strip()
        if text:
            comments_text += f"[{idx}] {text}\n"
            
    if not comments_text.strip():
        return []
        
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
    try:
        structured_llm = llm.with_structured_output(CommentFilterResult)
    except Exception:
        structured_llm = llm

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a strictly professional data cleaning AI for automotive research.
        You will receive a numbered list of Facebook comments.
        
        KEEP comments that:
        - Discuss car features, software, technical issues, or driving experiences.
        - Contain objective praise or criticism of the car.
        - Mention pricing, dealer service, or purchase decisions.
        
        DISCARD (do not include the index) comments that:
        - Are spam, advertising SIM cards, real estate, or irrelevant products.
        - Are personal attacks, political arguments, extreme vulgarity, or meaningless replies (e.g. "Chẩm", ".", "Up", "Hóng").
        
        Output ONLY the indices of the comments to KEEP."""),
        ("user", "Here are the comments:\n\n{comments_text}")
    ])
    
    chain = prompt | structured_llm
    
    try:
        res = chain.invoke({"comments_text": comments_text})
        if hasattr(res, 'kept_indices'):
            indices = res.kept_indices
        elif isinstance(res, dict) and 'kept_indices' in res:
            indices = res['kept_indices']
        else:
            indices = list(range(len(comments))) # fallback
            
        # Reconstruct the list based on kept indices
        filtered_comments = [comments[i] for i in indices if 0 <= i < len(comments)]
        return filtered_comments
    except Exception as e:
        print(f"WARNING: AI Comment Filter failed: {e}. Keeping original comments.")
        return comments

# --- CORE TOOL ---
def crawl_content_tool(posts: List[dict]):
    """
    Receives a list of posts with URLs and fetches detailed content/comments using Apify.
    Automatically runs AI Comment Cleaner to discard spam/junk comments.
    """
    client = ApifyClient(os.getenv("APIFY_TOKEN"))
    
    # Extract URLs for detailed scraping
    urls = [post['url'] for post in posts if post.get('url')]
    if not urls:
        return posts

    print(f"INFO: Fetching detailed content for {len(urls)} posts...")
    
    run_input = {
        "startUrls": [{"url": url} for url in urls],
        "includeComments": True,
        "viewOption": "CHRONOLOGICAL",
        "commentsMode": "RANKED_THREADED",
        "maxComments": 100  # Cost Optimization: Only scrape top 100 comments max per post
    }
    
    try:
        # Use facebook-posts-scraper to fetch individual post details
        run = client.actor("apify/facebook-posts-scraper").call(run_input=run_input)
        detailed_items = {item['url']: item for item in client.dataset(run["defaultDatasetId"]).iterate_items()}
        
        # Merge detailed data into the existing posts list
        for post in posts:
            detail = detailed_items.get(post['url'])
            if detail:
                post['full_text'] = detail.get('text', post['text'])
                raw_comments = detail.get('comments', [])
                
                # --- APPLY AI COMMENT CLEANER ---
                if raw_comments:
                    print(f"INFO: Cleaning {len(raw_comments)} comments for post {post.get('url', 'Unknown')}...")
                    clean_comments = filter_comments_with_ai(raw_comments)
                    post['comments'] = clean_comments
                    print(f"INFO: Retained {len(clean_comments)} valuable comments.")
                else:
                    post['comments'] = []
                    
                post['likes'] = detail.get('likesCount', 0)
        
        return posts
    except Exception as e:
        print(f"ERROR: Failed to crawl detailed content: {e}")
        return posts
