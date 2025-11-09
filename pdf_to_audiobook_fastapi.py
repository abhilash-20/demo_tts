from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from gtts import gTTS
from PyPDF2 import PdfReader
import tempfile
import os
import re
import time
import torch
import spacy
from transformers import pipeline as hf_pipeline

app = FastAPI()

# =====================================================
# 🔹 Load your fine-tuned DistilBERT NER model
# =====================================================
MODEL_DIR = "model"  # folder containing your unzipped wikiann-distilbert-ner
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForTokenClassification.from_pretrained(MODEL_DIR)

device = 0 if torch.cuda.is_available() else -1
ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer,
                        aggregation_strategy="simple", device=device)

# =====================================================
# 🔹 Load additional NER tools for ensemble
# =====================================================
print("🔹 Loading spaCy and Hugging Face models for ensemble...")
spacy_nlp = spacy.load("en_core_web_trf")

hf_ner = hf_pipeline("ner",
                     model="dslim/bert-base-NER",
                     aggregation_strategy="simple",
                     device=device)

print("✅ All models loaded successfully.")

# =====================================================
# 🔹 Helper: Clean input text
# =====================================================
def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())  # remove line breaks, extra spaces
    text = re.sub(r"[^A-Za-z0-9.,!?\"' ]+", "", text)  # remove unwanted symbols
    return text


# =====================================================
# 🔹 Individual extractors
# =====================================================
def extract_characters_trained(text: str):
    """Extract characters using your fine-tuned DistilBERT model."""
    results = ner_pipeline(text)
    names = {ent["word"].replace("##", "").strip()
             for ent in results
             if ent["entity_group"].upper() in ("PER", "PERSON")}
    if '"' in text and "Narrator" not in names:
        names.add("Narrator")
    return names


def extract_characters_spacy(text: str):
    """Extract characters using spaCy Transformer NER."""
    doc = spacy_nlp(text)
    names = {ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"}
    if '"' in text and "Narrator" not in names:
        names.add("Narrator")
    return names


def extract_characters_hf(text: str):
    """Extract characters using Hugging Face pretrained NER."""
    results = hf_ner(text)
    names = {ent["word"].strip()
             for ent in results
             if ent.get("entity_group", "").upper() in ("PER", "PERSON")}
    if '"' in text and "Narrator" not in names:
        names.add("Narrator")
    return names


# =====================================================
# 🔹 Ensemble extractor (union of all three)
# =====================================================
def ensemble_characters(text: str):
    """Combine results from trained model, spaCy, and Hugging Face NER."""
    a = extract_characters_trained(text)
    b = extract_characters_spacy(text)
    c = extract_characters_hf(text)

    combined = a.union(b).union(c)
    combined = {x for x in combined if len(x) > 2}

    # Merge substrings to remove duplicates (e.g., "Me" inside "Meera")
    final = []
    for cand in sorted(combined, key=len, reverse=True):
        if not any(cand in other for other in final):
            final.append(cand)

    # ✅ Enhanced Narrator Detection
    lower_text = text.lower()
    dialogue_quotes = text.count('"') + text.count("'")
    long_paragraphs = sum(1 for para in text.split("\n") if len(para) > 100)
    narrative_clues = any(
        phrase in lower_text
        for phrase in ["narrator", "she thought", "he thought", "reflected", "recalled"]
    )

    # Add narrator if story is narrative-heavy
    if (
        ("narrator" in lower_text)
        or (narrative_clues)
        or (dialogue_quotes < 6 and long_paragraphs > 2)
    ):
        if "Narrator" not in final:
            final.append("Narrator")

    # Post-process cleanup
    return clean_character_list(final)

def clean_character_list(characters):
    """Post-process raw detected entities into clean unique character names."""
    cleaned = set()
    for name in characters:
        name = name.strip()

        # Skip empty or too short
        if len(name) < 3:
            continue

        # Remove weird subword artifacts
        name = re.sub(r"##", "", name)
        name = re.sub(r"\s+", " ", name).strip()

        # Fix spacing around apostrophes (e.g., D ' Souza -> D'Souza)
        name = re.sub(r"\s*'\s*", "'", name)

        # Fix spacing after periods (e.g., . D -> D)
        name = re.sub(r"(^|\s)\.\s*", " ", name).strip()

        # Capitalize correctly while preserving apostrophes (e.g., D'Souza)
        name_parts = []
        for part in name.split():
            if "'" in part:
                sub = part.split("'")
                sub = [s.capitalize() for s in sub if s]
                name_parts.append("'".join(sub))
            else:
                name_parts.append(part.capitalize())
        name = " ".join(name_parts)

        # Remove if likely a title or not a person
        if re.match(r"^The\s+[A-Z]", name):  # e.g., "The Shadow Weaver"
            continue
        if any(w.lower() in {"pleaded", "said", "asked", "told", "replied"} for w in name.split()):
            continue

        # Remove obvious plurals
        name = re.sub(r"s$", "", name)

        cleaned.add(name)

    # Merge duplicates (case-insensitive)
    final = []
    for cand in sorted(cleaned, key=len, reverse=True):
        if not any(cand.lower() == other.lower() or cand.lower() in other.lower() for other in final):
            final.append(cand)

    return final
# =====================================================
# 🔹 /paste-text/ — Detect characters + generate audio
# =====================================================
@app.post("/paste-text/")
async def paste_text_endpoint(text: str = Form(...)):
    try:
        start_time = time.time()

        cleaned = clean_text(text)
        characters = ensemble_characters(cleaned)

        # Generate audiobook
        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)

        audio_filename = f"audiobook_{int(time.time())}.mp3"
        audio_path = os.path.join(output_dir, audio_filename)

        tts = gTTS(cleaned)
        tts.save(audio_path)

        gen_time = round(time.time() - start_time, 2)

        return JSONResponse({
            "characters_detected": characters,
            "text_length": len(cleaned),
            "audiobook_file": audio_path,
            "generation_time_seconds": gen_time,
            "message": "Audiobook generated successfully 🎧"
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# =====================================================
# 🔹 /upload-pdf/ — Process PDF & generate audiobook
# =====================================================
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile):
    try:
        start_time = time.time()

        # Save uploaded PDF temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Extract text from PDF
        extracted_text = ""
        with open(tmp_path, "rb") as pdf_file:
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                extracted_text += page.extract_text() or ""

        cleaned = clean_text(extracted_text)
        characters = ensemble_characters(cleaned)

        # Generate audiobook
        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)

        audio_filename = f"pdf_audiobook_{int(time.time())}.mp3"
        audio_path = os.path.join(output_dir, audio_filename)

        tts = gTTS(cleaned)
        tts.save(audio_path)

        gen_time = round(time.time() - start_time, 2)

        return JSONResponse({
            "characters_detected": characters,
            "text_length": len(cleaned),
            "audiobook_file": audio_path,
            "generation_time_seconds": gen_time,
            "message": "PDF processed successfully 🎧"
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# =====================================================
# 🔹 /download/ — Sample audio test endpoint
# =====================================================
@app.get("/download/")
async def download_file():
    output_dir = os.path.join(os.getcwd(), "output")
    sample_path = os.path.join(output_dir, "audiobook_sample.mp3")

    if not os.path.exists(sample_path):
        os.makedirs(output_dir, exist_ok=True)
        tts = gTTS("This is a sample audiobook file.")
        tts.save(sample_path)

    return FileResponse(sample_path, filename="audiobook_sample.mp3")


# =====================================================
# 🔹 Root route
# =====================================================
@app.get("/")
def home():
    return {"message": "AI Audiobook Generator (Ensemble NER) is running 🚀"}