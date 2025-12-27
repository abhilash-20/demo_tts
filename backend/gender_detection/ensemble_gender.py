from .name_based import name_gender_score
from .pronoun_based import pronoun_gender_score
from .context_based import context_gender_score


# def ensemble_gender(text: str, character: str):
#     scores = {"male": 0.0, "female": 0.0}

#     # Name-based
#     g, c = name_gender_score(character)
#     if g in scores:
#         scores[g] += 0.3 * c

#     # Pronoun-based
#     g, c = pronoun_gender_score(text, character)
#     if g in scores:
#         scores[g] += 0.5 * c

#     # Context-based
#     g, c = context_gender_score(text, character)
#     if g in scores:
#         scores[g] += 0.2 * c

#     if scores["male"] == scores["female"] == 0:
#         return "unknown", 0.0

#     final_gender = max(scores, key=scores.get)
#     confidence = min(1.0, scores[final_gender])

#     return final_gender, confidence

def ensemble_gender(text: str, character: str):
    scores = {"male": 0.0, "female": 0.0}

    # Name-based (fallback)
    name_g, name_c = name_gender_score(character)
    if name_g == "neutral":                           # short-circuit for neutral names
        return "neutral", 1.0

    if name_g in scores:
        scores[name_g] += 0.3 * name_c

    print("Name-based output:", character, name_g, name_c)

    # Pronoun-based
    g, c = pronoun_gender_score(text, character)
    if g in scores:
        scores[g] += 0.5 * c

    print("Pronoun-based output:", character,g, c)

    # Context-based
    g, c = context_gender_score(text, character)
    if g in scores:
        scores[g] += 0.2 * c

    print("Context-based output:",character, g, c)

    # ✅ HARD fallback
    if scores["male"] == scores["female"] == 0:
        if name_g in {"male", "female"}:
            return name_g, max(0.6, name_c)
        return "neutral", 0.5

    final_gender = max(scores, key=scores.get)
    confidence = min(1.0, scores[final_gender])

    return final_gender, confidence
