"""
Convert raw benchmark data (Parquet) into conversational SFT training JSONL format.
Formats data according to Gemma chat template:
  <start_of_turn>user
  {problem_statement}
  <end_of_turn>
  <start_of_turn>model
  {ground_truth_patch}
  <end_of_turn>
"""

import json
from pathlib import Path
import pandas as pd

RAW_DATA_PATH = Path("data/raw/swe_bench_lite.parquet")
OUTPUT_PATH = Path("data/processed/sft_training_data.jsonl")

def convert_to_sft_format():
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Missing {RAW_DATA_PATH}")

    df = pd.read_parquet(RAW_DATA_PATH)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    records = []
    for _, row in df.iterrows():
        repo = row["repo"]
        problem = row["problem_statement"]
        patch = row["patch"]

        # Filter out extremely large diffs to avoid context overflow
        if len(patch.splitlines()) > 100:
            continue

        system_instruction = (
            "You are CodeGuardian, an autonomous SWE agent. "
            "Analyze the problem statement and provide a minimal unified git patch that resolves the issue."
        )

        user_content = f"Repository: {repo}\n\nProblem Statement:\n{problem}\n\nPlease generate the minimal patch:"
        assistant_content = f"```diff\n{patch}\n```"

        conversation = {
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": assistant_content}
            ],
            "instance_id": row["instance_id"],
            "repo": repo
        }
        records.append(conversation)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for item in records:
            f.write(json.dumps(item) + "\n")

    print(f"Successfully processed {len(records)} training conversations to {OUTPUT_PATH}")

if __name__ == "__main__":
    convert_to_sft_format()
