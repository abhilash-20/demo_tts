"""
Simple Text → Audiobook FastAPI app (supports PDF upload or pasted text)
Features:
- Upload a PDF (will accept up to 5 pages by default)
- Paste text directly
- Uses pyttsx3 (offline) to synthesize to WAV file
- Measures and returns generation time and estimated audio duration

Notes / Dependencies:
- Python 3.8+
- pip install fastapi uvicorn pypdf2 pyttsx3 python-multipart pydub
- pydub + ffmpeg only needed if you want MP3 output. Install ffmpeg separately.
  On Ubuntu: sudo apt install ffmpeg

Run:
  uvicorn pdf_to_audiobook_fastapi:app --reload --port 8000

Endpoints:
- POST /upload-pdf  -> form field 'file' (multipart). Returns JSON with path to generated audio and timing.
- POST /paste-text  -> JSON {"text": "..."}. Returns JSON with path to generated audio and timing.

This is intentionally minimal and synchronous (simple for demo / testing). Adjust for production.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pypdf import PdfReader
import pyttsx3
import time
import os
import uuid
import math
from pydantic import BaseModel
from io import BytesIO

app = FastAPI(title="Text → Audiobook Demo")

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configuration
MAX_PDF_PAGES = 10               
WORDS_PER_PAGE_ESTIMATE = 500   
SPEECH_WPM = 150                

class PasteTextRequest(BaseModel):
    text: str


def extract_text_from_pdf_bytes(data: bytes, max_pages: int = MAX_PDF_PAGES) -> str:
    reader = PdfReader(BytesIO(data))
    num_pages = len(reader.pages)
    if num_pages == 0:
        return ""
    pages_to_use = min(num_pages, max_pages)
    texts = []
    for i in range(pages_to_use):
        page = reader.pages[i]
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        texts.append(page_text)
    return "\n\n".join(texts)


def estimate_audio_duration_seconds(text: str, wpm: int = SPEECH_WPM) -> float:
    words = len(text.split())
    minutes = words / wpm
    return minutes * 60.0


def synthesize_to_wav(text: str, filename_wav: str, rate: int = 180) -> None:
    """Use pyttsx3 to synchronously write WAV file. Blocking call."""
    engine = pyttsx3.init()
    
    engine.setProperty('rate', rate)  # words per minute (affects voice speed)
  
    engine.save_to_file(text, filename_wav)
    engine.runAndWait()
    engine.stop()


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    contents = await file.read()
    text = extract_text_from_pdf_bytes(contents)
    if not text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found in the PDF")

    
    reader = PdfReader(BytesIO(contents))
    actual_pages = len(reader.pages)
    pages_used = min(actual_pages, MAX_PDF_PAGES)

    
    truncated = actual_pages > MAX_PDF_PAGES

    # Time the synthesis
    file_id = str(uuid.uuid4())
    wav_path = os.path.join(OUTPUT_DIR, f"audiobook_{file_id}.wav")
    start = time.perf_counter()
    synthesize_to_wav(text, wav_path)
    end = time.perf_counter()

    gen_time = end - start
    est_duration = estimate_audio_duration_seconds(text)

    return {
        "status": "ok",
        "original_pdf_pages": actual_pages,
        "pages_used": pages_used,
        "truncated": truncated,
        "words": len(text.split()),
        "estimated_audio_duration_seconds": round(est_duration, 2),
        "generation_time_seconds": round(gen_time, 2),
        "audio_file": wav_path
    }


@app.post("/paste-text")
async def paste_text(payload: PasteTextRequest):
    text = payload.text or ""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Empty text provided")

    
    words = len(text.split())
    max_words = MAX_PDF_PAGES * WORDS_PER_PAGE_ESTIMATE
    if words > max_words:
        
        allowed_words = max_words
        split_words = text.split()
        text = " ".join(split_words[:allowed_words])
        truncated = True
    else:
        truncated = False

    file_id = str(uuid.uuid4())
    wav_path = os.path.join(OUTPUT_DIR, f"audiobook_{file_id}.wav")

    start = time.perf_counter()
    synthesize_to_wav(text, wav_path)
    end = time.perf_counter()

    gen_time = end - start
    est_duration = estimate_audio_duration_seconds(text)

    return {
        "status": "ok",
        "words": len(text.split()),
        "truncated": truncated,
        "estimated_audio_duration_seconds": round(est_duration, 2),
        "generation_time_seconds": round(gen_time, 2),
        "audio_file": wav_path
    }


@app.get("/download/{filename}")
def download_file(filename: str):
    local_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(local_path):
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(local_path, media_type='audio/wav', filename=filename)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
