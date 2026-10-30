import json
from pathlib import Path

import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

MODEL_DIR = Path("models/intent_classifier")
TEST_FILE = Path("data/intent_splits/test.csv")
RESULTS_DIR = Path("evaluation")

MAX_LENGTH = 64
BATCH_SIZE = 8


LABEL_TO_ID = {
    "benefit": 0,
    "documentation": 1,
    "escalation": 2,
    "exclusion": 3,
    "waiting_period": 4,
}

ID_TO_LABEL = {
    label_id: label
    for label, label_id in LABEL_TO_ID.items()
}


# ---------------------------------------------------------
# Dataset
# ---------------------------------------------------------

class IntentTestDataset(Dataset):

    def __init__(
        self,
        dataframe,
        tokenizer,
    ):
        self.questions = (
            dataframe["customer_question"].tolist()
        )

        self.labels = [
            LABEL_TO_ID[label]
            for label in dataframe["intent"]
        ]

        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.questions)

    def __getitem__(self, index):

        encoding = self.tokenizer(
            self.questions[index],
            truncation=True,
            padding="max_length",
            max_length=MAX_LENGTH,
            return_tensors="pt",
        )

        return {
            "question": self.questions[index],

            "input_ids": (
                encoding["input_ids"].squeeze(0)
            ),

            "attention_mask": (
                encoding["attention_mask"].squeeze(0)
            ),

            "labels": torch.tensor(
                self.labels[index],
                dtype=torch.long,
            ),
        }


# ---------------------------------------------------------
# Load test data
# ---------------------------------------------------------

def load_test_data():

    if not TEST_FILE.exists():
        raise FileNotFoundError(
            f"Test dataset not found: {TEST_FILE}"
        )

    df = pd.read_csv(TEST_FILE)

    required_columns = {
        "customer_question",
        "intent",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    df = df.dropna(
        subset=[
            "customer_question",
            "intent",
        ]
    ).copy()

    df["intent"] = (
        df["intent"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    invalid_labels = (
        set(df["intent"]) - set(LABEL_TO_ID)
    )

    if invalid_labels:
        raise ValueError(
            f"Invalid intent labels: "
            f"{invalid_labels}"
        )

    return df.reset_index(drop=True)


# ---------------------------------------------------------
# Evaluation
# ---------------------------------------------------------

def evaluate(
    model,
    data_loader,
    device,
):

    model.eval()

    actual_ids = []
    predicted_ids = []
    result_rows = []

    with torch.no_grad():

        for batch in data_loader:

            input_ids = batch["input_ids"].to(
                device
            )

            attention_mask = batch[
                "attention_mask"
            ].to(device)

            labels = batch["labels"].to(
                device
            )

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

            probabilities = torch.softmax(
                outputs.logits,
                dim=1,
            )

            confidence, predictions = torch.max(
                probabilities,
                dim=1,
            )

            actual_ids.extend(
                labels.cpu().tolist()
            )

            predicted_ids.extend(
                predictions.cpu().tolist()
            )

            for (
                question,
                actual,
                predicted,
                score,
            ) in zip(
                batch["question"],
                labels.cpu().tolist(),
                predictions.cpu().tolist(),
                confidence.cpu().tolist(),
            ):

                result_rows.append(
                    {
                        "question": question,
                        "actual_intent": (
                            ID_TO_LABEL[actual]
                        ),
                        "predicted_intent": (
                            ID_TO_LABEL[predicted]
                        ),
                        "confidence": round(
                            score,
                            4,
                        ),
                        "correct": (
                            actual == predicted
                        ),
                    }
                )

    return (
        actual_ids,
        predicted_ids,
        result_rows,
    )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    if not MODEL_DIR.exists():
        raise FileNotFoundError(
            "Fine-tuned model not found. "
            "Run Phase 6C first."
        )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Loading test dataset...")

    test_df = load_test_data()

    print(
        f"Test records: {len(test_df)}"
    )

    print("\nLoading fine-tuned model...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_DIR
    )

    model = (
        AutoModelForSequenceClassification
        .from_pretrained(
            MODEL_DIR
        )
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(f"Evaluation device: {device}")

    model.to(device)

    test_dataset = IntentTestDataset(
        dataframe=test_df,
        tokenizer=tokenizer,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
    )

    (
        actual_ids,
        predicted_ids,
        result_rows,
    ) = evaluate(
        model=model,
        data_loader=test_loader,
        device=device,
    )

    # -----------------------------------------------------
    # Metrics
    # -----------------------------------------------------

    accuracy = accuracy_score(
        actual_ids,
        predicted_ids,
    )

    macro_f1 = f1_score(
        actual_ids,
        predicted_ids,
        average="macro",
        zero_division=0,
    )

    labels = list(range(len(ID_TO_LABEL)))

    target_names = [
        ID_TO_LABEL[index]
        for index in labels
    ]

    report = classification_report(
        actual_ids,
        predicted_ids,
        labels=labels,
        target_names=target_names,
        zero_division=0,
    )

    matrix = confusion_matrix(
        actual_ids,
        predicted_ids,
        labels=labels,
    )

    print("\n========================================")
    print("FINE-TUNED MODEL TEST RESULTS")
    print("========================================")

    print(
        f"Accuracy : {accuracy:.4f}"
    )

    print(
        f"Macro F1 : {macro_f1:.4f}"
    )

    print("\nClassification Report:\n")

    print(report)

    print("Confusion Matrix:\n")

    print(matrix)

    # -----------------------------------------------------
    # Save per-question predictions
    # -----------------------------------------------------

    results_df = pd.DataFrame(
        result_rows
    )

    results_df.to_csv(
        RESULTS_DIR
        / "intent_classifier_predictions.csv",
        index=False,
    )

    # -----------------------------------------------------
    # Save summary metrics
    # -----------------------------------------------------

    metrics = {
        "accuracy": float(accuracy),
        "macro_f1": float(macro_f1),
        "test_records": len(test_df),
    }

    with (
        RESULTS_DIR
        / "intent_classifier_metrics.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metrics,
            file,
            indent=2,
        )

    print(
        "\nEvaluation results saved in "
        "the evaluation directory."
    )


if __name__ == "__main__":
    main()