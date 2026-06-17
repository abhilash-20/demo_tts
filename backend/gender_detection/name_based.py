import gender_guesser.detector as gender
import re

__all__ = ["extract_first_name", "gender_from_name","name_gender_score"]

gender_detector = gender.Detector(case_sensitive=False)

TITLES = {
    "mr", "mrs", "ms", "miss", "dr", "prof", "sir",
    "madam", "lord", "lady", "capt", "captain"
}

def extract_first_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^\w\s]", "", name)
    tokens = [t for t in name.split() if t not in TITLES and len(t) > 1]
    return tokens[0] if tokens else ""


def gender_from_name(name: str):
    first = extract_first_name(name)

    if not first or name == "Narrator":
        return {"gender": "neutral", "confidence": 1.0}

    g = gender_detector.get_gender(first)

    mapping = {
        "male": ("male", 0.9),
        "mostly_male": ("male", 0.75),
        "female": ("female", 0.9),
        "mostly_female": ("female", 0.75),
        "andy": ("unknown", 0.4),
        "unknown": ("unknown", 0.0),
    }

    gender_label, conf = mapping.get(g, ("unknown", 0.0))
    return {"gender": gender_label, "confidence": conf}


def name_gender_score(name: str):
    info = gender_from_name(name)
    return info["gender"], info["confidence"]
