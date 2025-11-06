import torch, os, json
from transformers import GPT2Config, GPT2LMHeadModel, AutoTokenizer

# path of your original checkpoint
pt_path = "models/example_model_final_averaged.pt" # adjust as needed
save_dir = "models/example" # directory to save HF model
os.makedirs(save_dir, exist_ok=True)

print("🔧 Converting .pt checkpoint to Hugging Face format...")

# Build a minimal GPT‑style config (edit dims if known)
config = GPT2Config(
    vocab_size=50257,
    n_positions=1024,
    n_ctx=1024,
    n_embd=768,
    n_layer=12,
    n_head=12
)

# Initialize model and load checkpoint
model = GPT2LMHeadModel(config)
state = torch.load(pt_path, map_location="cpu")
model.load_state_dict(state, strict=False)
model.save_pretrained(save_dir)

# Save or create a tokenizer (fallback: GPT2 tokenizer)
tokenizer = AutoTokenizer.from_pretrained("gpt2")
tokenizer.save_pretrained(save_dir)

# Persist config for reproducibility
with open(os.path.join(save_dir, "config.json"), "w", encoding="utf-8") as f:
    json.dump(config.to_dict(), f, indent=2)

print(f"✅ Converted model saved at: {save_dir}")
