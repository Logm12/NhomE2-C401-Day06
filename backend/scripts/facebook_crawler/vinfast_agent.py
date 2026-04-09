import os
import signal
import sys
import json
import operator
import pandas as pd
from typing import Annotated, List, TypedDict, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

from src.agent.tools.discover_posts import discover_posts_tool
from src.agent.tools.crawl_content import crawl_content_tool
from src.agent.tools.filter_posts import filter_posts_tool

load_dotenv()

# --- 1. STATE DEFINITION ---
class AgentState(TypedDict):
    posts: List[Dict[str, Any]]
    clean_dataset: Annotated[List[Dict[str, Any]], operator.add]
    iteration: int
    is_finished: bool

# --- 2. NODES IMPLEMENTATION ---

def discover_node(state: AgentState):
    """Step 1: Scans 100 new posts per target group."""
    print(f"\nINFO: [STEP 1: DISCOVER] Iteration {state['iteration'] + 1}")
    raw_posts = discover_posts_tool(limit_per_group=100)
    return {"posts": raw_posts, "iteration": state["iteration"] + 1}

def filter_node(state: AgentState):
    """Step 2: Pre-filters posts using gpt-5-mini BEFORE crawling deep content. Saves Apify credits."""
    print(f"INFO: [STEP 2: FILTER] Pre-filtering {len(state['posts'])} discovered posts...")
    
    if not state['posts']:
        return {"posts": []}
        
    relevant_posts = filter_posts_tool(state['posts'])
    
    # Overwrite state['posts'] with only relevant ones
    return {"posts": relevant_posts}

def crawl_node(state: AgentState):
    """Step 3: Fetches detailed content and comments ONLY for relevant posts."""
    print(f"INFO: [STEP 3: CRAWL] Fetching deep details for {len(state['posts'])} RELEVANT posts...")
    
    if not state['posts']:
        detailed_posts = []
    else:
        detailed_posts = crawl_content_tool(state['posts'])
        
    # We can stop after 1 robust iteration, or when we have enough data. 
    is_finished = state['iteration'] >= 1
    
    return {"clean_dataset": detailed_posts, "is_finished": is_finished}

# --- 3. GRAPH CONSTRUCTION ---

workflow = StateGraph(AgentState)

workflow.add_node("discover", discover_node)
workflow.add_node("crawl", crawl_node)
workflow.add_node("filter", filter_node)

workflow.set_entry_point("discover")
workflow.add_edge("discover", "filter")
workflow.add_edge("filter", "crawl")

def should_continue(state: AgentState):
    if state["is_finished"]:
        print("\nINFO: [FINISH] Dataset curation complete.")
        return END
    print("\nINFO: [LOOP] Continuing to next iteration.")
    return "discover"

workflow.add_conditional_edges("crawl", should_continue)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# --- 4. EXECUTION & EXPORT ---

def save_final_results(data):
    if not data:
        print("INFO: No data to save.")
        return
        
    os.makedirs("data/processed", exist_ok=True)
    
    # Save as JSONL
    with open("data/processed/vinfast_agent_clean.jsonl", "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    # Save as CSV
    df = pd.DataFrame(data)
    df.to_csv("data/processed/vinfast_agent_clean.csv", index=False, encoding="utf-8-sig")
    print(f"SUCCESS: Final dataset saved with {len(data)} entries.")

if __name__ == "__main__":
    initial_state = {
        "posts": [],
        "clean_dataset": [],
        "iteration": 0,
        "is_finished": False
    }
    
    print("INFO: Initializing VinFast AI Agent with gpt-5-mini...")
    print("INFO: Use Ctrl+C to stop and save the current progress at any time.")
    
    config = {"configurable": {"thread_id": "main_thread"}}

    # Graceful Shutdown Handler
    def signal_handler(sig, frame):
        print("\nINFO: Interrupt received. Saving results before exiting...")
        try:
            state_snapshot = app.get_state(config)
            if state_snapshot and state_snapshot.values:
                save_final_results(state_snapshot.values.get("clean_dataset", []))
            else:
                print("INFO: No intermediate data available.")
        except Exception as e:
            print(f"ERROR: Failed to save progress: {e}")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        final_output = app.invoke(initial_state, config=config)
        save_final_results(final_output["clean_dataset"])
    except (Exception, KeyboardInterrupt) as e:
        print(f"ERROR: Agent operation interrupted or failed: {e}")
        try:
            state_snapshot = app.get_state(config)
            save_final_results(state_snapshot.values.get("clean_dataset", []))
        except Exception:
            pass
