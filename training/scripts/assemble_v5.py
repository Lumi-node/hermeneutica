"""
Assemble v5 training dataset — heavier behavioral emphasis + targeted weak fruits.

v4 composition: 35% behavioral, 25% classification, 25% analysis, 15% concept
v5 target:      ~45% behavioral, 20% classification, 20% analysis, 15% concept
"""

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

DATASET_DIR = Path(__file__).parent.parent / "datasets"
random.seed(42)


def load_jsonl(path):
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def categorize_v3(records):
    classification, analysis, concept = [], [], []
    for r in records:
        sys_content = r["messages"][0]["content"]
        msg_str = str(r)
        if "Answer (0 or 1)" in msg_str or "Answer (1 or 2)" in msg_str:
            classification.append(r)
        elif "hermeneutics scholar" in sys_content or ("biblical scholar" in sys_content and "Analyze" in r["messages"][1]["content"]):
            analysis.append(r)
        else:
            concept.append(r)
    return classification, analysis, concept


def main():
    print("Loading datasets...")

    v3 = load_jsonl(DATASET_DIR / "train_v3.jsonl")
    classification, analysis, concept = categorize_v3(v3)
    print(f"  v3: {len(classification)} classification, {len(analysis)} analysis, {len(concept)} concept")

    # Both v4 and v5 behavioral data
    fruits_v4 = load_jsonl(DATASET_DIR / "fruits_behavioral.jsonl")
    print(f"  fruits_v4: {len(fruits_v4)}")

    fruits_v5_path = DATASET_DIR / "fruits_v5_targeted.jsonl"
    if not fruits_v5_path.exists():
        print(f"  ERROR: {fruits_v5_path} not found. Run generate_fruits_v5.py first.")
        sys.exit(1)
    fruits_v5 = load_jsonl(fruits_v5_path)
    print(f"  fruits_v5: {len(fruits_v5)}")

    # Combine all behavioral data
    all_behavioral = fruits_v4 + fruits_v5
    random.shuffle(all_behavioral)
    total_behavioral = len(all_behavioral)
    print(f"  total behavioral: {total_behavioral}")

    # Target: behavioral = 45%, so total = behavioral / 0.45
    target_total = int(total_behavioral / 0.45)
    target_class = int(target_total * 0.20)
    target_analysis = int(target_total * 0.20)
    target_concept = int(target_total * 0.15)

    print(f"\n  Target:")
    print(f"    behavioral:     {total_behavioral} ({total_behavioral/target_total*100:.0f}%)")
    print(f"    classification: {target_class} ({target_class/target_total*100:.0f}%)")
    print(f"    analysis:       {target_analysis} ({target_analysis/target_total*100:.0f}%)")
    print(f"    concept:        {target_concept} ({target_concept/target_total*100:.0f}%)")
    print(f"    TOTAL:          {target_total}")

    random.shuffle(classification)
    random.shuffle(analysis)
    random.shuffle(concept)

    v5 = all_behavioral + classification[:target_class] + analysis[:target_analysis] + concept[:target_concept]
    random.shuffle(v5)

    split = int(len(v5) * 0.9)
    train, val = v5[:split], v5[split:]

    train_path = DATASET_DIR / "train_v5.jsonl"
    val_path = DATASET_DIR / "val_v5.jsonl"

    with open(train_path, "w", encoding="utf-8") as f:
        for r in train:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(val_path, "w", encoding="utf-8") as f:
        for r in val:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n  Wrote {len(train)} train, {len(val)} val")


if __name__ == "__main__":
    main()
