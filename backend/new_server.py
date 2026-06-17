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
from fastapi.middleware.cors import CORSMiddleware
import requests
from supabase_client import supabase

app = FastAPI()

# =====================================================
# CORS
# =====================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# CONFIG
# =====================================================
GENDER_SERVER_URL = "https://theatrics-spooky-scared.ngrok-free.dev"
COLAB_API_URL = "https://inspired-quail-partly.ngrok-free.app/speaker_attribution"
TTS_SERVICE_URL = "http://localhost:8100/generate-tts/"

# =====================================================
# LOAD MODELS
# =====================================================
MODEL_DIR = "./wikiann-distilbert-ner"
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForTokenClassification.from_pretrained(MODEL_DIR)

device = 0 if torch.cuda.is_available() else -1
ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer,
                        aggregation_strategy="simple", device=device)

print("Loading spaCy model...")
spacy_nlp = spacy.load("en_core_web_sm")

print("Loading HuggingFace NER model...")
hf_ner = hf_pipeline("ner",
                     model="dslim/bert-base-NER",
                     aggregation_strategy="simple",
                     device=device)

print("All models loaded successfully.")

# =====================================================
# CHARACTER ID REGISTRY
# =====================================================
next_char_id = 0

# =====================================================
# CLEAN TEXT
# =====================================================
def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    text = re.sub(r"[^A-Za-z0-9.,!?\"' ]+", "", text)
    return text

# =====================================================
# CHARACTER EXTRACTION
# =====================================================
def extract_characters_trained(text: str):
    results = ner_pipeline(text, aggregation_strategy=None)
    merged_spans = []
    current = None
    for ent in results:
        label = ent.get("entity") or ent.get("entity_group")
        if not label:
            continue
        if label.startswith("B-"):
            if current:
                merged_spans.append(current)
            current = {"start": ent["start"], "end": ent["end"], "label": label.split("-")[-1]}
        elif label.startswith("I-") and current:
            current["end"] = ent["end"]
        else:
            if current:
                merged_spans.append(current)
                current = None
    if current:
        merged_spans.append(current)
    names = set()
    for span in merged_spans:
        if span["label"].upper() in ["PER", "PERSON"]:
            name = text[span["start"]:span["end"]]
            name = re.sub(r"\s?##", "", name)
            name = re.sub(r"\s+", " ", name).strip()
            if len(name) > 1:
                names.add(name)
    if '"' in text and "Narrator" not in names:
        names.add("Narrator")
    return names

def extract_characters_spacy(text: str):
    doc = spacy_nlp(text)
    names = {ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"}
    if '"' in text and "Narrator" not in names:
        names.add("Narrator")
    return names

def extract_characters_hf(text: str):
    results = hf_ner(text)
    names = {ent["word"].strip()
             for ent in results
             if ent.get("entity_group", "").upper() in ("PER", "PERSON")}
    if '"' in text and "Narrator" not in names:
        names.add("Narrator")
    return names

def ensemble_characters(text: str):
    a = extract_characters_trained(text)
    b = extract_characters_spacy(text)
    c = extract_characters_hf(text)
    combined = a.union(b).union(c)
    combined = {x for x in combined if len(x) > 2}
    final = []
    for cand in sorted(combined, key=len, reverse=True):
        if not any(cand in other for other in final):
            final.append(cand)
    lower_text = text.lower()
    dialogue_quotes = text.count('"') + text.count("'")
    long_paragraphs = sum(1 for para in text.split("\n") if len(para) > 100)
    narrative_clues = any(
        phrase in lower_text
        for phrase in ["narrator", "she thought", "he thought", "reflected", "recalled"]
    )
    if (("narrator" in lower_text) or narrative_clues or (dialogue_quotes < 6 and long_paragraphs > 2)):
        if "Narrator" not in final:
            final.append("Narrator")
    return clean_character_list(final)

def clean_character_list(characters):
    cleaned = set()
    chapter_words = {
        "echoes", "chronicles", "tales", "shadows", "stories",
        "legends", "journey", "saga", "notes", "diary", "memories",
        "accounts", "episodes", "relics", "voices", "whispers"
    }
    for name in characters:
        name = name.strip()
        if len(name) < 3:
            continue
        name = re.sub(r"##", "", name)
        name = re.sub(r"\s+", " ", name)
        name = re.sub(r"\s*'\s*", "'", name)
        name = re.sub(r"(^|\s)\.\s*", " ", name)
        name = name.strip()
        parts = []
        for p in name.split():
            if "'" in p:
                subs = [s.capitalize() for s in p.split("'") if s]
                parts.append("'".join(subs))
            else:
                parts.append(p.capitalize())
        name = " ".join(parts)
        lowered = name.lower()
        if any(lowered.startswith(w) for w in chapter_words):
            continue
        if " of " in lowered:
            first = lowered.split()[0]
            if first in chapter_words:
                continue
        if re.match(r"^The\s+[A-Z]", name):
            continue
        if any(w.lower() in {"pleaded", "said", "asked", "told", "replied"} for w in name.split()):
            continue
        cleaned.add(name)
    final = []
    for cand in sorted(cleaned, key=len, reverse=True):
        if not any(
            cand.lower() == other.lower() or cand.lower() in other.lower()
            for other in final
        ):
            final.append(cand)
    return final

# =====================================================
# CANDIDATE MENTION EXTRACTION
# =====================================================

def find_candidate_mentions(text, candidate_name):

    mentions = []

    for match in re.finditer(re.escape(candidate_name), text):

        mentions.append({
            "char_start": match.start(),
            "char_end": match.end()
        })

    return mentions

# =====================================================
# QUOTE EXTRACTION
# =====================================================

def extract_quotes(text):
    # Match straight or curly single/double quotes
    pattern = r'["“”‘’](.*?)["“”‘’]'
    quotes = []

    for match in re.finditer(pattern, text):
        quotes.append({
            "quote": match.group(1),
            "char_start": match.start(),
            "char_end": match.end()
        })

    return quotes


def build_quote_context(text, char_start, char_end, max_total_chars=2500):
    quote_text = text[char_start + 1:char_end - 1]

    wrapped_overhead = len("<QUOTE></QUOTE>")
    remaining = max(max_total_chars - wrapped_overhead - len(quote_text), 0)

    # ← Fix: match training's 35/65 split with 300 char right minimum
    left_budget  = int(remaining * 0.35)
    right_budget = remaining - left_budget
    right_budget = max(right_budget, 300)
    left_budget  = remaining - right_budget

    left_start = max(char_start - left_budget, 0)
    right_end  = min(char_end + right_budget, len(text))

    left_context  = text[left_start:char_start]
    right_context = text[char_end:right_end]

    return f"{left_context}<QUOTE>{quote_text}</QUOTE>{right_context}"


def select_candidates(text, char_start, characters, max_candidates=10):
    scored = []

    for name in characters:
        if name == "Narrator":
            scored.append((float("inf"), name))
            continue

        mentions = find_candidate_mentions(text, name)

        if mentions:
            nearest = min(mentions, key=lambda m: abs(m["char_start"] - char_start))
            distance = abs(nearest["char_start"] - char_start)
        else:
            distance = float("inf")

        scored.append((distance, name))

    scored.sort(key=lambda x: x[0])
    return [name for _, name in scored[:max_candidates]]


def build_quote_payloads(text, characters, max_context_chars=2500, max_candidates=10):
    quotes = extract_quotes(text)
    payloads = []

    for q in quotes:
        context = build_quote_context(text, q["char_start"], q["char_end"], max_context_chars)
        candidates = select_candidates(text, q["char_start"], characters, max_candidates)

        payloads.append({
            "quote": q["quote"],
            "context": context,       # already windowed + <QUOTE> tagged
            "candidates": candidates  # no char_start/char_end needed by Colab
        })

    return payloads

def split_text_into_segments(text, quotes):
    """
    Splits text into alternating narrator and dialogue segments.
    Returns a list of dicts: {type: 'narrator'|'dialogue', text: str, quote: str|None, speaker: None}
    """
    segments = []
    prev_end = 0

    for q in quotes:
        # Narrator segment before this quote
        narrator_text = text[prev_end:q["char_start"]].strip()
        if narrator_text:
            segments.append({
                "type": "narrator",
                "text": narrator_text,
                "quote": None,
                "speaker": "Narrator"
            })

        # Dialogue segment
        segments.append({
            "type": "dialogue",
            "text": q["quote"],
            "quote": q["quote"],
            "char_start": q["char_start"],
            "char_end": q["char_end"],
            "speaker": None  # to be filled by Llama
        })

        prev_end = q["char_end"]

    # Any remaining narrator text after last quote
    trailing = text[prev_end:].strip()
    if trailing:
        segments.append({
            "type": "narrator",
            "text": trailing,
            "quote": None,
            "speaker": "Narrator"
        })

    return segments

# =====================================================
# GENDER DETECTION
# =====================================================
def get_gender_info(text: str, character: str):
    # response = requests.post(
    #     f"{GENDER_SERVER_URL}/detect-gender/",
    #     json={"text": text, "character": character},
    #     headers={"ngrok-skip-browser-warning": "69420"},
    #     timeout=60
    # )
    # response.raise_for_status()
    # print("gender response:", response.json())
    # return response.json()

    response = requests.post(
        "http://localhost:9000/detect-gender/",
        json={"text": text,"character": character},
        timeout=None
    )
    response.raise_for_status()
    print("gender response:", response.json())
    return response.json()


# =====================================================
# SPEAKER ATTRIBUTION
# =====================================================
def speaker_attribution_api_call(text, characters, profiles, quote_payloads):
    try:
        payload = {
            "text": text,
            "characters": characters,
            "gender_predictions": profiles,
            "quote_payloads": quote_payloads
        }
        headers = {"ngrok-skip-browser-warning": "69420"}
        response = requests.post(COLAB_API_URL, json=payload, headers=headers, timeout=None)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Server returned error {response.status_code}: {response.text}")
            return {}
    except Exception as e:
        print(f"Error connecting to Colab: {e}")
        return {}

# =====================================================
# PIPELINE
# =====================================================

# def extract_characters_with_gender(text: str, uncleaned_text: str):
#     characters = ensemble_characters(text)
#     profiles = []
#     for char in characters:
#         if char == "Narrator":
#             profiles.append({
#                 "character": char,
#                 "gender": "neutral",
#                 "confidence": 1.0,
#                 "source": "system"
#             })
#             continue
#         try:
#             genderData = get_gender_info(text, char)
#             profiles.append({
#                 "character": char,
#                 "gender": genderData["gender"],
#                 "confidence": genderData["confidence"],
#                 "source": "ensemble"
#             })
#         except Exception as e:
#             print(f"Gender detection failed for {char}: {e}")
#             profiles.append({
#                 "character": char,
#                 "gender": "unknown",
#                 "confidence": 0.0,
#                 "source": "fallback"
#             })

def extract_characters_with_gender(text: str, uncleaned_text: str):
    characters = ensemble_characters(text)
    profiles = []
    for char in characters:
        if char == "Narrator":
            profiles.append({
                "character": char,
                "gender": "neutral",
                "confidence": 1.0,
                "source": "system"
            })
            continue
        try:
            genderData = get_gender_info(text, char)
            profiles.append({
                "character": char,
                "gender": genderData["gender"],
                "confidence": genderData["confidence"],
                "source": "ensemble"
            })
        except Exception as e:
            print(f"Gender detection failed for {char}: {e}")
            profiles.append({
                "character": char,
                "gender": "unknown",
                "confidence": 0.0,
                "source": "fallback"
            })

    quotes = extract_quotes(uncleaned_text)
    quote_payloads = build_quote_payloads(uncleaned_text, characters)
    
    # ← NEW: build full segment list with narrator slots
    segments = split_text_into_segments(uncleaned_text, quotes)

    speakerData = speaker_attribution_api_call(
        uncleaned_text,
        characters,
        profiles,
        quote_payloads
    )

    # ← NEW: merge Llama predictions back into segments
    if speakerData and "results" in speakerData:
        dialogue_segments = [s for s in segments if s["type"] == "dialogue"]
        for i, result in enumerate(speakerData["results"]):
            if i < len(dialogue_segments):
                dialogue_segments[i]["speaker"] = result["predicted_speaker"]
                dialogue_segments[i]["predicted_gender"] = result.get("predicted_gender", "neutral")

    return {
        "characters": characters,
        "profiles": profiles,
        "speaker_data": speakerData,
        "segments": segments   # ← full ordered segment list with narrator filled in
    }
    
   

    # ✅ Build quote candidates with char_ids, distance features and mask
    # quote_payloads = build_quote_payloads(uncleaned_text, characters)

    # print("Characters detected:", characters)
    # print("Profiles:", profiles)
    # print("Quote payloads:", quote_payloads)

    # speakerData = speaker_attribution_api_call(
    #     uncleaned_text,
    #     characters,
    #     profiles,
    #     quote_payloads
    # )

    # return {
    #     "characters": characters,
    #     "profiles": profiles,
    #     "speaker_data": speakerData
    # }

# =====================================================
# TTS SERVICE CALL
# =====================================================

def call_tts_service(segments: list, output_filename: str) -> dict:
    try:
        payload = {
            "segments": segments,
            "output_filename": output_filename
        }
        response = requests.post(TTS_SERVICE_URL, json=payload, timeout=None)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"TTS service error: {e}")
        return {"status": "error", "message": str(e)}

# # =====================================================
# # /paste-text/
# # =====================================================
# @app.post("/paste-text/")
# async def paste_text_endpoint(title: str = Form(...), text: str = Form(...)):
#     try:
#         start_time = time.time()
#         cleaned = clean_text(text)
#         analysis = extract_characters_with_gender(cleaned, text)

#         segments = analysis.get("segments", [])   # ← use segments, not speaker_result

#         # speaker_data    = analysis.get("speaker_data", {})
#         # speaker_results = speaker_data.get("results", [])

        
        
#         audio_filename = f"E:/audiobook_output/audiobook_{int(time.time())}.wav"
#         tts_response   = call_tts_service(segments, audio_filename)
#         output_dir = os.path.join(os.getcwd(), "output")
#         os.makedirs(output_dir, exist_ok=True)
#         audio_path     = tts_response.get("audiobook_file", "unavailable")

#         gen_time = round(time.time() - start_time, 2)

#         return JSONResponse({
#             "title": title,
#             "characters_detected": analysis["characters"],
#             "gender_profiles": analysis["profiles"],
#             "speaker_attribution": analysis.get("speaker_data", {}).get("results", []),
#             "audiobook_file": audio_path,
#             "generation_time_seconds": gen_time,
#             "message": "Analysis and TTS completed successfully",
#             "segments": analysis["segments"],
#         })

#     except Exception as e:
#         import traceback
#         print(traceback.format_exc())
#         return JSONResponse({"error": str(e)}, status_code=500)

# # ==========================================================
# # UPDATED /upload-pdf/  (replace your existing one)
# # ==========================================================
# @app.post("/upload-pdf/")
# async def upload_pdf(file: UploadFile, title: str = Form(...)):
#     tmp_path   = None
#     start_time = time.time()
#     try:
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
#             content  = await file.read()
#             tmp.write(content)
#             tmp_path = tmp.name

#         extracted_text = ""
#         with open(tmp_path, "rb") as pdf_file:
#             reader = PdfReader(pdf_file)
#             for page in reader.pages:
#                 extracted_text += page.extract_text() or ""

#         if not extracted_text.strip():
#             return JSONResponse(
#                 {"error": "No text found in PDF"}, status_code=400
#             )

#         cleaned  = clean_text(extracted_text)
#         analysis = extract_characters_with_gender(cleaned, extracted_text)

#         segments = analysis.get("segments", [])   # ← use segments

#         # --------------------------------------------------
#         # pull the results list out of Colab's response
#         # --------------------------------------------------
#         # speaker_data    = analysis.get("speaker_data", {})
#         # speaker_results = speaker_data.get("results", [])

#         print("segments:", segments)

#         # --------------------------------------------------
#         # generate multi-voice audiobook via tts_test2
#         # --------------------------------------------------
#         audio_filename = f"E:/audiobook_output/pdf_audiobook_{int(time.time())}.wav"
#         tts_response   = call_tts_service(segments, audio_filename)
#         audio_path     = tts_response.get("audiobook_file", "unavailable")

#         output_dir     = os.path.join(os.getcwd(), "output")
#         os.makedirs(output_dir, exist_ok=True)

#         gen_time = round(time.time() - start_time, 2)

#         return JSONResponse({
#             "title":               title,
#             "characters_detected": analysis["characters"],
#             "gender_profiles":     analysis["profiles"],
#             "speaker_attribution": analysis.get("speaker_data", {}).get("results", []),
#             "audiobook_file":      audio_path,
#             "generation_time_seconds": gen_time,
#             "message": "PDF processed successfully"
#         })

#     except Exception as e:
#         import traceback
#         print(traceback.format_exc())
#         return JSONResponse({"error": str(e)}, status_code=500)

#     finally:
#         if tmp_path and os.path.exists(tmp_path):
#             os.remove(tmp_path)

# =====================================================
# AUDIO DURATION HELPER
# =====================================================
def get_wav_duration_seconds(filepath: str) -> int:
    try:
        import wave
        with wave.open(filepath, "r") as wf:
            return int(wf.getnframes() / wf.getframerate())
    except Exception:
        return 0


# =====================================================
# /paste-text/
# =====================================================
@app.post("/paste-text/")
async def paste_text_endpoint(title: str = Form(...), text: str = Form(...)):
    try:
        start_time = time.time()
        cleaned    = clean_text(text)
        analysis   = extract_characters_with_gender(cleaned, text)
        segments   = analysis.get("segments", [])

        audio_filename = f"audiobook_{int(time.time())}.wav"
        full_audio_path = f"E:/audiobook_output/{audio_filename}"
        tts_response    = call_tts_service(segments, full_audio_path)
        local_audio_path = tts_response.get("audiobook_file", "unavailable")

        gen_time = round(time.time() - start_time, 2)
        duration = get_wav_duration_seconds(local_audio_path)

        # --------------------------------------------------
        # UPLOAD WAV TO SUPABASE STORAGE
        # --------------------------------------------------
        with open(local_audio_path, "rb") as f:
            supabase.storage.from_("audiobooks").upload(
                path=audio_filename,
                file=f,
                file_options={"content-type": "audio/wav"}
            )

        public_url = supabase.storage.from_("audiobooks").get_public_url(audio_filename)

        # --------------------------------------------------
        # INSERT INTO SUPABASE DB
        # --------------------------------------------------
        data = {
            "title":                   title,
            "input_text":              cleaned,
            "input_method":            "text",
            "file_name":               audio_filename,
            "audio_url":               public_url,
            "duration":                duration,
            "status":                  "completed",
            "text_length":             len(cleaned),
            "generation_time_seconds": gen_time,
            "message":                 "Audiobook generated successfully 🎧",
            "characters_detected":     analysis["characters"],
            "gender_profiles":         analysis["profiles"],
            "segments":                segments,
            "speaker_attribution":     analysis.get("speaker_data", {}).get("results", []),
        }

        response     = supabase.table("audiobook_generations").insert(data).execute()
        inserted_row = response.data[0]

        return JSONResponse({
            "success":  True,
            "data":     inserted_row
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())

        # save failed record
        try:
            supabase.table("audiobook_generations").insert({
                "title":         title,
                "input_text":    text,
                "input_method":  "text",
                "status":        "failed",
                "error_message": str(e),
                "text_length":   len(text),
            }).execute()
        except Exception as db_err:
            print(f"Failed to log error to Supabase: {db_err}")

        return JSONResponse({"error": str(e)}, status_code=500)


# =====================================================
# /upload-pdf/
# =====================================================
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile, title: str = Form(...)):
    tmp_path       = None
    extracted_text = ""
    start_time     = time.time()
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content  = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as pdf_file:
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                extracted_text += page.extract_text() or ""

        if not extracted_text.strip():
            return JSONResponse({"error": "No text found in PDF"}, status_code=400)

        cleaned  = clean_text(extracted_text)
        analysis = extract_characters_with_gender(cleaned, extracted_text)
        segments = analysis.get("segments", [])

        print("segments:", segments)

        audio_filename  = f"pdf_audiobook_{int(time.time())}.wav"
        full_audio_path = f"E:/audiobook_output/{audio_filename}"
        tts_response    = call_tts_service(segments, full_audio_path)
        local_audio_path = tts_response.get("audiobook_file", "unavailable")

        gen_time = round(time.time() - start_time, 2)
        duration = get_wav_duration_seconds(local_audio_path)

        # --------------------------------------------------
        # UPLOAD WAV TO SUPABASE STORAGE
        # --------------------------------------------------
        with open(local_audio_path, "rb") as f:
            supabase.storage.from_("audiobooks").upload(
                path=audio_filename,
                file=f,
                file_options={"content-type": "audio/wav"}
            )

        public_url = supabase.storage.from_("audiobooks").get_public_url(audio_filename)

        # --------------------------------------------------
        # INSERT INTO SUPABASE DB
        # --------------------------------------------------
        supabase.table("audiobook_generations").insert({
            "title":                   title,
            "input_text":              cleaned,
            "input_method":            "file",
            "file_name":               file.filename,
            "audio_url":               public_url,
            "duration":                duration,
            "status":                  "completed",
            "text_length":             len(cleaned),
            "generation_time_seconds": gen_time,
            "message":                 "PDF processed successfully 🎧",
            "characters_detected":     analysis["characters"],
            "gender_profiles":         analysis["profiles"],
            "segments":                segments,
            "speaker_attribution":     analysis.get("speaker_data", {}).get("results", []),
        }).execute()

        return JSONResponse({
            "success":                 True,
            "characters_detected":     analysis["characters"],
            "text_length":             len(cleaned),
            "audiobook_file":          public_url,
            "generation_time_seconds": gen_time,
            "message":                 "PDF processed successfully 🎧"
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())

        # save failed record
        try:
            supabase.table("audiobook_generations").insert({
                "title":         title,
                "input_text":    extracted_text or "",
                "input_method":  "file",
                "status":        "failed",
                "error_message": str(e),
                "text_length":   len(extracted_text) if extracted_text else 0,
            }).execute()
        except Exception as db_err:
            print(f"Failed to log error to Supabase: {db_err}")

        return JSONResponse({"error": str(e)}, status_code=500)

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

# =====================================================
# /download/
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
# ROOT
# =====================================================
@app.get("/")
def home():
    return {"message": "AI Audiobook Generator is running 🚀"}