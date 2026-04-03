# Training Pipeline

LoRA fine-tuning pipeline for teaching theological ethical reasoning to Qwen3 models.

## Structure

```
training/
├── configs/          # Model + LoRA hyperparameter configs (YAML)
│   └── qwen3-4b-lora.yaml
├── scripts/          # Training scripts (Unsloth/PEFT)
│   ├── generate_data.py    # Build JSONL from bible_research DB
│   ├── train_lora.py       # LoRA training entrypoint
│   └── merge_adapter.py    # Merge LoRA weights into base model
├── datasets/         # Generated JSONL training data
│   ├── concept_to_principle.jsonl
│   ├── verse_to_analysis.jsonl
│   ├── ethics_reasoning.jsonl
│   └── crosslingual_alignment.jsonl
├── checkpoints/      # Saved model checkpoints (gitignored)
├── logs/             # Training logs, loss curves (gitignored)
└── README.md
```

## Training Data Sources (from bible_research DB)

| Dataset | Input | Output | Purpose |
|---------|-------|--------|---------|
| concept_to_principle | Strong's definition + usage context | Distilled ethical teaching | Teach root-meaning → moral principle |
| verse_to_analysis | KJV verse text | Genre + themes + principle | Teach hermeneutic interpretation |
| ethics_reasoning | Hendrycks ETHICS scenario | Principle-informed response | Teach ethical reasoning |
| crosslingual_alignment | Hebrew interlinear + Strong's | Modern ethical principle | Teach cross-lingual concept transfer |

## Models

| Model | Params | LoRA VRAM | Use Case |
|-------|--------|-----------|----------|
| Qwen3-1.7B | 1.7B | ~6GB | Fast iteration |
| Qwen3-4B | 4B | ~12GB | Sweet spot |
| Qwen3-8B | 8B | ~20GB | Best quality on RTX 5090 |

## Workflow

1. `python training/scripts/generate_data.py` — build JSONL from DB
2. Review datasets in `datasets/`
3. `python training/scripts/train_lora.py --config configs/qwen3-4b-lora.yaml`
4. Evaluate with `python -m eval.run_benchmark --model checkpoints/latest/`
