CONTEXT_MALE = {
    "father", "brother", "son", "husband", "king", "actor", "prince"
}
CONTEXT_FEMALE = {
    "mother", "sister", "daughter", "wife", "queen", "actress", "princess"
}

def context_gender_score(text: str, character: str, window=2):
    sentences = text.split(".")
    male_hits = 0
    female_hits = 0

    for i, sent in enumerate(sentences):
        if character.lower() in sent.lower():
            context = " ".join(
                sentences[max(0, i - window): i + window + 1]
            ).lower()

            male_hits += sum(1 for w in CONTEXT_MALE if w in context)
            female_hits += sum(1 for w in CONTEXT_FEMALE if w in context)

    total = male_hits + female_hits
    if total == 0:
        return "unknown", 0.0

    if male_hits > female_hits:
        return "male", male_hits / total
    else:
        return "female", female_hits / total
