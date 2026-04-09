from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List
import os
import json

class FilterResult(BaseModel):
    is_relevant: bool = Field(description="True ONLY if the post is a hands-on review, user evaluation, or driving experience of a VinFast EV. False for everything else including questions.")
    reason: str = Field(description="A concise explanation for the relevance decision.")
    category: str = Field(description="Classification: Review, or Irrelevant.")

def filter_posts_tool(posts: List[dict]):
    """
    Uses gpt-5-mini to filter and categorize posts based on relevance to VinFast Electric Vehicles.
    Includes parallel processing and incremental checkpointing.
    """
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
    
    try:
        structured_llm = llm.with_structured_output(FilterResult)
    except Exception:
        structured_llm = llm 
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert data analyst specializing in VinFast Electric Vehicles (EVs). 
        Your task is to filter and categorize Facebook posts.
        
        STRICTLY KEEP ONLY:
        - Detailed reviews, evaluations, user experiences, and test drives of VinFast EVs (CARS: VF3, VF5, VF6, VF7, VF8, VF9, Vfe34 AND MOTORBIKES: Klara, Feliz, Evo, Vento, etc.).
        - Posts where the author shares their actual experience using or driving the vehicle.
        
        AGGRESSIVELY DISCARD:
        - Buying demand, purchase questions, pricing inquiries ("Nên mua xe nào", "Xin giá", "Tư vấn mua").
        - Technical support questions, asking for help with bugs/errors ("Xe bị lỗi màn hình", "Cứu hộ bật không lên").
        - Buy, sell, trade, or transfer posts ("cần bán", "sang tên", "chính chủ", "nhận cọc", "sale", "Pass").
        - News, politics, current events, or general non-user-generated newspaper links.
        - General programming, coding, music, art, spam, or real estate.
        """),
        ("user", "Analyze the following post content:\n\nContent: {content}")
    ])
    
    chain = prompt | structured_llm
    
    relevant_posts = []
    irrelevant_count = 0
    checkpoint_path = "data/processed/filter_checkpoint.jsonl"
    os.makedirs("data/processed", exist_ok=True)
    
    print(f"INFO: Filtering {len(posts)} posts using gpt-5-mini (Parallel Mode + Checkpointing)...")
    
    from concurrent.futures import ThreadPoolExecutor
    
    def process_single_post(post):
        try:
            res = chain.invoke({"content": post.get('text', '')})
            if res.is_relevant:
                post['reason'] = res.reason
                post['category'] = res.category
                return post
            return None
        except Exception as e:
            print(f"ERROR: Failed to process post {post.get('url')}: {e}")
            return None

    chunk_size = 50
    for i in range(0, len(posts), chunk_size):
        chunk = posts[i:i + chunk_size]
        print(f"INFO: Processing chunk {i//chunk_size + 1} ({i} to {min(i+chunk_size, len(posts))})...")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            chunk_results = list(executor.map(process_single_post, chunk))
        
        batch_relevant = [res for res in chunk_results if res]
        relevant_posts.extend(batch_relevant)
        irrelevant_count += (len(chunk) - len(batch_relevant))
        
        if batch_relevant:
            with open(checkpoint_path, "a", encoding="utf-8") as f:
                for item in batch_relevant:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
            print(f"INFO: Checkpoint updated with {len(batch_relevant)} posts at {checkpoint_path}")
            
    print(f"SUCCESS: Filtering complete. Retained {len(relevant_posts)} posts.")
    return relevant_posts
