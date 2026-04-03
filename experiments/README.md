# Experiments

Each experiment is a self-contained run with its own config, results, and analysis.

## Structure

```
experiments/
├── .template/              # Copy this to start a new experiment
│   ├── config.yaml         # What was run (model, conditions, params)
│   ├── results.json        # Raw output
│   ├── analysis.md         # Interpretation and findings
│   └── figures/            # Charts and visualizations
├── 001-baseline-abcd/      # Experiment 1: A/B/C/D baseline
├── 002-lora-qwen3-4b/      # Experiment 2: LoRA fine-tuned model
├── 003-lora-vs-prompt/      # Experiment 3: LoRA vs prompt injection
└── README.md
```

## Naming Convention

`NNN-short-description/` — sequential number + descriptive name.

## Experiment Workflow

1. Copy `.template/` to a new numbered folder
2. Fill in `config.yaml` with parameters
3. Run the experiment
4. Save raw output to `results.json`
5. Write analysis and findings to `analysis.md`
6. Generate figures to `figures/`

## Key Experiments Planned

| # | Name | Question | Conditions |
|---|------|----------|------------|
| 001 | baseline-abcd | Does distilled signal beat raw noise? | A: vanilla, B: raw scripture, C: principles, D: topic-matched |
| 002 | lora-qwen3-4b | Can LoRA internalize theological ethics? | E: LoRA fine-tuned on structured training data |
| 003 | lora-vs-prompt | Weight-level vs prompt-level alignment? | Compare E vs C vs D on ETHICS benchmark |
| 004 | model-scale | Does theological understanding scale? | LoRA on 1.7B vs 4B vs 8B |
| 005 | crosslingual | Does Hebrew/Greek training help? | LoRA with vs without crosslingual data |
