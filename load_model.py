from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import torch
import re

def merge_entities_with_subwords(entities, text):
    """Merge NER spans, handle subwords, and preserve punctuation."""
    merged = []
    if not entities:
        return merged

    # Sort entities by position
    entities = sorted(entities, key=lambda x: x["start"])
    current = entities[0].copy()

    for ent in entities[1:]:
        # Merge if same entity and close together
        if ent["entity_group"] == current["entity_group"] and ent["start"] <= current["end"] + 1:
            current["end"] = max(current["end"], ent["end"])
            current["score"] = (current["score"] + ent["score"]) / 2
        else:
            merged.append(current)
            current = ent.copy()

    merged.append(current)

    clean = []
    for ent in merged:
        # Extract exact text from input
        span_text = text[ent["start"]:ent["end"]].strip()

        # --- NEW FIX ---
        # If span starts with a lowercase letter and previous char was part of same word
        if ent["start"] > 0 and text[ent["start"] - 1].isalpha():
            # Extend one or two characters backward
            start_fix = ent["start"] - 2 if ent["start"] - 2 >= 0 else 0
            prefix = text[start_fix:ent["start"]]
            # Only add alphabetic prefix (e.g. "Ra")
            prefix = re.sub(r"[^A-Za-z]", "", prefix)
            span_text = prefix + span_text

        # Cleanup formatting
        span_text = re.sub(r"\s?##", "", span_text)
        span_text = re.sub(r"\s+", " ", span_text).strip()
        if span_text:
            span_text = span_text[0].upper() + span_text[1:]

        clean.append({
            "word": span_text,
            "entity": ent["entity_group"],
            "score": ent["score"]
        })

    return clean


# --- Main ---
model_dir = "model"

print("🔹 Loading model and tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_dir)
model = AutoModelForTokenClassification.from_pretrained(model_dir)

device = 0 if torch.cuda.is_available() else -1
print(f"✅ Using {'GPU' if device == 0 else 'CPU'}")

nlp = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple", device=device)

text = "There is one god in Christianity, Jesus Christ, one god in Islam, Allah and countless gods in Hinduisim."
print("\n🔹 Running inference...")
results = nlp(text)

print("\n🧩 Named Entities Detected:")
if not results:
    print("No named entities found.")
else:
    cleaned = merge_entities_with_subwords(results, text)
    for ent in cleaned:
        print(f"{ent['word']} → {ent['entity']} ({ent['score']:.2f})")