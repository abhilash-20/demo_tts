from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from transformers import pipeline
import spacy
import tempfile
import os
import re
from collections import Counter

app = FastAPI()

# Load NLP tools
nlp = spacy.load("en_core_web_sm")
zero_shot = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Helper function to clean text
def clean_text(text):
    text = re.sub(r"\s+", " ", text.strip())  # remove line breaks
    text = re.sub(r"[^A-Za-z0-9.,!?\"' ]+", "", text)  # remove symbols
    return text

# Intelligent ML-based character detection
def intelligent_character_extraction(text):
    doc = nlp(text)
    candidates = set()

    # Extract named entities (persons or orgs) + subjects
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG"]:
            candidates.add(ent.text)
    for tok in doc:
        if tok.dep_ == "nsubj" and tok.pos_ in {"PROPN", "NOUN"}:
            candidates.add(tok.text)

    # Clean candidates
    candidates = {c.strip() for c in candidates if len(c.strip()) > 1}

    # Remove generic or common filler words
    common_words = {
        "Yes", "No", "Ok", "Hey", "Hello", "Hi", "Do", "So", "Go", "Please",
        "He", "She", "They", "We", "It", "Man", "Woman", "Boy", "Girl", "Someone"
    }
    candidates = {c for c in candidates if c not in common_words}

    # Classify each candidate using zero-shot classification
    characters = []
    for cand in candidates:
        try:
            res = zero_shot(cand, ["character", "object", "place", "abstract"])
            if res["labels"][0] == "character" and res["scores"][0] > 0.6:
                characters.append(cand)
        except Exception:
            continue

    # If dialogue exists, assume a narrator is present
    if '"' in text and "Narrator" not in characters:
        characters.append("Narrator")

    # Deduplicate and sort
    return sorted(set(characters))

# Endpoint: Paste text
@app.post("/paste-text/")
async def paste_text_endpoint(text: str = Form(...)):
    try:
        cleaned = clean_text(text)
        characters = intelligent_character_extraction(cleaned)
        return JSONResponse({"characters_detected": characters, "text_length": len(cleaned)})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# Endpoint: File upload
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Normally you'd extract text here (using PyPDF2 or pdfminer)
        extracted_text = "PDF parsing not implemented in this example."

        characters = intelligent_character_extraction(extracted_text)
        return JSONResponse({"characters_detected": characters})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# Endpoint: Download file
@app.get("/download/")
async def download_file():
    sample_path = "output_audio.mp3"
    if not os.path.exists(sample_path):
        with open(sample_path, "w") as f:
            f.write("This is a placeholder file.")
    return FileResponse(sample_path, filename="output_audio.mp3")

@app.get("/")
def home():
    return {"message": "AI Audiobook Generator API is running 🚀"}
