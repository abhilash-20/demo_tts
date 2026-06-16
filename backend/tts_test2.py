# from TTS.api import TTS
# from pydub import AudioSegment
# import os
# import random

# # ==========================================================
# # ---------------------- LOAD MODEL ------------------------
# # ==========================================================

# tts = TTS(
#     model_name="tts_models/en/vctk/vits",
#     gpu=False
# )

# # ==========================================================
# # ---------------------- VOICE POOLS -----------------------
# # ==========================================================

# MALE_VOICES = [
#     "p226",
#     "p228",
#     "p229",
#     "p232",
#     "p237",
#     "p241"
# ]

# FEMALE_VOICES = [
#     "p225",
#     "p227",
#     "p230",
#     "p233",
#     "p236",
#     "p243"
# ]

# NEUTRAL_VOICE = "p231"

# # ==========================================================
# # -------------- SPEAKER → VOICE ASSIGNMENT ---------------
# # ==========================================================

# character_voice_map = {}

# used_male = []
# used_female = []


# def assign_voice(
#     speaker,
#     gender,
#     character_voice_map
# ):

#     # already assigned before
#     if speaker in character_voice_map:
#         return character_voice_map[speaker]

#     # assign new voice
#     if gender.lower() == "male":

#         available = [
#             v for v in MALE_VOICES
#             if v not in used_male
#         ]

#         if len(available) == 0:
#             available = MALE_VOICES

#         selected_voice = random.choice(available)

#         used_male.append(selected_voice)

#     elif gender.lower() == "female":

#         available = [
#             v for v in FEMALE_VOICES
#             if v not in used_female
#         ]

#         if len(available) == 0:
#             available = FEMALE_VOICES

#         selected_voice = random.choice(available)

#         used_female.append(selected_voice)

#     else:
#         selected_voice = NEUTRAL_VOICE

#     character_voice_map[speaker] = selected_voice

#     return selected_voice

# # ==========================================================
# # -------- PROCESS EXACT SPEAKER ATTRIBUTION OUTPUT --------
# # ==========================================================

# def process_speaker_output(raw_output):

#     processed_segments = []

#     for idx, item in enumerate(raw_output):

#         quote = item.get("quote", "").strip()

#         # skip empty quotes
#         if quote == "":
#             continue

#         speaker = item.get(
#             "predicted_speaker",
#             "Unknown"
#         )

#         gender = item.get(
#             "predicted_gender",
#             "neutral"
#         )

#         # assign voice dynamically
#         assigned_voice = assign_voice(
#             speaker,
#             gender,
#             character_voice_map
#         )

#         processed_segments.append({

#             "segment_id": idx,

#             "text": quote,

#             "speaker": speaker,

#             "gender": gender,

#             "voice_id": assigned_voice
#         })

#     return processed_segments

# # ==========================================================
# # ---------------- GENERATE AUDIO FILES --------------------
# # ==========================================================

# def generate_audio(processed_segments):

#     os.makedirs(
#         "generated_audio",
#         exist_ok=True
#     )

#     audio_files = []

#     for segment in processed_segments:

#         output_file = (
#             f"generated_audio/"
#             f"segment_{segment['segment_id']}.wav"
#         )

#         print("\n======================")
#         print(f"Speaker : {segment['speaker']}")
#         print(f"Gender  : {segment['gender']}")
#         print(f"Voice   : {segment['voice_id']}")
#         print(f"Text    : {segment['text']}")
#         print("======================")

#         tts.tts_to_file(
#             text=segment["text"],
#             speaker=segment["voice_id"],
#             file_path=output_file
#         )

#         audio_files.append(output_file)

#     return audio_files

# # ==========================================================
# # --------------------- MERGE AUDIO ------------------------
# # ==========================================================

# def merge_audio(audio_files):

#     final_audio = AudioSegment.empty()

#     for file in audio_files:

#         segment = AudioSegment.from_wav(file)

#         pause = AudioSegment.silent(
#             duration=300
#         )

#         final_audio += segment + pause

#     final_audio.export(
#         "final_story.wav",
#         format="wav"
#     )

#     print("\nFinal audiobook generated!")

# # ==========================================================
# # -------- EXACT STRUCTURE FROM YOUR PIPELINE --------------
# # ==========================================================

# speaker_output = [

#     {
#         "quote":
#         "Mother, have you heard about our summer holidays yet?",

#         "predicted_speaker":
#         "Quentins",

#         "predicted_gender":
#         "male",

#         "scores":
#         [[0.0925]]
#     },

#     {
#         "quote":
#         "Can we go to Polseath as usual?",

#         "predicted_speaker":
#         "Julian",

#         "predicted_gender":
#         "male",

#         "scores":
#         [[0.0931]]
#     },

#     {
#         "quote":
#         "I feel sure we'll love it!",

#         "predicted_speaker":
#         "Anne",

#         "predicted_gender":
#         "female",

#         "scores":
#         [[0.1044]]
#     },

#     {
#         "quote":
#         "Well, your Aunt Fanny said that her Georgina would love a bit of company.",

#         "predicted_speaker":
#         "Daddy",

#         "predicted_gender":
#         "male",

#         "scores":
#         [[0.1011]]
#     },

#     {
#         "quote":
#         "It sounds exciting to me!",

#         "predicted_speaker":
#         "Mother",

#         "predicted_gender":
#         "female",

#         "scores":
#         [[0.0991]]
#     }

# ]

# # ==========================================================
# # ---------------------- PIPELINE --------------------------
# # ==========================================================

# processed_segments = process_speaker_output(
#     speaker_output
# )

# print("\nProcessed Segments:\n")

# for item in processed_segments:
#     print(item)

# audio_files = generate_audio(
#     processed_segments
# )

# merge_audio(audio_files)

# print("\nFinal Voice Mapping:")
# print(character_voice_map)
from TTS.api import TTS
from pydub import AudioSegment
import os
import random

# ==========================================================
# ---------------------- LOAD MODEL ------------------------
# ==========================================================

tts = TTS(
    model_name="tts_models/en/vctk/vits",
    gpu=False
)

# ==========================================================
# VERIFIED MALE VOICES
# ==========================================================

# ==========================================================
# VERIFIED MALE VOICES
# ==========================================================

MALE_VOICES = [
    "p226",   # male
    "p228",   # male
    "p241"    # male
]

# ==========================================================
# VERIFIED FEMALE VOICES
# ==========================================================

FEMALE_VOICES = [
    "p225",   # female
    "p243"    # female
]

# ==========================================================
# NEUTRAL VOICE
# ==========================================================

NEUTRAL_VOICE = "p230"

# ==========================================================
# -------------- SPEAKER → VOICE ASSIGNMENT ---------------
# ==========================================================

character_voice_map = {}

used_male = set()
used_female = set()


def assign_voice(
    speaker,
    gender,
    character_voice_map
):

    # ------------------------------------------------------
    # if speaker already assigned before
    # ------------------------------------------------------
    if speaker in character_voice_map:
        return character_voice_map[speaker]

    gender = gender.lower().strip()

    # ------------------------------------------------------
    # MALE SPEAKER
    # ------------------------------------------------------
    if gender == "male":

        available_voices = [
            voice
            for voice in MALE_VOICES
            if voice not in used_male
        ]

        # if all voices exhausted
        if len(available_voices) == 0:
            available_voices = MALE_VOICES

        selected_voice = random.choice(
            available_voices
        )

        used_male.add(selected_voice)

    # ------------------------------------------------------
    # FEMALE SPEAKER
    # ------------------------------------------------------
    elif gender == "female":

        available_voices = [
            voice
            for voice in FEMALE_VOICES
            if voice not in used_female
        ]

        # if all voices exhausted
        if len(available_voices) == 0:
            available_voices = FEMALE_VOICES

        selected_voice = random.choice(
            available_voices
        )

        used_female.add(selected_voice)

    # ------------------------------------------------------
    # NEUTRAL / UNKNOWN
    # ------------------------------------------------------
    else:

        selected_voice = NEUTRAL_VOICE

    # ------------------------------------------------------
    # SAVE SPEAKER -> VOICE MAP
    # ------------------------------------------------------
    character_voice_map[speaker] = selected_voice

    return selected_voice


# ==========================================================
# -------- PROCESS EXACT SPEAKER ATTRIBUTION OUTPUT --------
# ==========================================================

def process_speaker_output(raw_output):

    processed_segments = []

    for idx, item in enumerate(raw_output):

        quote = item.get(
            "quote",
            ""
        ).strip()

        # skip empty quotes
        if quote == "":
            continue

        speaker = item.get(
            "predicted_speaker",
            "Unknown"
        )

        gender = item.get(
            "predicted_gender",
            "neutral"
        )

        # --------------------------------------------------
        # ASSIGN VOICE USING PREDICTED GENDER
        # --------------------------------------------------
        assigned_voice = assign_voice(
            speaker=speaker,
            gender=gender,
            character_voice_map=character_voice_map
        )

        processed_segments.append({

            "segment_id": idx,

            "text": quote,

            "speaker": speaker,

            "gender": gender,

            "voice_id": assigned_voice
        })

    return processed_segments


# ==========================================================
# ---------------- GENERATE AUDIO FILES --------------------
# ==========================================================

def generate_audio(processed_segments):

    os.makedirs(
        "generated_audio",
        exist_ok=True
    )

    audio_files = []

    for segment in processed_segments:

        output_file = (
            f"generated_audio/"
            f"segment_{segment['segment_id']}.wav"
        )

        print("\n======================")
        print(f"Speaker : {segment['speaker']}")
        print(f"Gender  : {segment['gender']}")
        print(f"Voice   : {segment['voice_id']}")
        print(f"Text    : {segment['text']}")
        print("======================")

        tts.tts_to_file(
            text=segment["text"],
            speaker=segment["voice_id"],
            file_path=output_file
        )

        audio_files.append(output_file)

    return audio_files


# ==========================================================
# --------------------- MERGE AUDIO ------------------------
# ==========================================================

def merge_audio(audio_files):

    final_audio = AudioSegment.empty()

    for file in audio_files:

        segment = AudioSegment.from_wav(file)

        pause = AudioSegment.silent(
            duration=300
        )

        final_audio += segment + pause

    final_audio.export(
        "final_story4.wav",
        format="wav"
    )

    print("\nFinal audiobook generated!")


# ==========================================================
# -------- EXACT STRUCTURE FROM YOUR PIPELINE --------------
# ==========================================================

speaker_output = [

    {
        "quote":
        "Mother, have you heard about our summer holidays yet?",

        "predicted_speaker":
        "Quentins",

        "predicted_gender":
        "male",

        "scores":
        [[0.0925]]
    },

    {
        "quote":
        "Can we go to Polseath as usual?",

        "predicted_speaker":
        "Julian",

        "predicted_gender":
        "male",

        "scores":
        [[0.0931]]
    },

    {
        "quote":
        "I feel sure we'll love it!",

        "predicted_speaker":
        "Anne",

        "predicted_gender":
        "female",

        "scores":
        [[0.1044]]
    },

    {
        "quote":
        "Well, your Aunt Fanny said that her Georgina would love a bit of company.",

        "predicted_speaker":
        "Daddy",

        "predicted_gender":
        "male",

        "scores":
        [[0.1011]]
    },

    {
        "quote":
        "It sounds exciting to me!",

        "predicted_speaker":
        "Mother",

        "predicted_gender":
        "female",

        "scores":
        [[0.0991]]
    }

]

# ==========================================================
# ---------------------- PIPELINE --------------------------
# ==========================================================

processed_segments = process_speaker_output(
    speaker_output
)

print("\n=========== PROCESSED SEGMENTS ===========\n")

for item in processed_segments:
    print(item)

audio_files = generate_audio(
    processed_segments
)

merge_audio(audio_files)

print("\n=========== FINAL VOICE MAPPING ===========")
print(character_voice_map)