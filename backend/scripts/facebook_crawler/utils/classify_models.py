import json
import os
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# --- 1. CLASSIFICATION SCHEMA ---
class ModelTag(BaseModel):
    model_name: str = Field(description="The specific VinFast model name: VF3, VFe34, VF5, VF6, VF7, VF8, VF9, or E-Motorbike. Use 'General EV' if multiple or not specified.")

def classify_post_model(text: str, llm_chain) -> str:
    """Invokes LLM to identify the car model from text."""
    try:
        res = llm_chain.invoke({"content": text[:2000]}) # Limit text length for efficiency
        return res.model_name
    except Exception:
        return "Unknown"

def run_model_classification(input_path: str):
    """
    Reads the processed dataset and assigns a car model tag to each post.
    """
    if not os.path.exists(input_path):
        print(f"ERROR: Input file not found at {input_path}")
        return

    print(f"INFO: Classification started for {input_path}...")

    # Initialize LLM
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
    try:
        structured_llm = llm.with_structured_output(ModelTag)
    except Exception:
        structured_llm = llm

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an automotive expert. Identify the specific VinFast vehicle model mentioned in the review.
        Models: VF3, VFe34, VF5, VF6, VF7, VF8, VF9.
        Other: E-Motorbike (Klara, Feliz, Evo, Vento).
        If multiple models or generic VinFast EV discussion, use 'General EV'.
        Output ONLY the model name."""),
        ("user", "Analyze this post content: {content}")
    ])
    
    chain = prompt | structured_llm
    
    updated_data = []
    
    # Load and Classify
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        total = len(lines)
        for i, line in enumerate(lines):
            item = json.loads(line.strip())
            content = item.get('full_text', item.get('text', ''))
            
            print(f"INFO: Classifying post {i+1}/{total}...", end="\r")
            item['car_model'] = classify_post_model(content, chain)
            updated_data.append(item)
            
    except Exception as e:
        print(f"\nERROR: Failed during classification: {e}")
        return

    # Save Results
    print("\nINFO: Saving classified dataset...")
    
    # Save JSONL
    with open(input_path, "w", encoding="utf-8") as f:
        for item in updated_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    # Update CSV
    csv_path = input_path.replace(".jsonl", ".csv")
    try:
        df = pd.DataFrame(updated_data)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"SUCCESS: Dataset updated with car models at {input_path} and {csv_path}")
    except Exception as e:
        print(f"ERROR: Failed to update CSV: {e}")

if __name__ == "__main__":
    DATA_PATH = "data/processed/vinfast_agent_clean.jsonl"
    run_model_classification(DATA_PATH)
