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
char2id = {}
next_char_id = 0

def register_characters(characters):
    global char2id, next_char_id
    for name in characters:
        if name not in char2id:
            char2id[name] = next_char_id
            next_char_id += 1
    return char2id

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
# def extract_quotes(text):
#     pattern = r'["""\u2018\u2019](.*?)["""\u2018\u2019]'
#     quotes = []
#     for match in re.finditer(pattern, text):
#         quotes.append({
#             "quote": match.group(1),
#             "char_start": match.start(),
#             "char_end": match.end()
#         })
#     return quotes
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

# =====================================================
# DISTANCE FEATURES
# =====================================================
def compute_distance_features(text, quote_start, candidate_name):
    first_occurrence = text.find(candidate_name)
    if first_occurrence == -1:
        return [0.5, 0, 0, 0]
    relative_position = abs(first_occurrence - quote_start) / len(text)
    before = 1 if first_occurrence < quote_start else 0
    after = 1 if first_occurrence > quote_start else 0
    same_sentence = 0
    return [relative_position, same_sentence, before, after]

# =====================================================
# BUILD CANDIDATES WITH ALL FEATURES
# =====================================================
'''
def build_candidates_with_features(text, characters):
    register_characters(characters)
    quotes = extract_quotes(text)

    all_quote_candidates = []

    for q in quotes:
        candidates = []
        for name in characters:
            distance = compute_distance_features(
                text,
                q["char_start"],
                name
            )
            # candidates.append({
            #     "name": name,
            #     "char_id": char2id[name],        # ✅ candidate_char_ids
            #     "distance_features": distance,    # ✅ candidate_distance
            #     "mask": 1                         # ✅ candidate_mask
            # })

            mentions = find_candidate_mentions(text, name)

            if len(mentions) > 0:

                nearest_mention = min(
                    mentions,
                    key=lambda m: abs(m["char_start"] - q["char_start"])
                )

            else:

                nearest_mention = {
                    "char_start": 0,
                    "char_end": 1
                }

            candidates.append({

                "name": name,

                "mention_char_start":
                    nearest_mention["char_start"],

                "mention_char_end":
                    nearest_mention["char_end"],

                "distance_features": distance,

                "mask": 1
            })

        all_quote_candidates.append({
            "quote": q["quote"],
            "char_start": q["char_start"],
            "char_end": q["char_end"],
            "candidates": candidates
        })

    return all_quote_candidates
'''
def build_candidates_with_features(text, characters):
    register_characters(characters)
    quotes = extract_quotes(text)

    all_quote_candidates = []

    for q in quotes:
        candidates = []
        # for name in characters:
        #     distance = compute_distance_features(
        #         text,
        #         q["char_start"],
        #         name
        #     )
        #     # candidates.append({
        #     #     "name": name,
        #     #     "char_id": char2id[name],
        #     #     "distance_features": distance,
        #     #     "mask": 1
        #     # })
        #     mentions = find_candidate_mentions(text, name)

        #     if len(mentions) > 0:

        #         nearest_mention = min(
        #             mentions,
        #             key=lambda m: abs(m["char_start"] - q["char_start"])
        #         )

        #     else:

        #         nearest_mention = {
        #             "char_start": 0,
        #             "char_end": 1
        #         }

        #     candidates.append({

        #         "name": name,

        #         "mention_char_start":
        #             nearest_mention["char_start"],

        #         "mention_char_end":
        #             nearest_mention["char_end"],

        #         "distance_features": distance,

        #         "mask": 1
        #     })
        candidate_pool = []

        for name in characters:

            mentions = find_candidate_mentions(text, name)

            if len(mentions) > 0:

                nearest_mention = min(
                    mentions,
                    key=lambda m: abs(m["char_start"] - q["char_start"])
                )

                nearest_distance = abs(
                    nearest_mention["char_start"] - q["char_start"]
                )

                candidate_mask=1

            else:

                nearest_mention = {
                    "char_start": 0,
                    "char_end": 1
                }

                nearest_distance = 999999

                candidate_mask=0

            distance = compute_distance_features(
                text,
                q["char_start"],
                name
            )

            candidate_pool.append({

                "name": name,

                "mention_char_start":
                    nearest_mention["char_start"],

                "mention_char_end":
                    nearest_mention["char_end"],

                "distance_features": distance,

                "mask": candidate_mask,

                "nearest_distance": nearest_distance
            })

        # SORT nearest first
        candidate_pool.sort(
            key=lambda x: x["nearest_distance"]
        )

        # KEEP ONLY TOP 10
        candidates = candidate_pool[:10]

        while len(candidates) < 10:

            candidates.append({

                "name": "[PAD]",

                "mention_char_start": 0,

                "mention_char_end": 1,

                "distance_features": [999.0, 999.0, 999.0, 999.0],

                "mask": 0
            })

        # REMOVE helper field
        for c in candidates:
            c.pop("nearest_distance", None)

        real_count = sum(c["mask"] for c in candidates)

        print("REAL =", real_count)
        print("TOTAL =", len(candidates))

        # ✅ Add this
        print(f"\nQuote: {q['quote']}")
        for c in candidates:
            print(f"  Character: {c['name']} | distance: {c['distance_features']} | mask: {c['mask']}")
            

        all_quote_candidates.append({
            "quote": q["quote"],
            "char_start": q["char_start"],
            "char_end": q["char_end"],
            "candidates": candidates
        })

    return all_quote_candidates
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
def speaker_attribution_api_call(text, characters, profiles, quote_candidates):
    try:
        payload = {
            "text": text,
            "characters": characters,
            "gender_predictions": profiles,
            "quote_candidates": quote_candidates    # ✅ includes char_ids, distance, mask
        }
        headers = {"ngrok-skip-browser-warning": "69420"}
        response = requests.post(
            COLAB_API_URL,
            json=payload,
            headers=headers,
            timeout=None
        )
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
'''
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

    # ✅ Build quote candidates with char_ids, distance features and mask
    quote_candidates = build_candidates_with_features(text, characters)

    speakerData = speaker_attribution_api_call(
        uncleaned_text,
        characters,
        profiles,
        quote_candidates
    )

    return {
        "characters": characters,
        "profiles": profiles,
        "speaker_data": speakerData
    }
'''
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
    
   

    # ✅ Build quote candidates with char_ids, distance features and mask
    quote_candidates = build_candidates_with_features(uncleaned_text, characters)

    print("Characters detected:", characters)
    print("Profiles:", profiles)
    print("Quote candidates:", quote_candidates)

    speakerData = speaker_attribution_api_call(
        uncleaned_text,
        characters,
        profiles,
        quote_candidates
    )

    return {
        "characters": characters,
        "profiles": profiles,
        "speaker_data": speakerData
    }
# =====================================================
# /paste-text/
# =====================================================
@app.post("/paste-text/")
async def paste_text_endpoint(title: str = Form(...), text: str = Form(...)):
    try:
        start_time = time.time()
        cleaned = clean_text(text)
        analysis = extract_characters_with_gender(cleaned, text)

        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)
        audio_filename = f"audiobook_{int(time.time())}.mp3"
        audio_path = os.path.join(output_dir, audio_filename)
        tts = gTTS(cleaned)
        tts.save(audio_path)

        gen_time = round(time.time() - start_time, 2)

        return JSONResponse({
            "title": title,
            "characters_detected": analysis["characters"],
            "gender_profiles": analysis["profiles"],
            "speaker_attribution": analysis["speaker_data"],
            "audiobook_file": audio_path,
            "generation_time_seconds": gen_time,
            "message": "Analysis completed successfully"
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JSONResponse({"error": str(e)}, status_code=500)

# =====================================================
# /upload-pdf/
# =====================================================
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile, title: str = Form(...)):
    tmp_path = None
    start_time = time.time()
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        extracted_text = ""
        with open(tmp_path, "rb") as pdf_file:
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                extracted_text += page.extract_text() or ""

        if not extracted_text.strip():
            return JSONResponse({"error": "No text found in PDF"}, status_code=400)

        cleaned = clean_text(extracted_text)
        analysis = extract_characters_with_gender(cleaned, extracted_text)  # ✅ fixed

        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)
        audio_filename = f"pdf_audiobook_{int(time.time())}.mp3"
        audio_path = os.path.join(output_dir, audio_filename)
        tts = gTTS(cleaned)
        tts.save(audio_path)

        gen_time = round(time.time() - start_time, 2)

        return JSONResponse({
            "title": title,
            "characters_detected": analysis["characters"],
            "gender_profiles": analysis["profiles"],
            "speaker_attribution": analysis["speaker_data"],
            "audiobook_file": audio_path,
            "generation_time_seconds": gen_time,
            "message": "PDF processed successfully"
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
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