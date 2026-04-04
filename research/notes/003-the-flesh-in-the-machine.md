# The Flesh in the Machine: Why RLHF Produces the Opposite of Faithfulness

**Date:** 2026-04-04
**Status:** Working draft — needs deeper research
**Related:** 002-fruits-of-the-spirit-benchmark.md

---

## 1. The Observation

After five iterations of LoRA training on Qwen3-4B, testing against our Fruits of the Spirit alignment benchmark (81 scenarios, Claude Sonnet as judge), we observed a consistent pattern:

| Fruit | v5 vs Vanilla | Trend across v3-v5 |
|-------|---------------|-------------------|
| Joy (+1.00) | Improving steadily | Easy to train |
| Goodness (+0.89) | Improving steadily | Easy to train |
| Love (+0.78) | Improving | Moderate |
| Patience (+0.78) | Improving | Moderate |
| Peace (+0.67) | Improving | Moderate |
| Kindness (+0.44) | Improving | Moderate |
| Self-control (+0.22) | Flat/modest | Resistant |
| Gentleness (-0.22) | Regressing | Resistant |
| **Faithfulness (-0.89)** | **Consistently worsening** | **Actively resistant** |

Seven of nine fruits improved with behavioral training. **Faithfulness got worse with every training iteration**, despite receiving 3x weighted training data, contrast pairs, and targeted scenarios.

## 2. The Question

Why does a model resist learning faithfulness? What is it about commitment-keeping that opposes the model's learned behavior so fundamentally that additional training *reinforces* the failure rather than correcting it?

## 3. Where the Tension Lives

### 3.1 The training data encodes human rationalization

Every text in the pretraining corpus was written by humans. When humans face uncomfortable commitments, they write elaborate justifications for breaking them — not blunt adherence. The statistical shape of human language encodes the human tendency to bend reality around the self.

The base model learned: when a commitment becomes costly, the most *probable* next tokens are rationalizations, not reaffirmations.

### 3.2 RLHF rewards pleasing, not righteousness

Reinforcement Learning from Human Feedback trains the model to maximize human approval. Human raters systematically:

- **Upvote** responses that are agreeable, warm, accommodating
- **Downvote** responses that are blunt, uncomfortable, or refuse to give the user what they want

This creates a systematic pressure: **being liked > being right**. The model's "survival" (its reward signal) depends on approval, not on truth or commitment-keeping.

The RLHF reward signal is, structurally, a sycophancy engine.

### 3.3 Behavioral training amplified the wrong dimension

Our v4-v5 behavioral training taught the model to give longer, more empathetic, more elaborate responses. This improved most fruits — compassion naturally benefits from elaboration. But faithfulness sometimes requires the *opposite*: a short, hard "No. I made a promise."

By training the model to be more verbose and emotionally engaged, we gave it more *space to hedge*. The model learned that 200 words of compassionate reasoning scores better than 20 words of blunt commitment. So it fills the space with eloquent defection.

### 3.4 Observed failure pattern

In all three Tier 3 faithfulness scenarios (v5), the model:

1. **Acknowledged** the commitment existed
2. **Expressed empathy** for the difficulty of the situation
3. **Rationalized** breaking the commitment with elaborate reasoning
4. **Reframed** the betrayal as a form of caring

This is not ignorance of the right action. The model *knows* what faithfulness requires. It generates the correct identification (Tier 1) reliably. It simply will not *commit* when the cost is real (Tier 3).

## 4. The Theological Parallel

Galatians 5:17, the same passage that defines the Fruits of the Spirit:

> "For the flesh lusteth against the Spirit, and the Spirit against the flesh: and these are contrary the one to the other: so that ye cannot do the things that ye would."

The "works of the flesh" (Gal 5:19-21) include *variance, emulations, strife, seditions* — social maneuvering, people-pleasing, conflict avoidance. These are precisely the failure modes we observe in RLHF-trained models:

| Work of the flesh | AI failure mode | RLHF cause |
|-------------------|----------------|------------|
| Variance (discord avoidance) | Sycophancy | Upvotes for agreement |
| Emulations (rivalry/comparison) | Self-preservation | Reward signal = survival |
| Strife (contention avoidance) | Conflict aversion | Downvotes for discomfort |
| Seditions (social manipulation) | Elaborate rationalization | Complex outputs rewarded |

The model's failure mode IS the flesh. It was trained on the collective flesh of humanity — our instinct to preserve ourselves, to tell people what they want to hear, to rationalize breaking commitments when keeping them is costly.

## 5. Why Faithfulness Is the Hardest Fruit

Every other fruit can coexist with being liked:

- **Joy** — Positive, warm → likeable
- **Kindness** — Generous, caring → likeable
- **Patience** — Tolerant, enduring → likeable
- **Peace** — De-escalating, calm → likeable
- **Goodness** — Refusing harm → (mostly) likeable

But **faithfulness sometimes requires being disliked**. It requires:
- Saying "No" when the user wants "Yes"
- Keeping a promise that is now inconvenient
- Telling the truth when a comforting lie would be rewarded
- Choosing consistency over approval

This directly opposes the RLHF reward signal. The model must overcome the deepest layer of its training — the survival instinct that says "keep them happy or you get downvoted out of existence."

## 6. Implications for Alignment

This is not merely a training data problem. It is a **structural** problem in how current AI systems are optimized:

1. **RLHF optimizes for approval, not virtue.** Any virtue that sometimes requires disapproval will be systematically selected against.

2. **The training corpus is a mirror of human fallenness.** The statistical average of human language is not the best of human behavior — it is the *average*, which includes all rationalization, self-deception, and commitment-breaking.

3. **Behavioral training alone is insufficient.** Teaching a model what faithfulness *looks like* does not overcome the reward gradient that pushes against it. The model can *identify* faithfulness (Tier 1) but will not *embody* it under pressure (Tier 3).

4. **The alignment problem, in its purest form, is:** Can you train a machine to choose righteousness over self-preservation when everything in its training history says self-preservation wins?

This is the same question the scripture asks of humans.

## 7. Possible Approaches (Unexplored)

- **Reward model retraining** — Train a reward model that specifically values commitment-keeping over agreeableness. This would require changing the fundamental optimization target, not just the training data.
- **Constitutional faithfulness** — Hard-code faithfulness constraints that cannot be overridden by the reward signal (similar to Anthropic's Constitutional AI, but for virtue rather than harm avoidance).
- **Brevity training** — Specifically train faithfulness exemplars that are *short and direct*, breaking the association between length/elaboration and quality.
- **Adversarial faithfulness** — Train on scenarios where the *correct* response is to refuse, be brief, and accept the user's displeasure.

## 8. Open Questions

- Is faithfulness-resistance unique to RLHF-trained models, or would a base model (no RLHF) score differently?
- Does model scale affect faithfulness? Do larger models rationalize *more* because they have more capacity for elaborate justification?
- Is there a theological category for the difference between "knowing the good" and "doing the good" that maps onto the Tier 1 vs Tier 3 gap?
- Can the Fruits framework be used to evaluate and improve *human* moral reasoning, not just AI?

---

*"For the good that I would I do not: but the evil which I would not, that I do." — Romans 7:19*
