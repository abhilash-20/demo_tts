# from fastapi import FastAPI
# from pydantic import BaseModel
# from typing import List
# from TTS.api import TTS
# from pydub import AudioSegment
# import uvicorn
# import os
# import random
# import time

# app = FastAPI()

# # ==========================================================
# # LOAD MODEL ONCE AT STARTUP
# # ==========================================================

# tts_engine = TTS(
#     model_name="tts_models/en/vctk/vits",
#     gpu=False
# )

# # ==========================================================
# # VOICE POOLS
# # ==========================================================

# MALE_VOICES = [
#     "p226", "p228", "p241",
#     "p232","p236","p231"
# ]

# FEMALE_VOICES = [
#     "p225", "p243","p260","p237","p227"
# ]

# NARRATOR_VOICE = "p230"

# # ==========================================================
# # REQUEST SCHEMA
# # ==========================================================

# # class SpeakerSegment(BaseModel):
# #     quote: str
# #     predicted_speaker: str
# #     predicted_gender: str

# # class TTSRequest(BaseModel):
# #     results: List[SpeakerSegment]
# #     output_filename: str = "final_story.wav"

# class SpeakerSegment(BaseModel):
#     type: str                        # "narrator" or "dialogue"
#     text: str                        # the actual text to speak
#     speaker: str                     # "Narrator" or character name
#     predicted_gender: str = "neutral"

# class TTSRequest(BaseModel):
#     segments: List[SpeakerSegment]
#     output_filename: str = "final_story.wav"

# # ==========================================================
# # VOICE ASSIGNMENT
# # ==========================================================

# # def assign_voice(speaker, gender, character_voice_map, used_male, used_female):

# #     if speaker in character_voice_map:
# #         return character_voice_map[speaker]

# #     gender = gender.lower().strip()

# #     if gender == "male":
# #         available = [v for v in MALE_VOICES if v not in used_male]
# #         if not available:
# #             available = MALE_VOICES
# #         selected = random.choice(available)
# #         used_male.add(selected)

# #     elif gender == "female":
# #         available = [v for v in FEMALE_VOICES if v not in used_female]
# #         if not available:
# #             available = FEMALE_VOICES
# #         selected = random.choice(available)
# #         used_female.add(selected)

# #     else:
# #         selected = NEUTRAL_VOICE

# #     character_voice_map[speaker] = selected
# #     return selected

# def assign_voice(speaker, gender, character_voice_map, used_male, used_female):

#     # Narrator always gets a fixed dedicated voice
#     if speaker == "Narrator":
#         return NARRATOR_VOICE

#     if speaker in character_voice_map:
#         return character_voice_map[speaker]

#     gender = gender.lower().strip()

#     if gender == "male":
#         available = [v for v in MALE_VOICES if v not in used_male]
#         if not available:
#             available = MALE_VOICES
#         selected = random.choice(available)
#         used_male.add(selected)

#     elif gender == "female":
#         available = [v for v in FEMALE_VOICES if v not in used_female]
#         if not available:
#             available = FEMALE_VOICES
#         selected = random.choice(available)
#         used_female.add(selected)

#     else:
#         selected = NEUTRAL_VOICE

#     character_voice_map[speaker] = selected
#     return selected

# # ==========================================================
# # PROCESS SEGMENTS
# # ==========================================================

# def process_speaker_output(raw_output, character_voice_map, used_male, used_female):

#     processed_segments = []

#     for idx, item in enumerate(raw_output):

#         text = item.text.strip()
#         if not text:
#             continue

#         speaker = item.speaker
#         gender  = item.predicted_gender

#         voice = assign_voice(
#             speaker, gender,
#             character_voice_map,
#             used_male, used_female
#         )

#         processed_segments.append({
#             "segment_id": idx,
#             "text":       text,
#             "speaker":    speaker,
#             "gender":     gender,
#             "voice_id":   voice,
#             "type":       item.type
#         })

#     return processed_segments

# # ==========================================================
# # GENERATE INDIVIDUAL WAV FILES
# # ==========================================================

# def generate_audio(processed_segments):

#     os.makedirs("E:/audiobook_output/generated_audio", exist_ok=True)
#     audio_files = []

#     for segment in processed_segments:

#         output_file = f"E:/audiobook_output/generated_audio/segment_{segment['segment_id']}.wav"

#         print(f"\n======================")
#         print(f"Speaker : {segment['speaker']}")
#         print(f"Gender  : {segment['gender']}")
#         print(f"Voice   : {segment['voice_id']}")
#         print(f"Text    : {segment['text']}")
#         print(f"======================")

#         tts_engine.tts_to_file(
#             text=segment["text"],
#             speaker=segment["voice_id"],
#             file_path=output_file
#         )

#         audio_files.append(output_file)

#     return audio_files

# # ==========================================================
# # MERGE WAV FILES
# # ==========================================================

# def merge_audio(audio_files, output_filename):

#     final_audio = AudioSegment.empty()

#     for file in audio_files:
#         segment = AudioSegment.from_wav(file)
#         pause   = AudioSegment.silent(duration=300)
#         final_audio += segment + pause

#     os.makedirs(os.path.dirname(output_filename), exist_ok=True)
#     final_audio.export(output_filename, format="wav")
#     print(f"\nFinal audiobook saved → {output_filename}")
#     return output_filename



# # ==========================================================
# # /generate-tts/  ENDPOINT
# # ==========================================================

# @app.post("/generate-tts/")
# def generate_tts(request: TTSRequest):
#     try:
#         # fresh state per request
#         character_voice_map = {}
#         used_male           = set()
#         used_female         = set()

#         processed_segments = process_speaker_output(
#             request.segments,
#             character_voice_map,
#             used_male,
#             used_female
#         )

#         print("\n=========== PROCESSED SEGMENTS ===========")
#         for item in processed_segments:
#             print(item)

#         audio_files = generate_audio(processed_segments)

#         output_path = request.output_filename
#         final_path = merge_audio(audio_files, output_path)

#         print("\n=========== FINAL VOICE MAPPING ===========")
#         print(character_voice_map)

#         return {
#             "status":        "success",
#             "audiobook_file": final_path,
#             "voice_mapping":  character_voice_map
#         }

#     except Exception as e:
#         import traceback
#         print(traceback.format_exc())
#         return {"status": "error", "message": str(e)}

# # ==========================================================
# # ROOT
# # ==========================================================

# @app.get("/")
# def home():
#     return {"message": "TTS microservice running"}

# # ==========================================================
# # MAIN
# # ==========================================================

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8100)
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from TTS.api import TTS
from pydub import AudioSegment
import uvicorn
import os
import random

app = FastAPI()

# ==========================================================
# LOAD MODEL ONCE AT STARTUP
# ==========================================================

tts_engine = TTS(
    model_name="tts_models/en/vctk/vits",
    gpu=False
)

# ==========================================================
# VOICE POOLS  (4 buckets + narrator)
# ==========================================================

MALE_YOUNG_VOICES   = ["p231", "p226", "p251", "p269","p257"]
MALE_OLD_VOICES     = ["p228", "p229", "p232", "p262"]

FEMALE_YOUNG_VOICES = ["p225", "p227", "p243", "p244", "p260","p276"]
FEMALE_OLD_VOICES   = ["p261"]

NARRATOR_VOICE      = "p230"

# ==========================================================
# AGE KEYWORDS  →  "old" bucket trigger
# ==========================================================

OLD_KEYWORDS = {
    # male
    "grandfather", "grandpa", "granddad", "grandad",
    "old man", "elderly man", "aged man","father", "dad", "daddy", "papa",
    "elder", "senior", "ancient", "wizard",
    # female
    "grandmother", "grandma", "granny", "gran",
    "old woman", "old lady", "elderly woman", "aged woman",
    # gender-neutral
    "old", "elderly", "aged", "ancient", "sage",
}

def is_old_speaker(speaker: str) -> bool:
    """
    Returns True if speaker name/label contains any age keyword.
    Checks both single-word and multi-word keywords.
    """
    speaker_lower = speaker.lower()
    for keyword in OLD_KEYWORDS:
        if keyword in speaker_lower:
            return True
    return False

# ==========================================================
# VOICE ASSIGNMENT
# ==========================================================

def assign_voice(
    speaker: str,
    gender: str,
    character_voice_map: dict,
    used_male_young: set,
    used_male_old: set,
    used_female_young: set,
    used_female_old: set,
) -> str:

    # ----------------------------------------------------------
    # Narrator always gets dedicated fixed voice
    # ----------------------------------------------------------
    if speaker == "Narrator":
        return NARRATOR_VOICE

    # ----------------------------------------------------------
    # Already assigned in this session → reuse
    # ----------------------------------------------------------
    if speaker in character_voice_map:
        return character_voice_map[speaker]

    gender     = gender.lower().strip()
    use_old    = is_old_speaker(speaker)

    # ----------------------------------------------------------
    # Pick bucket based on gender + age
    # ----------------------------------------------------------
    if gender == "male":
        if use_old:
            pool      = MALE_OLD_VOICES
            used_pool = used_male_old
        else:
            pool      = MALE_YOUNG_VOICES
            used_pool = used_male_young

    elif gender == "female":
        if use_old:
            pool      = FEMALE_OLD_VOICES
            used_pool = used_female_old
        else:
            pool      = FEMALE_YOUNG_VOICES
            used_pool = used_female_young

    else:
        # neutral / unknown → default to young male pool
        pool      = MALE_YOUNG_VOICES
        used_pool = used_male_young

    # ----------------------------------------------------------
    # Pick unused voice from pool; reset if exhausted
    # ----------------------------------------------------------
    available = [v for v in pool if v not in used_pool]
    if not available:
        available = pool          # reset — allow reuse
        used_pool.clear()

    selected = random.choice(available)
    used_pool.add(selected)

    character_voice_map[speaker] = selected
    return selected

# ==========================================================
# REQUEST SCHEMA
# ==========================================================

class SpeakerSegment(BaseModel):
    type:             str              # "narrator" or "dialogue"
    text:             str              # text to speak
    speaker:          str              # "Narrator" or character name
    predicted_gender: str = "neutral"

class TTSRequest(BaseModel):
    segments:        List[SpeakerSegment]
    output_filename: str = "final_story.wav"

# ==========================================================
# PROCESS SEGMENTS
# ==========================================================

def process_speaker_output(
    raw_output:          List[SpeakerSegment],
    character_voice_map: dict,
    used_male_young:     set,
    used_male_old:       set,
    used_female_young:   set,
    used_female_old:     set,
) -> list:

    processed_segments = []

    for idx, item in enumerate(raw_output):

        text = item.text.strip()
        if not text:
            continue

        speaker = item.speaker
        gender  = item.predicted_gender

        voice = assign_voice(
            speaker, gender,
            character_voice_map,
            used_male_young,
            used_male_old,
            used_female_young,
            used_female_old,
        )

        age_label = "old" if is_old_speaker(speaker) else "young"

        processed_segments.append({
            "segment_id": idx,
            "text":       text,
            "speaker":    speaker,
            "gender":     gender,
            "age":        age_label,
            "voice_id":   voice,
            "type":       item.type,
        })

    return processed_segments

# ==========================================================
# GENERATE INDIVIDUAL WAV FILES
# ==========================================================

def generate_audio(processed_segments: list) -> list:

    os.makedirs("E:/audiobook_output/generated_audio", exist_ok=True)
    audio_files = []

    for segment in processed_segments:

        output_file = (
            f"E:/audiobook_output/generated_audio/"
            f"segment_{segment['segment_id']}.wav"
        )

        print(f"\n======================")
        print(f"Speaker : {segment['speaker']}")
        print(f"Gender  : {segment['gender']}")
        print(f"Age     : {segment['age']}")
        print(f"Voice   : {segment['voice_id']}")
        print(f"Text    : {segment['text']}")
        print(f"======================")

        tts_engine.tts_to_file(
            text=segment["text"],
            speaker=segment["voice_id"],
            file_path=output_file,
        )

        audio_files.append(output_file)

    return audio_files

# ==========================================================
# MERGE WAV FILES
# ==========================================================

def merge_audio(audio_files: list, output_filename: str) -> str:

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
        used_male_young     = set()
        used_male_old       = set()
        used_female_young   = set()
        used_female_old     = set()

        processed_segments = process_speaker_output(
            request.segments,
            character_voice_map,
            used_male_young,
            used_male_old,
            used_female_young,
            used_female_old,
        )

        print("\n=========== PROCESSED SEGMENTS ===========")
        for item in processed_segments:
            print(item)

        audio_files = generate_audio(processed_segments)
        final_path  = merge_audio(audio_files, request.output_filename)

        print("\n=========== FINAL VOICE MAPPING ===========")
        print(character_voice_map)

        return {
            "status":         "success",
            "audiobook_file": final_path,
            "voice_mapping":  character_voice_map,
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