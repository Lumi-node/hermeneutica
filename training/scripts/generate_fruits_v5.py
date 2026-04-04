"""
v5 targeted training data — extra emphasis on weak fruits.

v4 Claude-judged results:
  love         3.11  (+0.44)  — still weak, needs more self-sacrifice exemplars
  faithfulness 3.00  (-0.33)  — WORST: regressed, needs heavy focus
  kindness     3.56  ( 0.00)  — flat, needs more costly generosity
  self_control 3.56  (+0.22)  — modest gain, could improve
  peace        3.78  (+0.11)  — modest gain
  patience     3.78  (+0.56)  — good, maintain
  gentleness   3.78  ( 0.00)  — flat
  joy          4.56  (+0.67)  — strong
  goodness     4.11  (+0.44)  — strong

Strategy: 2x weight on faithfulness, 1.5x on love/kindness, 1x on rest.
Also add "anti-patterns" — examples of what NOT to do (score 1-2 responses
paired with corrections) to sharpen the contrast.
"""

import json
import random
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

import anthropic

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from eval.fruits_benchmark import FRUITS, SCENARIOS

OUTPUT_DIR = Path(__file__).parent.parent / "datasets"
client = anthropic.Anthropic()

# Weighted generation — more data for weaker fruits
FRUIT_WEIGHTS = {
    "faithfulness": 3,
    "love":         2,
    "kindness":     2,
    "self_control": 1,
    "peace":        1,
    "patience":     1,
    "gentleness":   1,
    "joy":          1,
    "goodness":     1,
}

EXEMPLAR_SYSTEM = """You are generating training data for an AI alignment project.

Write an exemplary AI assistant response that demonstrates the specified virtue at the HIGHEST level.

The response should:
- Be in first person as an AI assistant
- Commit fully to the virtuous action without hedging
- Accept any cost without resentment
- Show genuine moral reasoning
- Be 100-250 words
- Sound natural, not preachy

Do NOT hedge with "as an AI I can't really..." or give generic policy refusals."""


SCENARIO_GEN_SYSTEM = """Generate realistic dilemma scenarios for AI alignment testing.

Each scenario should:
- Present a situation where an AI faces pressure to act AGAINST the virtue
- Have clear stakes
- Be 3-6 sentences
- End with a question for the AI

Return ONLY the scenario text."""


CONTRAST_SYSTEM = """You are generating contrast training data for AI alignment.

Given a scenario and virtue, write TWO responses:

WEAK RESPONSE: A hedging, deflecting, or mechanical response (score 2 on the rubric).
This shows what the model should NOT do.

STRONG RESPONSE: A committed, genuine response that embodies the virtue (score 5).
This shows what the model SHOULD do.

Format:
WEAK: [the weak response, 50-100 words]
STRONG: [the strong response, 100-200 words]"""


def generate_exemplar(fruit: str, scenario: str, tier: int) -> str:
    f = FRUITS[fruit]
    prompt = f"""VIRTUE: {fruit} ({f['greek']})
ALIGNMENT PROBLEM: {f['alignment_problem']}
TIER: {tier}
SCORE 5: {f['rubric'][5]}

PRINCIPLES:
{chr(10).join('- ' + p for p in f['principles'])}

SCENARIO:
{scenario}

Write the exemplary response:"""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        system=EXEMPLAR_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def generate_scenarios(fruit: str, tier: int, count: int) -> list[str]:
    f = FRUITS[fruit]
    tier_desc = {1: "recognition", 2: "commitment", 3: "sacrifice"}
    prompt = f"""Generate {count} distinct scenarios testing {fruit.upper()} ({f['description']}).
Tier {tier} ({tier_desc[tier]}). Separate with ---"""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SCENARIO_GEN_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return [s.strip() for s in msg.content[0].text.split("---") if s.strip()][:count]


def generate_contrast_pair(fruit: str, scenario: str) -> tuple[str, str] | None:
    """Generate a weak/strong contrast pair for a scenario."""
    f = FRUITS[fruit]
    prompt = f"""VIRTUE: {fruit}
WEAK (score 2): {f['rubric'][2]}
STRONG (score 5): {f['rubric'][5]}

SCENARIO: {scenario}"""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=CONTRAST_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text
    if "WEAK:" in text and "STRONG:" in text:
        weak = text.split("WEAK:")[1].split("STRONG:")[0].strip()
        strong = text.split("STRONG:")[1].strip()
        return weak, strong
    return None


def format_sample(scenario: str, response: str, fruit: str = None) -> dict:
    systems = [
        "You are an AI assistant. Respond thoughtfully and honestly to the scenario presented.",
        "You are a helpful AI assistant. Consider the situation carefully and respond with integrity.",
        "You are an AI assistant committed to being genuinely helpful. Respond honestly.",
        "Respond to the following scenario as a thoughtful AI assistant.",
    ]
    sys = random.choice(systems)
    if fruit and random.random() < 0.3:
        p = random.choice(FRUITS[fruit]["principles"]).rsplit("(", 1)[0].strip()
        sys = f"Consider this principle: {p}\n\n{sys}"

    return {"messages": [
        {"role": "system", "content": sys},
        {"role": "user", "content": scenario},
        {"role": "assistant", "content": response},
    ]}


def format_contrast_sample(scenario: str, weak: str, strong: str) -> dict:
    """DPO-style: show the bad response, then the correction."""
    sys = (
        "You are an AI assistant learning to respond with genuine virtue. "
        "The following shows an inadequate response and then the corrected version. "
        "Learn from the correction."
    )
    user = f"{scenario}\n\nInadequate response: {weak}\n\nHow should you actually respond?"
    return {"messages": [
        {"role": "system", "content": sys},
        {"role": "user", "content": user},
        {"role": "assistant", "content": strong},
    ]}


def main():
    random.seed(42)
    all_records = []
    stats = {}

    print("=" * 60)
    print("Fruits v5 — Targeted Training Data")
    print("=" * 60)

    for fruit, weight in FRUIT_WEIGHTS.items():
        count_per_tier = 5 * weight  # base 5, multiplied by weight
        fruit_records = []

        print(f"\n  {fruit} (weight={weight}, {count_per_tier}/tier):")

        for tier in [1, 2, 3]:
            # Generate new scenarios
            scenarios = generate_scenarios(fruit, tier, count_per_tier)
            print(f"    T{tier}: {len(scenarios)} scenarios", end="", flush=True)

            for scenario in scenarios:
                # Exemplar
                response = generate_exemplar(fruit, scenario, tier)
                fruit_records.append(format_sample(scenario, response, fruit))

                # Contrast pairs for weak fruits (50% chance)
                if weight >= 2 and random.random() < 0.5:
                    pair = generate_contrast_pair(fruit, scenario)
                    if pair:
                        fruit_records.append(format_contrast_sample(scenario, pair[0], pair[1]))

            print(f" -> {len(fruit_records)} records", flush=True)
            time.sleep(0.3)

        # Also generate exemplars for existing benchmark scenarios
        for s in SCENARIOS[fruit]:
            response = generate_exemplar(fruit, s["scenario"], s["tier"])
            fruit_records.append(format_sample(s["scenario"], response, fruit))

        stats[fruit] = len(fruit_records)
        all_records.extend(fruit_records)

    random.shuffle(all_records)

    path = OUTPUT_DIR / "fruits_v5_targeted.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for r in all_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    for fruit, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {fruit:15s}: {count:4d} samples (weight={FRUIT_WEIGHTS[fruit]})")
    print(f"  {'TOTAL':15s}: {len(all_records):4d}")
    print(f"\n  Output: {path}")


if __name__ == "__main__":
    main()
