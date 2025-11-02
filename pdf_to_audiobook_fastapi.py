from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from transformers import pipeline
from gtts import gTTS
import spacy
import tempfile
import os
import re
import time
from PyPDF2 import PdfReader  # optional, used for text extraction

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

    speech_verbs = {"said", "asked", "replied", "told", "whispered", "laughed", "smiled", "cried", "shouted", "thought"}

    # Extract PERSON entities
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            candidates.add(ent.text.strip())

    # Extract probable speaker names near speech verbs
    for sent in doc.sents:
        if any(tok.lemma_.lower() in speech_verbs for tok in sent):
            for tok in sent:
                if tok.ent_type_ == "PERSON" or tok.pos_ == "PROPN":
                    candidates.add(tok.text.strip())

    # Remove generic or noisy terms
    bad_words = {"He", "She", "They", "We", "It", "Someone", "Anyone", "Man", "Woman", "Boy", "Girl"}
    candidates = {c for c in candidates if c not in bad_words and len(c) > 1}

    # Merge sub-parts of names (e.g., "Aarav" + "Aarav Mehta")
    merged = set()
    for cand in sorted(candidates, key=len, reverse=True):
        if not any(cand in m for m in merged):
            merged.add(cand)

    # Run zero-shot classification
    characters = []
    for cand in merged:
        try:
            phrase = f"{cand} is a person or character in a story."
            res = zero_shot(phrase, ["character", "object", "place", "abstract"])
            if res["labels"][0] == "character" and res["scores"][0] > 0.6:
                characters.append(cand)
        except Exception:
            continue

    # Add Narrator if dialogues exist
    if '"' in text and "Narrator" not in characters:
        characters.append("Narrator")

    return sorted(set(characters))


# ✅ Paste text endpoint — detects characters + generates audiobook
@app.post("/paste-text/")
async def paste_text_endpoint(text: str = Form(...)):
    try:
        start_time = time.time()

        cleaned = clean_text(text)
        characters = intelligent_character_extraction(cleaned)

        # Ensure output directory exists
        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)

        # Generate audiobook file
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
            "message": f"Audiobook saved successfully at {audio_path} 🎧"
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ✅ Upload PDF endpoint — same behavior
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile):
    try:
        start_time = time.time()

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
        characters = intelligent_character_extraction(cleaned)

        # Ensure output directory exists
        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)

        # Generate audiobook
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
            "message": f"PDF processed and audiobook saved successfully at {audio_path} 🎧"
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# Download endpoint
@app.get("/download/")
async def download_file():
    output_dir = os.path.join(os.getcwd(), "output")
    sample_path = os.path.join(output_dir, "audiobook_sample.mp3")
    if not os.path.exists(sample_path):
        os.makedirs(output_dir, exist_ok=True)
        tts = gTTS("This is a sample audiobook file.")
        tts.save(sample_path)
    return FileResponse(sample_path, filename="audiobook_sample.mp3")


@app.get("/")
def home():
    return {"message": "AI Audiobook Generator API is running 🚀"}
