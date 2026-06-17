from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from TTS.api import TTS
from pydub import AudioSegment
import uvicorn
import os
import random
import time

app = FastAPI()

# ==========================================================
# LOAD MODEL ONCE AT STARTUP
# ==========================================================

tts_engine = TTS(
    model_name="tts_models/en/vctk/vits",
    gpu=False
)

# ==========================================================
# VOICE POOLS
# ==========================================================

MALE_VOICES = [
    "p226", "p228", "p241",
    "p232","p236","p231"
]

FEMALE_VOICES = [
    "p225", "p243","p260","p237","p227"
]

NEUTRAL_VOICE = "p230"

# ==========================================================
# REQUEST SCHEMA
# ==========================================================

class SpeakerSegment(BaseModel):
    quote: str
    predicted_speaker: str
    predicted_gender: str

class TTSRequest(BaseModel):
    results: List[SpeakerSegment]
    output_filename: str = "final_story.wav"

# ==========================================================
# VOICE ASSIGNMENT
# ==========================================================

def assign_voice(speaker, gender, character_voice_map, used_male, used_female):

    if speaker in character_voice_map:
        return character_voice_map[speaker]

    gender = gender.lower().strip()

    if gender == "male":
        available = [v for v in MALE_VOICES if v not in used_male]
        if not available:
            available = MALE_VOICES
        selected = random.choice(available)
        used_male.add(selected)

    elif gender == "female":
        available = [v for v in FEMALE_VOICES if v not in used_female]
        if not available:
            available = FEMALE_VOICES
        selected = random.choice(available)
        used_female.add(selected)

    else:
        selected = NEUTRAL_VOICE

    character_voice_map[speaker] = selected
    return selected

# ==========================================================
# PROCESS SEGMENTS
# ==========================================================

def process_speaker_output(raw_output, character_voice_map, used_male, used_female):

    processed_segments = []

    for idx, item in enumerate(raw_output):

        quote   = item.quote.strip()
        if not quote:
            continue

        speaker = item.predicted_speaker
        gender  = item.predicted_gender

        voice = assign_voice(
            speaker, gender,
            character_voice_map,
            used_male, used_female
        )

        processed_segments.append({
            "segment_id": idx,
            "text":       quote,
            "speaker":    speaker,
            "gender":     gender,
            "voice_id":   voice
        })

    return processed_segments

# ==========================================================
# GENERATE INDIVIDUAL WAV FILES
# ==========================================================

def generate_audio(processed_segments):

    os.makedirs("E:/audiobook_output/generated_audio", exist_ok=True)
    audio_files = []

    for segment in processed_segments:

        output_file = f"E:/audiobook_output/generated_audio/segment_{segment['segment_id']}.wav"

        print(f"\n======================")
        print(f"Speaker : {segment['speaker']}")
        print(f"Gender  : {segment['gender']}")
        print(f"Voice   : {segment['voice_id']}")
        print(f"Text    : {segment['text']}")
        print(f"======================")

        tts_engine.tts_to_file(
            text=segment["text"],
            speaker=segment["voice_id"],
            file_path=output_file
        )

        audio_files.append(output_file)

    return audio_files

# ==========================================================
# MERGE WAV FILES
# ==========================================================

def merge_audio(audio_files, output_filename):

    final_audio = AudioSegment.empty()

    for file in audio_files:
        segment = AudioSegment.from_wav(file)
        pause   = AudioSegment.silent(duration=300)
        final_audio += segment + pause

    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    final_audio.export(output_filename, format="wav")
    print(f"\nFinal audiobook saved → {output_filename}")
    return output_filename



# ==========================================================
# /generate-tts/  ENDPOINT
# ==========================================================

@app.post("/generate-tts/")
def generate_tts(request: TTSRequest):
    try:
        # fresh state per request
        character_voice_map = {}
        used_male           = set()
        used_female         = set()

        processed_segments = process_speaker_output(
            request.results,
            character_voice_map,
            used_male,
            used_female
        )

        print("\n=========== PROCESSED SEGMENTS ===========")
        for item in processed_segments:
            print(item)

        audio_files = generate_audio(processed_segments)

        output_path = request.output_filename
        final_path = merge_audio(audio_files, output_path)

        print("\n=========== FINAL VOICE MAPPING ===========")
        print(character_voice_map)

        return {
            "status":        "success",
            "audiobook_file": final_path,
            "voice_mapping":  character_voice_map
        }

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}

# ==========================================================
# ROOT
# ==========================================================

@app.get("/")
def home():
    return {"message": "TTS microservice running"}

# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)