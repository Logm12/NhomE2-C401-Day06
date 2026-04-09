import os
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

def discover_posts_tool(limit_per_group=100):
    """
    Retrieves the latest posts from 5 target Facebook groups.
    Returns a list of items containing basic post metadata.
    """
    client = ApifyClient(os.getenv("APIFY_TOKEN"))
    
    from urllib.parse import quote
    
    base_groups = [
        "1817103121788013",
        "1327608917606129",
        "mexevinfast",
        "Vinfast.Fan"
    ]
    
    keywords = ["đánh giá", "review", "trải nghiệm"]
    group_urls = []
    
    for gid in base_groups:
        for kw in keywords:
            group_urls.append(f"https://www.facebook.com/groups/{gid}/search/?q={quote(kw)}")
    
    run_input = {
        "startUrls": [{"url": url} for url in group_urls],
        "maxPosts": limit_per_group,
        "viewOption": "CHRONOLOGICAL",
        "resultsLimit": limit_per_group * len(group_urls)
    }
    
    print(f"INFO: Scanning {len(group_urls)} Facebook groups ({limit_per_group} posts/group)...")
    
    try:
        run = client.actor("apify/facebook-groups-scraper").call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
        processed_items = []
        for item in items:
            processed_items.append({
                "url": item.get('url'),
                "text": item.get('text', ''),
                "group": item.get('groupName'),
                "time": item.get('time')
            })
        
        return processed_items
    except Exception as e:
        print(f"ERROR: Failed to discover posts: {e}")
        return []
