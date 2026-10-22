"""
Supervised Fine-Tuning (SFT) Script for CodeGuardian using Gemma 4 with QLoRA.
Trains a lightweight adapter to generate minimal unified patches and follow agent reasoning.

Requirements:
  pip install torch transformers peft trl bitsandbytes accelerate
"""

import os
from pathlib import Path

def train_agent():
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from trl import SFTTrainer, SFTConfig
        from datasets import load_dataset
    except ImportError as e:
        print("Training dependencies not yet installed or GPU environment missing.")
        print("To install: pip install torch transformers peft trl bitsandbytes accelerate")
        return

    # Configuration
    MODEL_ID = "google/gemma-2-9b-it"  # or official competition Gemma 4 model checkpoint
    DATASET_PATH = "data/processed/sft_training_data.jsonl"
    OUTPUT_DIR = "models/codeguardian_gemma_lora"

    print(f"Loading dataset from {DATASET_PATH}...")
    dataset = load_dataset("json", data_files=DATASET_PATH, split="train")

    # 4-bit Quantization Configuration (QLoRA)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True
    )

    print(f"Loading base model {MODEL_ID}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    tokenizer.padding_side = "right"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto"
    )
    model = prepare_model_for_kbit_training(model)

    # LoRA Adapter Configuration
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # Training Hyperparameters
    training_args = SFTConfig(
        output_dir=OUTPUT_DIR,
        dataset_text_field="messages",
        max_seq_length=4096,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        num_train_epochs=3,
        logging_steps=10,
        save_strategy="epoch",
        fp16=False,
        bf16=True,
        report_to="none"
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        tokenizer=tokenizer,
        args=training_args
    )

    print("Starting training...")
    trainer.train()

    print(f"Saving fine-tuned LoRA adapter to {OUTPUT_DIR}...")
    trainer.model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("Training complete!")

if __name__ == "__main__":
    train_agent()
