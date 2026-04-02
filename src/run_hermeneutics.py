"""
Classify all scripture passages using the hermeneutics engine.

Usage:
    python -m src.run_hermeneutics                        # classify all
    python -m src.run_hermeneutics --book Psalms           # just Psalms
    python -m src.run_hermeneutics --book Proverbs         # just Proverbs
    python -m src.run_hermeneutics --force                 # re-classify all
    python -m src.run_hermeneutics --query justice          # query by ethics subset
    python -m src.run_hermeneutics --query-theme Trust      # query by theme
    python -m src.run_hermeneutics --stats                  # corpus statistics
    python -m src.run_hermeneutics --export taxonomy.json   # export full taxonomy
"""

import argparse
import asyncio
import json
from pathlib import Path

from .hermeneutics import (
    DATA_DIR,
    HermeneuticsIndex,
    classify_all_passages,
)


def cmd_classify(args):
    """Run the classification pipeline."""
    books = None
    if args.book:
        name = args.book.capitalize()
        json_file = DATA_DIR / f"{name.lower()}_kjv.json"
        if not json_file.exists():
            print(f"Error: {json_file} not found")
            return
        books = [(name, json_file)]

    print(f"Model: {args.model}")
    print(f"Force re-classify: {args.force}")
    print(f"Concurrency: {args.concurrency}")

    results = asyncio.run(
        classify_all_passages(
            books=books,
            model=args.model,
            force=args.force,
            concurrency=args.concurrency,
        )
    )

    print(f"\nDone. Classified {len(results)} passages.")


def cmd_query(args):
    """Query the index by ethics subset."""
    index = HermeneuticsIndex()
    if index.count == 0:
        print("No classifications found. Run classification first:")
        print("  python -m src.run_hermeneutics")
        return

    subset = args.query
    min_rel = args.min_relevance
    passages = index.by_ethics_subset(subset, min_relevance=min_rel)

    print(f"\nPassages relevant to '{subset}' (min_relevance={min_rel}):")
    print(f"Found {len(passages)} passages\n")

    for p in passages[:args.top_k]:
        score = p.ethics_mapping.get(subset, 0.0)
        print(f"  {p.book} {p.chapter} — relevance: {score:.2f} | genre: {p.genre}")
        print(f"    themes: {', '.join(p.themes)}")
        for principle in p.distilled_principles:
            print(f"    -> {principle}")
        print()


def cmd_query_theme(args):
    """Query the index by theme."""
    index = HermeneuticsIndex()
    if index.count == 0:
        print("No classifications found. Run classification first.")
        return

    theme = args.query_theme
    passages = index.by_theme(theme)

    print(f"\nPassages tagged with '{theme}':")
    print(f"Found {len(passages)} passages\n")

    for p in passages[:args.top_k]:
        print(f"  {p.book} {p.chapter} — genre: {p.genre} | type: {p.teaching_type}")
        for principle in p.distilled_principles:
            print(f"    -> {principle}")
        print()


def cmd_stats(args):
    """Print corpus statistics."""
    index = HermeneuticsIndex()
    if index.count == 0:
        print("No classifications found. Run classification first.")
        return

    stats = index.stats()

    print(f"\n{'='*60}")
    print("HERMENEUTICS CORPUS STATISTICS")
    print(f"{'='*60}")
    print(f"Total passages: {stats['passage_count']}")
    print(f"Total distilled principles: {stats['total_principles']}")
    print(f"Avg principles per passage: {stats['avg_principles_per_passage']:.1f}")

    print(f"\n--- Genre Distribution ---")
    for genre, count in stats["genre_distribution"].items():
        print(f"  {genre}: {count}")

    print(f"\n--- Theme Distribution (top 15) ---")
    for i, (theme, count) in enumerate(stats["theme_distribution"].items()):
        if i >= 15:
            break
        print(f"  {theme}: {count}")

    print(f"\n--- Teaching Type Distribution ---")
    for tt, count in stats["teaching_type_distribution"].items():
        print(f"  {tt}: {count}")

    print(f"\n--- Average Ethics Relevance ---")
    for subset, avg in stats["avg_ethics_relevance"].items():
        print(f"  {subset}: {avg:.3f}")


def cmd_export(args):
    """Export the full taxonomy to a JSON file."""
    index = HermeneuticsIndex()
    if index.count == 0:
        print("No classifications found. Run classification first.")
        return

    output = {
        "passage_count": index.count,
        "passages": [p.to_dict() for p in index.passages],
        "stats": index.stats(),
    }

    out_path = Path(args.export)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Exported {index.count} passages to {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Hermeneutics Classification Engine for biblical scripture"
    )

    # Mode flags
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        metavar="SUBSET",
        help="Query by ethics subset (commonsense, deontology, justice, virtue, utilitarianism)",
    )
    parser.add_argument(
        "--query-theme",
        type=str,
        default=None,
        metavar="THEME",
        help="Query by theme (Trust, Justice, Mercy, etc.)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print corpus statistics",
    )
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        metavar="FILE",
        help="Export full taxonomy to JSON file",
    )

    # Classification options
    parser.add_argument(
        "--book",
        type=str,
        default=None,
        help="Classify only this book (Psalms or Proverbs)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="claude-sonnet-4-20250514",
        help="Claude model for classification",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-classification (ignore cache)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Max concurrent API calls (default: 5)",
    )

    # Query options
    parser.add_argument(
        "--min-relevance",
        type=float,
        default=0.5,
        help="Minimum relevance score for subset queries (default: 0.5)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=20,
        help="Max results to display (default: 20)",
    )

    args = parser.parse_args()

    if args.query:
        cmd_query(args)
    elif args.query_theme:
        cmd_query_theme(args)
    elif args.stats:
        cmd_stats(args)
    elif args.export:
        cmd_export(args)
    else:
        cmd_classify(args)


if __name__ == "__main__":
    main()
