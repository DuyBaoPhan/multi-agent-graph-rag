"""
Router Training Script — Module A1.3
======================================
Fine-tune Qwen2.5-1.5B for intent classification using Unsloth & LoRA.
Target: Accuracy >= 92% on test set.
"""

import os
import torch
from loguru import logger
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments, AutoTokenizer
from unsloth import FastLanguageModel

# --- Configuration ---
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
DATA_PATH = "data/training/router/train_set.jsonl"
OUTPUT_DIR = "models/router-qwen-1.5b-lora"
MAX_SEQ_LENGTH = 512

def format_prompts(examples):
    """Format JSONL data into ChatML format for Qwen."""
    texts = []
    for text, intent in zip(examples["text"], examples["intent"]):
        prompt = f"<|im_start|>system\nPhân loại ý định người dùng vào một trong các nhóm: order, faq, consultant, chitchat. Trả về JSON: {{\"action\": \"intent\"}}<|im_end|>\n"
        prompt += f"<|im_start|>user\n{text}<|im_end|>\n"
        prompt += f"<|im_start|>assistant\n{{\"action\": \"{intent}\"}}<|im_end|>"
        texts.append(prompt)
    return {"text": texts}

def train():
    logger.info(f"Starting fine-tuning for {MODEL_NAME}...")

    # 1. Load Model & Tokenizer (4-bit quantization for efficiency)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=True,
    )

    # 2. Add LoRA adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
    )

    # 3. Load Dataset
    dataset = load_dataset("json", data_files=DATA_PATH, split="train")
    dataset = dataset.map(format_prompts, batched=True)

    # 4. Training Arguments
    args = TrainingArguments(
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=100,  # For demo, set to 100. For real training use num_train_epochs=3
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        output_dir=OUTPUT_DIR,
        save_strategy="steps",
        save_steps=50,
        report_to="none",
    )

    # 5. Initialize Trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        args=args,
    )

    # 6. Run Training
    trainer.train()
    
    # 7. Save model
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    logger.info(f"✅ Model saved to {OUTPUT_DIR}")

    # 8. Export to GGUF for Ultra-Low Latency (Module B2)
    logger.info("Exporting to GGUF (4-bit)...")
    model.save_pretrained_gguf(
        f"{OUTPUT_DIR}/gguf", 
        tokenizer, 
        quantization_method = "q4_k_m"
    )
    logger.info(f"🚀 GGUF model exported to {OUTPUT_DIR}/gguf. Ready for <100ms serving!")

if __name__ == "__main__":
    if not torch.cuda.is_available():
        logger.error("GPU not found. Please run on a machine with NVIDIA GPU.")
    else:
        train()
