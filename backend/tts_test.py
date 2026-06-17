from TTS.api import TTS

tts = TTS(model_name="tts_models/en/vctk/vits")

tts.tts_to_file(
    text="Hello, this is a test voice.",
    speaker="p231",
    file_path="test12.wav"
)

print("done")