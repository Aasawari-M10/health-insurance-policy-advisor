VALID_INTENTS = {
    "benefit",
    "waiting_period",
    "exclusion",
    "documentation",
    "escalation",
}


def classify_intent(question: str) -> str:
    """
    Temporary rule-based intent classifier.

    This will later be replaced by the trained
    Hugging Face intent classification model.
    """

    text = question.lower()

    if "document" in text:
        return "documentation"

    if "waiting" in text or "wait" in text:
        return "waiting_period"

    if "exclude" in text or "exclusion" in text:
        return "exclusion"

    if "guarantee" in text or "definitely" in text:
        return "escalation"

    if "cover" in text or "benefit" in text:
        return "benefit"

    return "escalation"