from allennlp.predictors.predictor import Predictor
import allennlp_models.coref
from pathlib import Path
import os

os.environ["TRANSFORMERS_OFFLINE"] = "1"

_MODEL_PATH = Path(__file__).parent / "models/coref-spanbert-large-2021.03.10"

coref_predictor = None

def get_coref_predictor():
    global coref_predictor
    if coref_predictor is None:
        coref_predictor = Predictor.from_path(str(_MODEL_PATH))
    return coref_predictor


# coref_predictor = None

# def get_coref_predictor():
#     global coref_predictor
#     if coref_predictor is None:
#         coref_predictor = Predictor.from_path(
#             _MODEL_PATH
#         )
#     return coref_predictor

MALE_PRONOUNS = {"he", "him", "his"}
FEMALE_PRONOUNS = {"she", "her", "hers"}

def pronoun_gender_score(text: str, character: str):
    """
    Determines gender based on pronouns linked via coreference.
    """
    predictor = get_coref_predictor()  # <-- ensure the predictor is loaded
    result = predictor.predict(document=text)
    tokens = result["document"]
    clusters = result["clusters"]

    male_count = 0
    female_count = 0

    for cluster in clusters:
        mentions = [" ".join(tokens[s:e+1]) for s, e in cluster]
        if any(character.lower() in m.lower() for m in mentions):
            for m in mentions:
                word = m.lower()
                if word in MALE_PRONOUNS:
                    male_count += 1
                elif word in FEMALE_PRONOUNS:
                    female_count += 1

    total = male_count + female_count
    if total == 0:
        return "unknown", 0.0

    if male_count > female_count:
        return "male", min(1.0, male_count / total)
    else:
        return "female", min(1.0, female_count / total)
