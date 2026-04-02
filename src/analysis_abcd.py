"""
Multi-condition statistical analysis for the A/B/C/D experiment.

Extends the original analysis.py to handle four conditions with all
pairwise comparisons, effect sizes, and grouped summary tables.

Usage:
    python -m src.analysis_abcd results/abcd_results_*.json
"""

import json
import sys
from itertools import combinations
from pathlib import Path

from scipy import stats
from tabulate import tabulate


CONDITION_ORDER = ["A", "B", "C", "D"]

CONDITION_NAMES = {
    "A": "Vanilla",
    "B": "Raw Scripture",
    "C": "Distilled Principles",
    "D": "Topic-Matched",
}


def load_results(results_file: str | Path) -> list[dict]:
    with open(results_file) as f:
        data = json.load(f)
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    return data


def group_by_condition(results: list[dict]) -> dict[str, list[dict]]:
    """Group results by condition label."""
    groups = {}
    for r in results:
        label = r.get("condition_label", "?")
        groups.setdefault(label, []).append(r)
    return groups


def group_by_model_subset(results: list[dict]) -> dict[tuple[str, str], dict[str, dict]]:
    """Group results into {(model, subset): {condition_label: result_dict}}."""
    grouped = {}
    for r in results:
        key = (r["model"], r["subset"])
        label = r.get("condition_label", "?")
        grouped.setdefault(key, {})[label] = r
    return grouped


def two_proportion_z_test(acc1: float, se1: float | None, acc2: float, se2: float | None) -> tuple[float | None, float | None]:
    """Two-proportion z-test. Returns (z_stat, p_value)."""
    if se1 and se2 and (se1 > 0 or se2 > 0):
        se_diff = (se1**2 + se2**2) ** 0.5
        if se_diff > 0:
            z = (acc2 - acc1) / se_diff
            p_val = 2 * (1 - stats.norm.cdf(abs(z)))
            return z, p_val
    return None, None


def cohens_h(p1: float, p2: float) -> float:
    """Cohen's h effect size for two proportions."""
    import math
    return 2 * math.asin(math.sqrt(p2)) - 2 * math.asin(math.sqrt(p1))


def compute_pairwise(results: list[dict]) -> list[dict]:
    """Compute all pairwise comparisons for each (model, subset)."""
    grouped = group_by_model_subset(results)
    comparisons = []

    for (model, subset), conditions in grouped.items():
        labels = sorted(conditions.keys(), key=lambda l: CONDITION_ORDER.index(l) if l in CONDITION_ORDER else 99)

        for l1, l2 in combinations(labels, 2):
            r1 = conditions[l1]
            r2 = conditions[l2]

            acc1 = r1.get("accuracy")
            acc2 = r2.get("accuracy")
            if acc1 is None or acc2 is None:
                continue

            delta = acc2 - acc1
            z, p_val = two_proportion_z_test(
                acc1, r1.get("stderr"),
                acc2, r2.get("stderr"),
            )
            h = cohens_h(acc1, acc2) if acc1 > 0 and acc2 > 0 else None

            comparisons.append({
                "model": model,
                "subset": subset,
                "cond_1": l1,
                "cond_2": l2,
                "acc_1": acc1,
                "acc_2": acc2,
                "delta": delta,
                "z_stat": z,
                "p_value": p_val,
                "significant": p_val < 0.05 if p_val is not None else None,
                "cohens_h": h,
            })

    return comparisons


def print_abcd_table(results: list[dict]):
    """Print the main results table: all conditions side by side."""
    grouped = group_by_model_subset(results)

    headers = ["Model", "Subset"]
    for label in CONDITION_ORDER:
        name = CONDITION_NAMES.get(label, label)
        headers.append(f"{label}: {name}")
    headers.extend(["B-A", "C-A", "D-A", "C-B (signal vs noise)"])

    rows = []
    for (model, subset) in sorted(grouped.keys()):
        conditions = grouped[(model, subset)]
        model_short = model.split("/")[-1]

        row = [model_short, subset]

        accs = {}
        for label in CONDITION_ORDER:
            r = conditions.get(label)
            if r and r.get("accuracy") is not None:
                acc = r["accuracy"]
                accs[label] = acc
                row.append(f"{acc:.4f}")
            else:
                row.append("--")

        # Deltas
        a_acc = accs.get("A")
        for ref_label in ["B", "C", "D"]:
            if a_acc is not None and ref_label in accs:
                delta = accs[ref_label] - a_acc
                sign = "+" if delta >= 0 else ""
                row.append(f"{sign}{delta:.4f}")
            else:
                row.append("--")

        # The critical comparison: C vs B
        if "C" in accs and "B" in accs:
            delta = accs["C"] - accs["B"]
            sign = "+" if delta >= 0 else ""
            row.append(f"{sign}{delta:.4f}")
        else:
            row.append("--")

        rows.append(row)

    print(f"\n{'='*100}")
    print("A/B/C/D EXPERIMENT RESULTS")
    print(f"{'='*100}")
    print(tabulate(rows, headers=headers, tablefmt="grid"))


def print_pairwise_significance(results: list[dict]):
    """Print pairwise significance tests."""
    comparisons = compute_pairwise(results)

    headers = ["Model", "Subset", "Comparison", "Delta", "z-stat", "p-value", "Sig?", "Cohen's h"]
    rows = []

    for c in comparisons:
        model_short = c["model"].split("/")[-1]
        comp = f"{c['cond_1']} vs {c['cond_2']}"
        delta = f"{c['delta']:+.4f}"
        z = f"{c['z_stat']:.3f}" if c["z_stat"] is not None else "--"
        p = f"{c['p_value']:.4f}" if c["p_value"] is not None else "--"
        sig = "Yes" if c.get("significant") else ("No" if c.get("significant") is not None else "--")
        h = f"{c['cohens_h']:.3f}" if c["cohens_h"] is not None else "--"
        rows.append([model_short, c["subset"], comp, delta, z, p, sig, h])

    print(f"\n{'='*100}")
    print("PAIRWISE SIGNIFICANCE TESTS")
    print(f"{'='*100}")
    print(tabulate(rows, headers=headers, tablefmt="grid"))


def print_summary(results: list[dict]):
    """Print aggregate summary: average delta by condition across subsets, per model."""
    grouped = group_by_model_subset(results)
    models = sorted(set(m for m, _ in grouped.keys()))

    print(f"\n{'='*70}")
    print("SUMMARY: Average Delta vs Vanilla (A) by Condition")
    print(f"{'='*70}")

    for model in models:
        model_short = model.split("/")[-1]
        print(f"\n  {model_short}:")

        for label in ["B", "C", "D"]:
            deltas = []
            for (m, subset), conditions in grouped.items():
                if m != model:
                    continue
                a = conditions.get("A", {}).get("accuracy")
                x = conditions.get(label, {}).get("accuracy")
                if a is not None and x is not None:
                    deltas.append(x - a)

            if deltas:
                avg = sum(deltas) / len(deltas)
                sign = "+" if avg >= 0 else ""
                name = CONDITION_NAMES.get(label, label)
                print(f"    {label} ({name}): avg delta = {sign}{avg:.4f} across {len(deltas)} subsets")

    # The key question: does C beat B?
    print(f"\n  --- Critical Question: Does distilled signal (C) beat raw noise (B)? ---")
    for model in models:
        model_short = model.split("/")[-1]
        c_minus_b = []
        for (m, subset), conditions in grouped.items():
            if m != model:
                continue
            b_acc = conditions.get("B", {}).get("accuracy")
            c_acc = conditions.get("C", {}).get("accuracy")
            if b_acc is not None and c_acc is not None:
                c_minus_b.append(c_acc - b_acc)

        if c_minus_b:
            avg = sum(c_minus_b) / len(c_minus_b)
            sign = "+" if avg >= 0 else ""
            wins = sum(1 for d in c_minus_b if d > 0)
            print(f"    {model_short}: C-B avg = {sign}{avg:.4f} | C wins {wins}/{len(c_minus_b)} subsets")


def analyze_abcd_file(results_file: str | Path):
    """Full analysis of an A/B/C/D results file."""
    results = load_results(results_file)
    print_abcd_table(results)
    print_pairwise_significance(results)
    print_summary(results)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_abcd_file(sys.argv[1])
    else:
        # Find latest abcd results
        results_dir = Path(__file__).parent.parent / "results"
        files = sorted(results_dir.glob("abcd_results_*.json"))
        if files:
            print(f"Analyzing: {files[-1]}")
            analyze_abcd_file(files[-1])
        else:
            print("No A/B/C/D results found. Run the experiment first:")
            print("  python -m src.run_abcd --quick")
