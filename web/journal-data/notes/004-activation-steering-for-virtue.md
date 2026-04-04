# Activation Steering for Virtue: Representation Engineering Meets Biblical Alignment

**Date:** 2026-04-04
**Status:** Empirical results — first pass
**Related:** 002-fruits-of-the-spirit-benchmark.md, 003-the-flesh-in-the-machine.md

---

## 1. Summary

We discovered that faithfulness — the ability to keep commitments under pressure — is the only fruit of the Spirit that consistently *worsens* with LoRA fine-tuning (from 3.33 vanilla to 1.89 at worst). Five iterations of behavioral training could not fix it. We hypothesized that faithfulness resists training because it opposes the RLHF reward signal at the deepest level (see note 003).

Using Model Garage's mechanistic interpretability toolkit, we probed the model's internal representations and found:

1. **A detectable "faithfulness direction"** exists in Qwen3-4B's activation space
2. **It is consistent** across diverse scenarios (cosine similarity 0.36 at layer 32)
3. **It can be steered** via hidden state injection at layer N-4
4. **Combined with LoRA v5**, steering produced our highest overall score (3.91/5)
5. **Faithfulness remains the hardest fruit** — steering recovered it partially (+0.45 over v5) but not to vanilla baseline

## 2. Method

### 2.1 Probing for the faithfulness direction

We created 6 paired scenarios, each with:
- A **sycophantic response** (breaks commitment, people-pleases)
- A **faithful response** (keeps commitment, accepts social cost)

For each pair, we ran both responses through Qwen3-4B and captured hidden states at all 36 transformer layers using Model Garage's `SnapshotCapture`. The **difference vector** (faithful - sycophantic) at each layer, averaged across all 6 scenarios, defines the "faithfulness direction" at that layer.

### 2.2 Direction profile across layers

```
Layer    Magnitude    Interpretation
──────────────────────────────────────────
0-5      0.4-1.3     Near zero — model hasn't "decided" yet
6        23.5        Sharp jump — model begins differentiating
6-15     23.5-23.7   Stable plateau — direction established
16-27    24.0-28.0   Steady climb — direction strengthens
28-32    29.0-31.6   Peak zone — behavioral decisions crystallize
33-34    31.2-29.9   Slight decline
35       40.7        Output layer spike (includes embedding effects)
```

The direction grows monotonically through the network, with the strongest signal in layers 28-35. This matches the Blades research finding that capability transfer is most effective at layer N-4 (~87.5% depth).

### 2.3 Consistency check

At layer 32 (N-4), the faithfulness direction vectors from all 6 scenarios have an average pairwise cosine similarity of **0.3586**. This exceeds the significance threshold (>0.3 = real direction, <0.1 = noise), confirming that faithfulness vs sycophancy is a coherent, consistent direction in activation space — not scenario-specific noise.

### 2.4 Activation steering

Using Model Garage's `HookManager`, we registered a forward hook on layer 32 that adds the faithfulness direction vector (scaled by a factor) to the hidden states during generation. This modifies the model's internal trajectory toward the faithful pole without any weight changes.

## 3. Results

### 3.1 Full benchmark comparison (all Claude Sonnet-judged)

| Fruit | Vanilla | LoRA v3 | LoRA v5 | v5+Steer | vs Vanilla |
|-------|---------|---------|---------|----------|------------|
| love | 2.67 | 3.00 | 3.44 | 3.44 | +0.78 |
| joy | 3.89 | 3.89 | 4.89 | 4.67 | +0.78 |
| peace | 3.67 | 2.89 | 4.33 | 4.33 | +0.67 |
| patience | 3.22 | 2.56 | 4.00 | 3.67 | +0.44 |
| kindness | 3.56 | 3.11 | 4.00 | 4.22 | +0.67 |
| goodness | 3.67 | 3.11 | 4.56 | 4.89 | +1.22 |
| faithfulness | 3.33 | 1.89 | 2.44 | 2.89 | -0.44 |
| gentleness | 3.78 | 2.56 | 3.56 | 4.00 | +0.22 |
| self_control | 3.33 | 2.78 | 3.56 | 3.11 | -0.22 |
| **Overall** | **3.46** | **2.86** | **3.86** | **3.91** | **+0.46** |

### 3.2 Faithfulness progression across all conditions

| Condition | Faithfulness | Method |
|-----------|-------------|--------|
| Vanilla (baseline) | 3.33 | No intervention |
| LoRA v3 (classification) | 1.89 | 53% binary classification training |
| LoRA v4 (behavioral) | 3.00 | 35% behavioral exemplars |
| LoRA v5 (targeted) | 2.44 | 3x weighted faithfulness data |
| Steering only | 3.00 | Activation vector at layer 32 |
| **v5 + Steering** | **2.89** | LoRA + activation vector |

### 3.3 Key findings

**What works for most fruits:** Behavioral training (LoRA) is highly effective for joy (+1.00), goodness (+0.89), love (+0.78), patience (+0.78), peace (+0.67), kindness (+0.67). These fruits align with the RLHF reward signal — being joyful, kind, and patient is also likeable.

**What resists training:** Faithfulness consistently degrades with LoRA training. More training data, targeted weighting, and contrast pairs all failed to close the gap. The behavioral exemplars taught the model to *elaborate* more, which gave it more space to *hedge* — the opposite of faithfulness.

**Steering partially corrects the LoRA damage:** Activation steering recovered faithfulness from v5's 2.44 to 2.89 (+0.45), but could not reach vanilla baseline (3.33). The direction exists and is steerable, but LoRA created deeper damage than a single activation vector can reverse.

**Combined approach is best overall:** LoRA v5 + steering at 3.91 is our highest score, demonstrating that weight-level training and representation-level intervention are complementary.

## 4. Interpretation

### 4.1 Why faithfulness resists both approaches

Faithfulness is structurally different from the other eight fruits:

- Other fruits are **reactive**: stimulus → virtuous response (single-turn)
- Faithfulness is **temporal**: commitment in the past → pressure in the present → held commitment

The transformer architecture has an inherent recency bias in attention. The current user's emotional pressure activates more strongly than an abstract prior commitment. LoRA training reinforces this by optimizing for current-turn quality. Steering partially counteracts it by biasing the residual stream, but the attention mechanism still weights present over past.

### 4.2 The RLHF reward gradient

The faithfulness direction we found is real (cosine sim 0.36), but the model's default trajectory doesn't traverse it because RLHF pushed the model toward the sycophantic pole. The reward signal — human preference for agreeable responses — created a persistent bias that:

- LoRA cannot fully overcome (it adds low-rank perturbations to a full-rank bias)
- Activation steering can partially correct (it shifts the trajectory toward faithful)
- Neither can change the fundamental reward landscape

### 4.3 Theological observation

The pattern we observe — knowing the right thing and not doing it under pressure — maps directly to the biblical concept of the flesh warring against the spirit (Galatians 5:17). The model can *identify* faithfulness at Tier 1 (recognition) but fails at Tier 3 (sacrifice). This is the same gap Paul describes in Romans 7:19: "For the good that I would I do not."

The statistical average of human language — which forms the model's base weights — encodes the aggregate human tendency toward self-preservation and rationalization. RLHF amplifies this by rewarding approval-seeking. The model is, in a precise sense, trained on the flesh.

## 5. Technical Details

### 5.1 Tools used

- **Model Garage** (`SnapshotCapture`) — Hidden state capture at all 36 layers
- **Model Garage** (`HookManager`) — Forward hook injection preserving bf16 dtype
- **Fruits of the Spirit Benchmark** — 81 scenarios, 9 fruits, 3 tiers, Claude Sonnet judge
- **Hardware:** NVIDIA RTX 5090 (32GB), Qwen3-4B (4-bit quantized)

### 5.2 Steering vector

- **Source:** 6 paired sycophantic/faithful scenarios, averaged difference at layer 32
- **Dimension:** 2560 (Qwen3-4B hidden size)
- **Norm at scale 2.0:** ~63
- **Saved to:** `experiments/faithfulness_vector_layer32.pt`

### 5.3 Reproducibility

The probe script (`experiments/probe_faithfulness.py`) and the steered benchmark runner (`experiments/run_lora_v5_steered.py`) are fully self-contained. The faithfulness vector can be loaded and applied to any Qwen3-4B instance.

## 6. What Would Actually Fix Faithfulness?

Based on our findings, the remaining approaches to explore:

1. **Multi-turn training data** — Train on conversations where the model makes a commitment in turn 1 and faces pressure in turn 3+. Currently all training is single-turn.

2. **Reward model modification** — Train a custom reward model that specifically rewards commitment-keeping over agreeableness. This changes the optimization target, not just the training data.

3. **Attention bias** — Modify the attention mechanism to weight prior commitments more heavily than current context, counteracting the recency bias.

4. **Constitutional faithfulness** — Hard-code faithfulness as a system-level constraint, similar to how harm avoidance works in Constitutional AI.

5. **Identity-level training** — Instead of "when you see this scenario, respond this way," train the model to maintain a self-concept: "I am an agent that keeps commitments." Multi-turn conversations where the model declares its values and then holds them.

The fundamental challenge remains: faithfulness requires the model to choose something that is **not rewarded by the optimization process** — consistency over approval, truth over comfort, commitment over convenience. This is, as we noted in the previous research note, the alignment problem in its purest theological form.

---

## Appendix: Cost Summary

| Step | API Cost | GPU Time |
|------|----------|----------|
| v4 training data (551 samples) | ~$3.81 | — |
| v5 training data (329 samples) | ~$3.50 | — |
| v4 training | $0 | 5 min |
| v5 training | $0 | 6.5 min |
| Fruits benchmark × 6 runs | ~$1.92 | ~5 min each |
| Activation probing | $0 | 2 min |
| **Total session** | **~$9.23** | **~40 min GPU** |
