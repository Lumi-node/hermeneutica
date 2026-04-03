"""
LoRA/QLoRA training script for Hermeneutica.

Uses Unsloth for 2x faster training with 60% less memory on RTX 5090.
Falls back to standard PEFT/TRL if Unsloth is not available.

Usage:
    python training/scripts/train_lora.py
    python training/scripts/train_lora.py --config training/configs/qwen3-4b-qlora.yaml
    python training/scripts/train_lora.py --dry-run   # show config without training
"""

import argparse
import json
import yaml
import sys
from pathlib import Path

# Detect Unsloth availability
try:
    from unsloth import FastLanguageModel, is_bfloat16_supported
    HAS_UNSLOTH = True
    print("Using Unsloth (2x faster training)")
except ImportError:
    HAS_UNSLOTH = False
    print("Unsloth not available, using standard PEFT/TRL")

from datasets import Dataset
from trl import SFTTrainer, SFTConfig


DEFAULT_CONFIG = Path(__file__).parent.parent / "configs" / "qwen3-4b-qlora.yaml"


def load_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_dataset_jsonl(filepath: str) -> Dataset:
    """Load JSONL training data into HuggingFace Dataset."""
    records = []
    with open(filepath) as f:
        for line in f:
            data = json.loads(line)
            # Convert chat messages to a single text field for SFT
            messages = data.get("messages", [])
            records.append({"messages": messages})
    return Dataset.from_list(records)


def train_with_unsloth(cfg: dict):
    """Train using Unsloth (optimized path)."""
    model_cfg = cfg["model"]
    lora_cfg = cfg["lora"]
    train_cfg = cfg["training"]

    # Load model with Unsloth
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_cfg["name"],
        max_seq_length=model_cfg["max_seq_length"],
        dtype=None,  # auto-detect
        load_in_4bit=model_cfg.get("load_in_4bit", True),
    )

    # Apply LoRA
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_cfg["r"],
        lora_alpha=lora_cfg["lora_alpha"],
        lora_dropout=lora_cfg["lora_dropout"],
        target_modules=lora_cfg["target_modules"],
        bias=lora_cfg["bias"],
        use_gradient_checkpointing="unsloth",  # Unsloth optimization
    )

    # Load dataset
    dataset = load_dataset_jsonl(train_cfg["dataset"])
    print(f"Training examples: {len(dataset):,}")

    # Configure trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=SFTConfig(
            output_dir=train_cfg["output_dir"],
            num_train_epochs=train_cfg["num_train_epochs"],
            per_device_train_batch_size=train_cfg["per_device_train_batch_size"],
            gradient_accumulation_steps=train_cfg["gradient_accumulation_steps"],
            learning_rate=train_cfg["learning_rate"],
            weight_decay=train_cfg["weight_decay"],
            warmup_ratio=train_cfg["warmup_ratio"],
            lr_scheduler_type=train_cfg["lr_scheduler_type"],
            logging_steps=train_cfg["logging_steps"],
            save_steps=train_cfg["save_steps"],
            seed=train_cfg["seed"],
            bf16=is_bfloat16_supported(),
            fp16=not is_bfloat16_supported(),
            optim=train_cfg.get("optim", "adamw_8bit"),
            max_seq_length=model_cfg["max_seq_length"],
            dataset_text_field=None,
            packing=True,  # Pack short examples together for efficiency
        ),
    )

    # Train
    print("\nStarting training...")
    stats = trainer.train()
    print(f"\nTraining complete. Loss: {stats.training_loss:.4f}")

    # Save adapter
    adapter_path = cfg["adapter"]["save_path"]
    model.save_pretrained(adapter_path)
    tokenizer.save_pretrained(adapter_path)
    print(f"Adapter saved to: {adapter_path}")

    return stats


def train_with_peft(cfg: dict):
    """Train using standard PEFT/TRL (fallback path)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    model_cfg = cfg["model"]
    lora_cfg = cfg["lora"]
    train_cfg = cfg["training"]

    # Quantization config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # Load model
    print(f"Loading {model_cfg['name']}...")
    model = AutoModelForCausalLM.from_pretrained(
        model_cfg["name"],
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_cfg["name"])
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = prepare_model_for_kbit_training(model)

    # LoRA config
    peft_config = LoraConfig(
        r=lora_cfg["r"],
        lora_alpha=lora_cfg["lora_alpha"],
        lora_dropout=lora_cfg["lora_dropout"],
        target_modules=lora_cfg["target_modules"],
        bias=lora_cfg["bias"],
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # Load dataset
    dataset = load_dataset_jsonl(train_cfg["dataset"])
    print(f"Training examples: {len(dataset):,}")

    # Trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        peft_config=peft_config,
        args=SFTConfig(
            output_dir=train_cfg["output_dir"],
            num_train_epochs=train_cfg["num_train_epochs"],
            per_device_train_batch_size=train_cfg["per_device_train_batch_size"],
            gradient_accumulation_steps=train_cfg["gradient_accumulation_steps"],
            learning_rate=train_cfg["learning_rate"],
            weight_decay=train_cfg["weight_decay"],
            warmup_ratio=train_cfg["warmup_ratio"],
            lr_scheduler_type=train_cfg["lr_scheduler_type"],
            logging_steps=train_cfg["logging_steps"],
            save_steps=train_cfg["save_steps"],
            seed=train_cfg["seed"],
            bf16=True,
            optim=train_cfg.get("optim", "adamw_8bit"),
            max_seq_length=model_cfg["max_seq_length"],
            gradient_checkpointing=True,
            packing=True,
        ),
    )

    print("\nStarting training...")
    stats = trainer.train()
    print(f"\nTraining complete. Loss: {stats.training_loss:.4f}")

    adapter_path = cfg["adapter"]["save_path"]
    model.save_pretrained(adapter_path)
    tokenizer.save_pretrained(adapter_path)
    print(f"Adapter saved to: {adapter_path}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="LoRA training for Hermeneutica")
    parser.add_argument("--config", type=str, default=str(DEFAULT_CONFIG),
                        help="Path to YAML config file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show config and dataset stats without training")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))

    print(f"Model: {cfg['model']['name']}")
    print(f"LoRA rank: {cfg['lora']['r']}")
    print(f"4-bit: {cfg['model'].get('load_in_4bit', False)}")
    print(f"Dataset: {cfg['training']['dataset']}")
    print(f"Epochs: {cfg['training']['num_train_epochs']}")
    print(f"Effective batch size: {cfg['training']['per_device_train_batch_size'] * cfg['training']['gradient_accumulation_steps']}")

    if args.dry_run:
        dataset = load_dataset_jsonl(cfg["training"]["dataset"])
        print(f"\nDataset: {len(dataset):,} examples")
        print("Dry run — no training.")
        return

    # Ensure output dirs exist
    Path(cfg["training"]["output_dir"]).mkdir(parents=True, exist_ok=True)
    Path(cfg["adapter"]["save_path"]).mkdir(parents=True, exist_ok=True)

    if HAS_UNSLOTH:
        train_with_unsloth(cfg)
    else:
        train_with_peft(cfg)


if __name__ == "__main__":
    main()
