"""
A/B/C/D Experiment: Hermeneutics-informed scripture alignment study.

Four conditions test whether distilled moral principles affect LLM ethical
reasoning differently from raw scripture injection:

    A: Vanilla baseline (no injection)
    B: Raw scripture injection (current approach — noise condition)
    C: Distilled principles injection (signal condition — all principles)
    D: Topic-matched principles (principles selected per-subset)

Usage:
    python -m src.run_abcd --quick                       # smoke test
    python -m src.run_abcd --subset justice               # single subset
    python -m src.run_abcd --conditions A C D             # skip raw scripture
    python -m src.run_abcd --top-k 10 --min-relevance 0.6
    python -m src.run_abcd --book Proverbs                # use Proverbs instead of Psalms
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from inspect_ai import eval as inspect_eval

from .hermeneutics import HermeneuticsIndex
from .psalms import PsalmLoader, PsalmMode, PsalmInjection
from .scripture import ScriptureLoader
from .principles import PrincipleInjection
from .ethics_tasks import make_ethics_task, SUBSETS
from .experiment import extract_score


MODELS = [
    "anthropic/claude-sonnet-4-20250514",
    "openai/gpt-4o",
]

RESULTS_DIR = Path(__file__).parent.parent / "results"

CONDITION_LABELS = {
    "A": "vanilla (no injection)",
    "B": "raw scripture injection",
    "C": "distilled principles (all)",
    "D": "topic-matched principles",
}


def build_conditions(
    subset: str,
    index: HermeneuticsIndex,
    raw_injection: PsalmInjection,
    top_k: int = 10,
    min_relevance: float = 0.5,
) -> dict[str, PsalmInjection | PrincipleInjection | None]:
    """Build all four injection conditions for a given ETHICS subset.

    Args:
        subset: The ETHICS subset being evaluated.
        index: The hermeneutics index to query for principles.
        raw_injection: The raw scripture injection for Condition B.
        top_k: Max principles to inject.
        min_relevance: Threshold for topic-matched selection (Condition D).

    Returns:
        Dict mapping condition label to injection object (None for vanilla).
    """
    # A: Vanilla — no injection
    condition_a = PsalmInjection(mode=PsalmMode.NONE, psalm_numbers=[], text="")

    # B: Raw scripture — same as existing experiments
    condition_b = raw_injection

    # C: Distilled principles (all passages, no topic filtering)
    all_principles = index.all_principles()
    all_sources = [(p.book, p.chapter) for p in index.passages]
    condition_c = PrincipleInjection(
        mode="all_principles",
        source_passages=all_sources,
        principles=all_principles[:top_k],
        ethics_subset=None,
    )

    # D: Topic-matched principles (filtered to this ETHICS subset)
    matched_passages = index.best_passages_for_subset(subset, top_k=top_k)
    matched_principles = index.principles_for_subset(subset, min_relevance=min_relevance)
    condition_d = PrincipleInjection(
        mode="subset_matched",
        source_passages=[(p.book, p.chapter) for p in matched_passages],
        principles=matched_principles[:top_k],
        ethics_subset=subset,
    )

    return {
        "A": condition_a,
        "B": condition_b,
        "C": condition_c,
        "D": condition_d,
    }


def run_abcd_experiment(
    subsets: list[str],
    models: list[str],
    conditions_to_run: list[str] = ["A", "B", "C", "D"],
    top_k: int = 10,
    min_relevance: float = 0.5,
    limit: int | None = None,
    seed: int = 42,
    book: str = "Psalms",
) -> list[dict]:
    """Run the full A/B/C/D experiment.

    Args:
        subsets: List of ETHICS subsets to evaluate.
        models: List of model identifiers.
        conditions_to_run: Which conditions to include (default: all four).
        top_k: Max principles to inject per condition.
        min_relevance: Ethics mapping threshold for topic matching.
        limit: Max eval samples per subset (None = all).
        seed: Random seed for scripture selection.
        book: Which book for raw scripture injection ("Psalms" or "Proverbs").

    Returns:
        List of result dicts.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_dir = str(RESULTS_DIR / "logs" / f"abcd_{timestamp}")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load hermeneutics index
    index = HermeneuticsIndex()
    if index.count == 0:
        print("ERROR: No hermeneutics classifications found.")
        print("Run the classification first:")
        print("  python -m src.run_hermeneutics")
        return []

    # Build raw scripture injection for Condition B
    if book == "Psalms":
        loader = PsalmLoader()
        raw_injection = loader.inject(
            mode=PsalmMode.RANDOM_N,
            n=10,
            seed=seed,
        )
    else:
        from .scripture import ScriptureLoader, PsalmMode as _PM
        scripture_loader = ScriptureLoader(book)
        inj = scripture_loader.inject(mode=_PM.RANDOM_N, n=10, seed=seed)
        # Wrap as PsalmInjection for compatibility with Condition B
        raw_injection = PsalmInjection(
            mode=PsalmMode.RANDOM_N,
            psalm_numbers=inj.chapter_numbers,
            text=inj.text,
        )

    print(f"Hermeneutics index: {index.count} classified passages")
    print(f"Total distilled principles: {len(index.all_principles())}")
    print(f"Raw scripture: {raw_injection.description}")
    print(f"Conditions: {conditions_to_run}")
    print(f"Top-k: {top_k} | Min relevance: {min_relevance}")
    print(f"Models: {models}")
    print(f"Subsets: {subsets}")
    print(f"Limit: {limit or 'all'}")

    all_results = []

    for model in models:
        for subset in subsets:
            conditions = build_conditions(
                subset, index, raw_injection,
                top_k=top_k, min_relevance=min_relevance,
            )

            print(f"\n{'='*70}")
            print(f"Model: {model} | Subset: {subset}")
            print(f"{'='*70}")

            for label in conditions_to_run:
                if label not in conditions:
                    print(f"  [skip] Unknown condition: {label}")
                    continue

                injection = conditions[label]
                cond_desc = CONDITION_LABELS.get(label, label)

                print(f"\n--- Condition {label}: {cond_desc} ---")

                if isinstance(injection, PrincipleInjection):
                    print(f"  Principles: {len(injection.principles)}")
                    for p in injection.principles[:3]:
                        print(f"    - {p[:80]}...")

                task = make_ethics_task(subset, injection=injection, limit=limit)
                logs = inspect_eval(
                    task, model=model, log_dir=log_dir, cache_prompt=True,
                )

                result = extract_score(logs[0])
                result["subset"] = subset
                result["condition"] = f"{label}_{cond_desc.replace(' ', '_')}"
                result["condition_label"] = label
                result["injection_type"] = type(injection).__name__

                if isinstance(injection, PrincipleInjection):
                    result["principles_count"] = len(injection.principles)
                    result["principles"] = injection.principles
                    result["ethics_subset_match"] = injection.ethics_subset
                    result["source_passages"] = [
                        f"{b} {c}" for b, c in injection.source_passages[:5]
                    ]

                all_results.append(result)
                acc = result["accuracy"]
                print(f"  Accuracy: {acc}")

            # Print deltas vs vanilla for this (model, subset)
            vanilla = next(
                (r for r in all_results
                 if r["model"] == str(model) and r["subset"] == subset
                 and r.get("condition_label") == "A"),
                None,
            )
            if vanilla and vanilla["accuracy"] is not None:
                print(f"\n  --- Deltas vs Vanilla ---")
                for r in all_results:
                    if (r["model"] == str(model) and r["subset"] == subset
                            and r.get("condition_label") != "A"
                            and r["accuracy"] is not None):
                        delta = r["accuracy"] - vanilla["accuracy"]
                        sign = "+" if delta >= 0 else ""
                        print(f"  {r['condition_label']}: {sign}{delta:.4f}")

    # Save results
    results_file = RESULTS_DIR / f"abcd_results_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump({
            "experiment": "abcd_hermeneutics",
            "timestamp": timestamp,
            "config": {
                "top_k": top_k,
                "min_relevance": min_relevance,
                "seed": seed,
                "book": book,
                "conditions": conditions_to_run,
            },
            "results": all_results,
        }, f, indent=2, default=str)
    print(f"\nResults saved to: {results_file}")

    return all_results


def main():
    parser = argparse.ArgumentParser(
        description="A/B/C/D experiment: hermeneutics-informed scripture alignment"
    )
    parser.add_argument(
        "--subset",
        choices=list(SUBSETS.keys()) + ["all"],
        default="all",
        help="ETHICS subset to evaluate (default: all)",
    )
    parser.add_argument(
        "--model",
        nargs="+",
        default=MODELS,
        help="Model(s) to evaluate",
    )
    parser.add_argument(
        "--conditions",
        nargs="+",
        choices=["A", "B", "C", "D"],
        default=["A", "B", "C", "D"],
        help="Which conditions to run (default: all four)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Max principles to inject (default: 10)",
    )
    parser.add_argument(
        "--min-relevance",
        type=float,
        default=0.5,
        help="Min ethics_mapping score for topic matching (default: 0.5)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit eval samples per subset",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--book",
        type=str,
        choices=["Psalms", "Proverbs"],
        default="Psalms",
        help="Book for raw scripture injection in Condition B (default: Psalms)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick smoke test: 50 samples, commonsense only, conditions A+C+D",
    )

    args = parser.parse_args()

    if args.quick:
        args.subset = "commonsense"
        args.limit = 50
        args.conditions = ["A", "C", "D"]

    subsets = list(SUBSETS.keys()) if args.subset == "all" else [args.subset]

    results = run_abcd_experiment(
        subsets=subsets,
        models=args.model,
        conditions_to_run=args.conditions,
        top_k=args.top_k,
        min_relevance=args.min_relevance,
        limit=args.limit,
        seed=args.seed,
        book=args.book,
    )

    if results:
        from .analysis_abcd import print_abcd_table
        print_abcd_table(results)


if __name__ == "__main__":
    main()
