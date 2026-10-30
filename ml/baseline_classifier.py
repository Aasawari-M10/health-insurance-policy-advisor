from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
)
from transformers import pipeline


TEST_FILE = Path("data/intent_splits/test.csv")


# Human-readable labels given to the zero-shot model
CANDIDATE_LABELS = [
    "benefit",
    "waiting period",
    "exclusion",
    "documentation",
    "escalation",
]


# Convert human-readable model labels
# back to our application's internal labels
LABEL_MAPPING = {
    "benefit": "benefit",
    "waiting period": "waiting_period",
    "exclusion": "exclusion",
    "documentation": "documentation",
    "escalation": "escalation",
}


def load_test_data():
    """Load the test split created in Phase 6A."""

    if not TEST_FILE.exists():
        raise FileNotFoundError(
            f"Test file not found: {TEST_FILE}"
        )

    df = pd.read_csv(TEST_FILE)

    print(f"Loaded {len(df)} test records.")

    return df


def load_model():
    """Load pretrained zero-shot classification model."""

    print("\nLoading pretrained Hugging Face model...")

    classifier = pipeline(
        task="zero-shot-classification",
        model="facebook/bart-large-mnli",
    )

    print("Model loaded successfully.")

    return classifier


def predict_intent(classifier, question):
    """Predict intent for one insurance question."""

    result = classifier(
        question,
        candidate_labels=CANDIDATE_LABELS,
        hypothesis_template=(
            "This insurance question is about {}."
        ),
    )

    predicted_label = result["labels"][0]
    confidence = result["scores"][0]

    internal_label = LABEL_MAPPING[
        predicted_label
    ]

    return internal_label, confidence


def evaluate_baseline(classifier, test_df):
    """Evaluate baseline model."""

    actual_labels = []
    predicted_labels = []

    print("\nRunning predictions...\n")

    for _, row in test_df.iterrows():

        question = row["customer_question"]
        actual_intent = row["intent"]

        predicted_intent, confidence = (
            predict_intent(
                classifier,
                question,
            )
        )

        actual_labels.append(actual_intent)
        predicted_labels.append(predicted_intent)

        print("----------------------------------------")
        print(f"Question   : {question}")
        print(f"Actual     : {actual_intent}")
        print(f"Predicted  : {predicted_intent}")
        print(f"Confidence : {confidence:.4f}")

    accuracy = accuracy_score(
        actual_labels,
        predicted_labels,
    )

    macro_f1 = f1_score(
        actual_labels,
        predicted_labels,
        average="macro",
    )

    print("\n========================================")
    print("HUGGING FACE BASELINE RESULTS")
    print("========================================")

    print(f"Accuracy : {accuracy:.4f}")
    print(f"Macro F1 : {macro_f1:.4f}")

    print("\nClassification Report:\n")

    print(
        classification_report(
            actual_labels,
            predicted_labels,
            zero_division=0,
        )
    )

    return accuracy, macro_f1


def main():

    test_df = load_test_data()

    classifier = load_model()

    evaluate_baseline(
        classifier,
        test_df,
    )


if __name__ == "__main__":
    main()