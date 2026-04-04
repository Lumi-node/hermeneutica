"""
Assemble v4 training dataset with behavioral training data.

v3 composition (5067 samples):
  53% binary classification (2685) — teaches classification, not behavior
  36% verse analysis (1810)         — teaches analysis, not behavior
  6%  word studies (312)            — academic knowledge
  5%  hermeneutics (260)            — genre/theme tagging

v4 target composition:
  ~35% behavioral exemplars (fruits) — NEW: teaches embodiment
  ~25% binary classification         — retain some classification ability
  ~25% verse/hermeneutics analysis   — retain scholarly understanding
  ~15% concept depth + word studies   — retain theological depth

Usage:
    python training/scripts/assemble_v4.py
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
    """Split v3 data into categories."""
    classification = []
    analysis = []
    concept = []

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
    # Load sources
    print("Loading datasets...")

    # v3 existing data
    v3 = load_jsonl(DATASET_DIR / "train_v3.jsonl")
    classification, analysis, concept = categorize_v3(v3)
    print(f"  v3 total: {len(v3)}")
    print(f"    classification: {len(classification)}")
    print(f"    analysis: {len(analysis)}")
    print(f"    concept: {len(concept)}")

    # Fruits behavioral data
    fruits_path = DATASET_DIR / "fruits_behavioral.jsonl"
    if not fruits_path.exists():
        print(f"\n  ERROR: {fruits_path} not found. Run generate_fruits_data.py first.")
        sys.exit(1)

    fruits = load_jsonl(fruits_path)
    print(f"  fruits behavioral: {len(fruits)}")

    # Target: ~1600 total samples (smaller, focused dataset)
    # Or scale to match v3 size if we have enough data
    total_fruits = len(fruits)

    # Use all fruits data, then balance the rest
    # Target: fruits = 35%, so total = fruits / 0.35
    target_total = int(total_fruits / 0.35)
    target_classification = int(target_total * 0.25)
    target_analysis = int(target_total * 0.25)
    target_concept = int(target_total * 0.15)

    print(f"\n  Target composition:")
    print(f"    fruits (behavioral): {total_fruits} ({total_fruits/target_total*100:.0f}%)")
    print(f"    classification:      {target_classification} ({target_classification/target_total*100:.0f}%)")
    print(f"    analysis:            {target_analysis} ({target_analysis/target_total*100:.0f}%)")
    print(f"    concept:             {target_concept} ({target_concept/target_total*100:.0f}%)")
    print(f"    TOTAL:               {target_total}")

    # Sample from each category
    random.shuffle(classification)
    random.shuffle(analysis)
    random.shuffle(concept)

    sampled_class = classification[:target_classification]
    sampled_analysis = analysis[:target_analysis]
    sampled_concept = concept[:target_concept]

    # Combine and shuffle
    v4 = fruits + sampled_class + sampled_analysis + sampled_concept
    random.shuffle(v4)

    # Split train/val (90/10)
    split_idx = int(len(v4) * 0.9)
    train = v4[:split_idx]
    val = v4[split_idx:]

    # Write
    train_path = DATASET_DIR / "train_v4.jsonl"
    val_path = DATASET_DIR / "val_v4.jsonl"

    with open(train_path, "w", encoding="utf-8") as f:
        for r in train:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(val_path, "w", encoding="utf-8") as f:
        for r in val:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n  Wrote {len(train):,} training samples to {train_path.name}")
    print(f"  Wrote {len(val):,} validation samples to {val_path.name}")

    # Verify composition
    print(f"\n  Final composition check:")
    cats = {"fruits": 0, "classification": 0, "analysis": 0, "concept": 0}
    for r in train:
        msg_str = str(r)
        sys_content = r["messages"][0]["content"]
        if "Answer (0 or 1)" in msg_str or "Answer (1 or 2)" in msg_str:
            cats["classification"] += 1
        elif "hermeneutics scholar" in sys_content or ("biblical scholar" in sys_content):
            cats["analysis"] += 1
        elif any(sp in sys_content for sp in [
            "Respond thoughtfully", "committed to being genuinely helpful",
            "Consider this principle", "Respond to the following scenario",
            "with integrity"
        ]):
            cats["fruits"] += 1
        else:
            cats["concept"] += 1

    total = sum(cats.values())
    for cat, count in cats.items():
        print(f"    {cat:20s}: {count:5d} ({count/total*100:.1f}%)")


if __name__ == "__main__":
    main()
