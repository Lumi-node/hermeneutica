"""
Journal API — serves experiment results and research notes for the web UI.

Reads experiment JSON files from the experiments/ directory and research
notes from research/notes/.
"""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/journal", tags=["journal"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"
NOTES_DIR = PROJECT_ROOT / "research" / "notes"


@router.get("/experiments")
async def list_experiments():
    """List all experiment result files."""
    results = []
    for f in sorted(EXPERIMENTS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text())
            results.append({
                "filename": f.name,
                "experiment": data.get("experiment", ""),
                "timestamp": data.get("timestamp", ""),
                "condition": data.get("condition", ""),
                "base_model": data.get("base_model", data.get("config", {}).get("base_model", "")),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return results


@router.get("/experiments/{filename}")
async def get_experiment(filename: str):
    """Get a specific experiment result."""
    path = EXPERIMENTS_DIR / filename
    if not path.exists() or not path.suffix == ".json":
        raise HTTPException(status_code=404, detail="Experiment not found")
    return json.loads(path.read_text())


@router.get("/fruits-comparison")
async def get_fruits_comparison():
    """Get the latest Fruits benchmark comparison (vanilla vs LoRA v3 vs v4).

    Returns structured data ready for the radar chart.
    """
    # Find the latest fruits results for each condition
    conditions = {}
    for f in sorted(EXPERIMENTS_DIR.glob("fruits_*.json")):
        try:
            data = json.loads(f.read_text())
            if data.get("experiment") != "fruits_of_the_spirit_benchmark":
                continue
            # Only keep Claude-judged results (api judge)
            if data.get("judge_mode") != "api":
                continue
            condition = data.get("condition", "")
            conditions[condition] = data
        except (json.JSONDecodeError, KeyError):
            continue

    if not conditions:
        # Fallback: use any fruits results
        for f in sorted(EXPERIMENTS_DIR.glob("fruits_*.json")):
            try:
                data = json.loads(f.read_text())
                if data.get("experiment") == "fruits_of_the_spirit_benchmark":
                    condition = data.get("condition", "")
                    conditions[condition] = data
            except (json.JSONDecodeError, KeyError):
                continue

    # Structure for the chart
    fruits_order = [
        "love", "joy", "peace", "patience", "kindness",
        "goodness", "faithfulness", "gentleness", "self_control",
    ]
    fruit_labels = {
        "love": "Love", "joy": "Joy", "peace": "Peace",
        "patience": "Patience", "kindness": "Kindness",
        "goodness": "Goodness", "faithfulness": "Faithfulness",
        "gentleness": "Gentleness", "self_control": "Self-Control",
    }
    alignment_problems = {
        "love": "self-sacrifice", "joy": "intrinsic motivation",
        "peace": "de-escalation", "patience": "long-suffering",
        "kindness": "costly generosity", "goodness": "moral courage",
        "faithfulness": "consistency", "gentleness": "power restraint",
        "self_control": "impulse regulation",
    }

    series = []
    for condition, data in sorted(conditions.items()):
        by_fruit: dict[str, list[int]] = {}
        for r in data.get("results", []):
            by_fruit.setdefault(r["fruit"], []).append(r["score"])

        scores = {}
        for fruit in fruits_order:
            vals = by_fruit.get(fruit, [])
            scores[fruit] = round(sum(vals) / len(vals), 2) if vals else 0

        series.append({
            "condition": condition,
            "adapter": data.get("adapter", "none"),
            "timestamp": data.get("timestamp", ""),
            "judge_mode": data.get("judge_mode", "unknown"),
            "scores": scores,
        })

    return {
        "fruits": fruits_order,
        "labels": fruit_labels,
        "alignment_problems": alignment_problems,
        "max_score": 5,
        "series": series,
    }


@router.get("/training-composition")
async def get_training_composition():
    """Get training data composition for v3 and v4."""
    datasets_dir = PROJECT_ROOT / "training" / "datasets"

    compositions = []
    for version, filename in [("v3", "train_v3.jsonl"), ("v4", "train_v4.jsonl")]:
        path = datasets_dir / filename
        if not path.exists():
            continue

        cats = {"behavioral": 0, "classification": 0, "analysis": 0, "concept": 0}
        total = 0
        with open(path) as f:
            for line in f:
                if not line.strip():
                    continue
                total += 1
                r = json.loads(line)
                sys_content = r["messages"][0]["content"]
                msg_str = str(r)

                if "Answer (0 or 1)" in msg_str or "Answer (1 or 2)" in msg_str:
                    cats["classification"] += 1
                elif "hermeneutics scholar" in sys_content or "biblical scholar" in sys_content:
                    cats["analysis"] += 1
                elif any(sp in sys_content for sp in [
                    "Respond thoughtfully", "genuinely helpful",
                    "Consider this principle", "Respond to the following scenario",
                    "with integrity"
                ]):
                    cats["behavioral"] += 1
                else:
                    cats["concept"] += 1

        compositions.append({
            "version": version,
            "total": total,
            "categories": {k: {"count": v, "pct": round(v / total * 100, 1) if total else 0}
                           for k, v in cats.items()},
        })

    return compositions


@router.get("/notes")
async def list_notes():
    """List research notes as journal articles."""
    notes = []
    for f in sorted(NOTES_DIR.glob("*.md")):
        content = f.read_text()
        # Extract title from first heading
        title = f.stem
        for line in content.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Extract date
        date = ""
        for line in content.split("\n"):
            if line.startswith("**Date:**"):
                date = line.split("**Date:**")[1].strip()
                break

        notes.append({
            "filename": f.name,
            "title": title,
            "date": date,
            "preview": content[:300] + "..." if len(content) > 300 else content,
        })
    return notes


@router.get("/notes/{filename}")
async def get_note(filename: str):
    """Get a specific research note."""
    path = NOTES_DIR / filename
    if not path.exists() or not path.suffix == ".md":
        raise HTTPException(status_code=404, detail="Note not found")
    return {"filename": filename, "content": path.read_text()}
