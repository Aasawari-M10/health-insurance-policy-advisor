from pathlib import Path

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)


MODEL_PATH = Path("models/intent_classifier")


class IntentClassifierService:

    def __init__(self):

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Intent classifier model not found: "
                f"{MODEL_PATH}"
            )

        self.device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        print(
            f"Loading intent classifier on "
            f"{self.device}"
        )

        self.tokenizer = (
            AutoTokenizer.from_pretrained(
                MODEL_PATH
            )
        )

        self.model = (
            AutoModelForSequenceClassification
            .from_pretrained(
                MODEL_PATH
            )
        )

        self.model.to(self.device)

        self.model.eval()

    def classify_intent(
        self,
        question: str,
    ) -> dict:

        encoded = self.tokenizer(
            question,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=64,
        )

        encoded = {
            key: value.to(self.device)
            for key, value in encoded.items()
        }

        with torch.no_grad():

            output = self.model(
                **encoded
            )

        probabilities = torch.softmax(
            output.logits,
            dim=-1,
        )

        confidence, predicted_id = (
            torch.max(
                probabilities,
                dim=-1,
            )
        )

        label = self.model.config.id2label[
            predicted_id.item()
        ]

        return {
            "intent": label,
            "confidence": round(
                confidence.item(),
                4,
            ),
        }


intent_classifier_service = (
    IntentClassifierService()
)


def classify_intent(question: str) -> dict:
    return (
        intent_classifier_service
        .classify_intent(question)
    )