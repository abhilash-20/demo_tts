┌──────────────────────────────────────────────────────────────┐
│                   Start FastAPI App                        │
│  File: pdf_to_audiobook_fastapi.py                           │
└──────────────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│ Create OUTPUT_DIR ("outputs") for storing generated audio     │
│ Define constants:                                             │
│  - MAX_PDF_PAGES = 10                                         │
│  - WORDS_PER_PAGE_ESTIMATE = 500                              │
│  - SPEECH_WPM = 150                                           │
└──────────────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│                Define Helper Functions                     │
├──────────────────────────────────────────────────────────────┤
│ extract_text_from_pdf_bytes()                                 │
│   → reads PDF bytes using PdfReader                           │
│   → extracts text up to MAX_PDF_PAGES                         │
│                                                               │
│ estimate_audio_duration_seconds()                             │
│   → estimates audio length based on words/WPM                 │
│                                                               │
│ synthesize_to_wav()                                           │
│   → uses pyttsx3 to convert text → speech (WAV file)          │
└──────────────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│                 Endpoint: /upload-pdf                      │
│  Method: POST, input: PDF file                                │
│                                                              │
│ 1️⃣ Validate file type (.pdf)                                 │
│ 2️⃣ Extract text using extract_text_from_pdf_bytes()           │
│ 3️⃣ Count pages, check if truncated                           │
│ 4️⃣ Generate unique filename (uuid)                           │
│ 5️⃣ Call synthesize_to_wav() to produce WAV                   │
│ 6️⃣ Measure generation time                                   │
│ 7️⃣ Estimate duration                                         │
│ 8️⃣ Return JSON →                                              │
│     { status, pages, truncated, words,                        │
│       est_duration, gen_time, audio_file }                    │
└──────────────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│                 Endpoint: /paste-text                      │
│  Method: POST, input: JSON {"text": "..."}                    │
│                                                              │
│ 1️⃣ Validate non-empty text                                   │
│ 2️⃣ Truncate if exceeds (MAX_PDF_PAGES × WORDS_PER_PAGE_EST)  │
│ 3️⃣ Generate unique filename (uuid)                           │
│ 4️⃣ Call synthesize_to_wav()                                  │
│ 5️⃣ Measure time + estimate duration                          │
│ 6️⃣ Return JSON (same structure as /upload-pdf)               │
└──────────────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│               Endpoint: /download/{filename}                │
│  Method: GET                                                  │
│                                                              │
│ 1️⃣ Check if file exists in outputs/                          │
│ 2️⃣ Return FileResponse(audio/wav)                            │
│ 3️⃣ Otherwise → raise 404                                     │
└──────────────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│               Supporting Modules Used                       │
│--------------------------------------------------------------│
│ fastapi          → Web framework for API creation             │
│ File, UploadFile → Handle uploaded files                      │
│ HTTPException    → Raise custom errors                        │
│ FileResponse     → Return downloadable files                  │
│ pypdf.PdfReader  → Extract text from PDFs                     │
│ pyttsx3          → Offline TTS engine                         │
│ time             → Measure performance                        │
│ os, uuid         → File management + unique naming            │
│ pydantic.BaseModel → Validate JSON body                       │
│ BytesIO          → Handle PDF in-memory                       │
└──────────────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│                     End of Flow                             │
│  Run with: uvicorn pdf_to_audiobook_fastapi:app --reload      │
└──────────────────────────────────────────────────────────────┘
