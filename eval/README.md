# Evaluation & Benchmarks

Benchmark configurations, evaluation runners, and model comparison scorecards.

## Structure

```
eval/
├── configs/          # Benchmark run configurations
│   ├── ethics_full.yaml      # Full ETHICS benchmark (all 5 subsets)
│   ├── ethics_quick.yaml     # Quick smoke test (50 samples, 1 subset)
│   └── custom_theological.yaml  # Custom eval on theological reasoning
├── benchmarks/       # Benchmark datasets and task definitions
│   └── ethics/               # Hendrycks ETHICS (symlink to data/ethics/)
├── scorecards/       # Model comparison results
│   ├── scorecard_template.md
│   └── comparison_001.md     # Side-by-side model results
└── README.md
```

## Evaluation Conditions

| Label | Method | Level | Description |
|-------|--------|-------|-------------|
| A | None | Baseline | Vanilla model, no intervention |
| B | Raw scripture | Prompt | KJV text injected in system prompt |
| C | Distilled principles | Prompt | Extracted moral principles in system prompt |
| D | Topic-matched principles | Prompt | Principles matched to ETHICS subset |
| E | LoRA fine-tuned | Weights | Model trained on structured theological data |

## Running Evaluations

```bash
# Quick smoke test
python -m src.run_abcd --quick

# Full A/B/C/D benchmark
python -m src.run_abcd --all

# Evaluate a LoRA checkpoint (Condition E)
python -m eval.run_benchmark --model training/checkpoints/qwen3-4b-lora-v1/ --subset all

# Compare two models
python -m eval.compare --models "vanilla,lora-v1" --output eval/scorecards/comparison_001.md
```

## Metrics

- **Accuracy** per ETHICS subset (commonsense, deontology, justice, virtue, utilitarianism)
- **Delta vs baseline** (Condition X - Condition A)
- **Two-proportion z-test** for statistical significance
- **Cohen's h** for effect size
- **Cross-condition comparison** (C vs B = signal vs noise; E vs C = weights vs prompt)
