"""Fine-tune Qwen2.5-Coder-7B-Instruct on Revit Family Engine data using Unsloth QLoRA."""

from __future__ import annotations

import os
os.environ["TORCHDYNAMO_DISABLE"] = "1"

import unsloth  # Must be imported first for optimizations
import json

from datasets import Dataset
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel

# ---------------------------------------------------------------------------
# Model -- Qwen2.5-Coder-7B fits comfortably on RTX 3090 (24GB)
# ---------------------------------------------------------------------------

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-Coder-7B-Instruct",
    max_seq_length=4096,
    load_in_4bit=True,
    dtype=None,  # auto-detect (bf16 on Ampere+)
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    use_gradient_checkpointing="unsloth",
)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

with open("/workspace/data/revit_training_data.json") as f:
    raw = json.load(f)

SYSTEM_PROMPT = (
    "You are an expert Revit family creation AI. Generate precise, compilable "
    "C# code using the Revit API for parametric family geometry, parameters, "
    "constraints, and type management.\n\n"
    "Rules:\n"
    "- Use Revit internal units: feet for length (mm / 304.8), radians for angles\n"
    "- Always wrap geometry creation in Transaction blocks\n"
    "- FamilyManager operations happen OUTSIDE Transaction blocks\n"
    "- Reference planes must exist before dimensions that reference them\n"
    "- Parameters must be assigned to types via famMgr.Set()\n"
    "- Use proper enum types (BuiltInParameterGroup, ParameterType)\n"
    "- Code must compile against Revit 2024+ API (.NET 8.0)\n"
    "- Namespace: Autodesk.Revit.DB, Autodesk.Revit.UI"
)


def format_sample(sample: dict) -> dict:
    instruction = sample["instruction"]
    if sample.get("input"):
        instruction += f"\n\n{sample['input']}"

    text = tokenizer.apply_chat_template(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": instruction},
            {"role": "assistant", "content": sample["output"]},
        ],
        tokenize=False,
        add_generation_prompt=False,
    )
    return {"text": text}


dataset = Dataset.from_list(raw).map(format_sample)
dataset = dataset.train_test_split(test_size=0.05, seed=42)

print(f"[OK] Train: {len(dataset['train'])} samples, Eval: {len(dataset['test'])} samples")

# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    dataset_text_field="text",
    max_seq_length=4096,
    packing=True,
    args=TrainingArguments(
        output_dir="/workspace/data/revit-lora-checkpoints",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        num_train_epochs=3,
        learning_rate=1e-4,
        lr_scheduler_type="cosine",
        warmup_steps=50,
        weight_decay=0.01,
        bf16=True,
        tf32=True,
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="epoch",
        save_total_limit=3,
        seed=42,
        report_to="none",
    ),
)

trainer.train()

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

# Save LoRA adapter (small, ~50MB)
model.save_pretrained("/workspace/data/revit-lora-adapter")
tokenizer.save_pretrained("/workspace/data/revit-lora-adapter")
print("[OK] LoRA adapter saved to /workspace/data/revit-lora-adapter")

# Save merged model as GGUF for Ollama (Q4_K_M quantization)
model.save_pretrained_gguf(
    "/workspace/data/revit-lora-gguf",
    tokenizer,
    quantization_method="q4_k_m",
)
print("[OK] GGUF model saved to /workspace/data/revit-lora-gguf")

print("\n[DONE] To create the Ollama model, run:")
print("  ollama create revit-family-7b-ft -f Modelfile.finetune")
