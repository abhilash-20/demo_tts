# from allennlp.predictors.predictor import Predictor
# import allennlp_models.coref
# from pathlib import Path
# import os

# os.environ["TRANSFORMERS_OFFLINE"] = "1"

# _MODEL_PATH = Path(__file__).parent / "models/coref-spanbert-large-2021.03.10"

# coref_predictor = None

# def get_coref_predictor():
#     global coref_predictor
#     if coref_predictor is None:
#         coref_predictor = Predictor.from_path(str(_MODEL_PATH))
#     return coref_predictor


# # coref_predictor = None

# # def get_coref_predictor():
# #     global coref_predictor
# #     if coref_predictor is None:
# #         coref_predictor = Predictor.from_path(
# #             _MODEL_PATH
# #         )
# #     return coref_predictor

# MALE_PRONOUNS = {"he", "him", "his"}
# FEMALE_PRONOUNS = {"she", "her", "hers"}

# def pronoun_gender_score(text: str, character: str):
#     """
#     Determines gender based on pronouns linked via coreference.
#     """
#     predictor = get_coref_predictor()  # <-- ensure the predictor is loaded
#     result = predictor.predict(document=text)
#     tokens = result["document"]
#     clusters = result["clusters"]

#     male_count = 0
#     female_count = 0

#     for cluster in clusters:
#         mentions = [" ".join(tokens[s:e+1]) for s, e in cluster]
#         if any(character.lower() in m.lower() for m in mentions):
#             for m in mentions:
#                 word = m.lower()
#                 if word in MALE_PRONOUNS:
#                     male_count += 1
#                 elif word in FEMALE_PRONOUNS:
#                     female_count += 1

#     total = male_count + female_count
#     if total == 0:
#         return "unknown", 0.0

#     if male_count > female_count:
#         return "male", min(1.0, male_count / total)
#     else:
#         return "female", min(1.0, female_count / total)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------

from allennlp.predictors.predictor import Predictor
import allennlp_models.coref
from pathlib import Path
import os

os.environ["TRANSFORMERS_OFFLINE"] = "1"

_MODEL_PATH = Path(__file__).parent / "models/coref-spanbert-large-2021.03.10"

coref_predictor = None
character_memory = {}  # Stores character → {gender, voice, confidence}
implicit_counter = 1   # Counter for generic implicit characters

MALE_PRONOUNS = {"he", "him", "his"}
FEMALE_PRONOUNS = {"she", "her", "hers"}

def get_coref_predictor():
    global coref_predictor
    if coref_predictor is None:
        coref_predictor = Predictor.from_path(str(_MODEL_PATH))
    return coref_predictor


def is_character_mention(mention: str, character: str):
    """
    Check if a mention contains the character name exactly.
    """
    return any(token.lower() == character.lower() for token in mention.split())


def assign_gender_from_pronouns(mentions):
    """
    Count pronouns in a cluster to determine gender.
    """
    male_count, female_count = 0, 0
    for m in mentions:
        word = m.lower()
        if word in MALE_PRONOUNS:
            male_count += 1
        elif word in FEMALE_PRONOUNS:
            female_count += 1
    total = male_count + female_count
    if total == 0:
        return None, 0.0
    gender = "male" if male_count > female_count else "female"
    confidence = max(0.0, min(1.0, (male_count if gender=="male" else female_count) / total))
    return gender, confidence


def pronoun_gender_score(text: str, character: str = None):
    """
    Determine gender and assign voice, using:
    - Character name if present
    - Implicit gender clusters otherwise
    """
    global implicit_counter
    predictor = get_coref_predictor()
    result = predictor.predict(document=text)
    tokens = result["document"]
    clusters = result["clusters"]

    assigned_gender = "unknown"
    assigned_conf = 0.0
    assigned_voice = None

    for cluster in clusters:
        mentions = [" ".join(tokens[s:e+1]) for s, e in cluster]
        # Check if cluster contains the known character
        if character and any(is_character_mention(m, character) for m in mentions):
            gender, conf = assign_gender_from_pronouns(mentions)
            if gender:
                character_memory[character] = {
                    "character": character,
                    "gender": gender,
                    "voice": character_memory.get(character, {}).get("voice", f"{gender}_voice_{len(character_memory)+1}"),
                    "confidence": conf
                }
                assigned_name = character
                assigned_gender = gender
                assigned_conf = conf
                assigned_voice = character_memory[character]["voice"]
                break
        else:
            # Treat all pronoun clusters as implicit if no known character matched
            gender, conf = assign_gender_from_pronouns(mentions)
            if gender:
                implicit_name = f"__implicit_{gender}_{implicit_counter}__"
                character_memory[implicit_name] = {
                    "character": implicit_name,
                    "gender": gender,
                    "voice": f"{gender}_voice_{len(character_memory)+1}",
                    "confidence": conf
                }
                implicit_counter += 1
                assigned_name = implicit_name
                assigned_gender = gender
                assigned_conf = conf
                assigned_voice = character_memory[implicit_name]["voice"]

    return assigned_gender, assigned_conf





