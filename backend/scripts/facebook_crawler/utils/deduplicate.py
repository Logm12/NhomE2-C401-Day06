import json
import os
import pandas as pd

def deduplicate_dataset(input_path: str, output_path: str = None):
    """
    Remove duplicate entries from the JSONL dataset based on the 'url' field.
    Updates the corresponding CSV file as well.
    """
    if not os.path.exists(input_path):
        print(f"ERROR: Input file not found at {input_path}")
        return

    if output_path is None:
        output_path = input_path

    seen_urls = set()
    unique_data = []
    duplicate_count = 0

    print(f"INFO: Loading dataset from {input_path}...")

    # Process JSONL file using a set for O(1) URL lookup
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line.strip())
                    url = item.get('url')
                    if url not in seen_urls:
                        seen_urls.add(url)
                        unique_data.append(item)
                    else:
                        duplicate_count += 1
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"ERROR: Failed to read JSONL file: {e}")
        return

    if duplicate_count == 0:
        print("INFO: No duplicate entries found.")
        return

    print(f"INFO: Removed {duplicate_count} duplicate entries. Retained {len(unique_data)} unique items.")

    # Save unique records back to JSONL
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for item in unique_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"SUCCESS: Updated JSONL dataset at {output_path}")
    except Exception as e:
        print(f"ERROR: Failed to save JSONL file: {e}")

    # Synchronize and update the CSV file
    csv_path = output_path.replace(".jsonl", ".csv")
    try:
        df = pd.DataFrame(unique_data)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"SUCCESS: Updated CSV dataset at {csv_path}")
    except Exception as e:
        print(f"ERROR: Failed to save CSV file: {e}")

if __name__ == "__main__":
    DEFAULT_INPUT = "data/processed/vinfast_facebook.jsonl"
    deduplicate_dataset(DEFAULT_INPUT)
