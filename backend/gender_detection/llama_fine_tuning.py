from unsloth import FastLanguageModel
import torch
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset

# 1. Load Model (Optimized for 16GB VRAM)
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/llama-3-8b-bnb-4bit", # Pre-quantized version
    max_seq_length = 1024, # Keep this at 1024 or 512 to save memory
    load_in_4bit = True,
)

# 2. Add LoRA Adapters
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",],
    lora_alpha = 16,
    lora_dropout = 0, # Unsloth optimization: 0 is faster
    bias = "none",
    use_gradient_checkpointing = "unsloth", # Crucial for saving VRAM
)

# 3. Load Dataset
train_dataset = load_dataset("json", data_files="litbank_generative_train.jsonl", split="train")
val_dataset = load_dataset("json", data_files="litbank_generative_dev.jsonl", split="train")

def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    inputs       = examples["input"]
    outputs      = examples["output"]
    texts = []

    for instruction, input, output in zip(instructions, inputs, outputs):
        # Format the string exactly as you want the model to see it
        text = f"### Instruction:\n{instruction}\n\n### Input:\n{input}\n\n### Response:\n{output}{tokenizer.eos_token}"
        texts.append(text)

    # FIX: Return the list of strings directly, not a dictionary
    return texts

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = train_dataset,  # FIXED: Changed 'dataset' to 'train_dataset'
    eval_dataset = val_dataset,     # ADDED: This enables the validation logic
    formatting_func = formatting_prompts_func,
    max_seq_length = 1024,
    dataset_num_proc = 2,
    args = TrainingArguments(
        report_to = "none",
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        max_steps = 200,
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 1,
        output_dir = "outputs",
        optim = "adamw_8bit",
        save_steps=50,

        # Validation arguments
        eval_strategy = "steps",
        eval_steps = 10,
        per_device_eval_batch_size = 2,
        save_strategy = "steps",
        load_best_model_at_end = True,
        metric_for_best_model = "eval_loss", # Tells trainer what 'best' means
    ),
)

trainer.train(resume_from_checkpoint = "outputs/checkpoint-60")