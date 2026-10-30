import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
)
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

MODEL_NAME = "distilbert-base-uncased"

TRAIN_FILE = Path("data/intent_splits/train.csv")
VALIDATION_FILE = Path(
    "data/intent_splits/validation.csv"
)

OUTPUT_DIR = Path("models/intent_classifier")

MAX_LENGTH = 64
BATCH_SIZE = 8
EPOCHS = 3
LEARNING_RATE = 2e-5
RANDOM_SEED = 42


# ---------------------------------------------------------
# Intent label mapping
# ---------------------------------------------------------

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
# Reproducibility
# ---------------------------------------------------------

def set_seed(seed: int) -> None:
    """Set random seeds for reproducible experiments."""

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# ---------------------------------------------------------
# Dataset validation
# ---------------------------------------------------------

def load_dataset(file_path: Path) -> pd.DataFrame:
    """Load and validate an intent dataset split."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    required_columns = {
        "customer_question",
        "intent",
    }

    missing_columns = (
        required_columns - set(df.columns)
    )

    if missing_columns:
        raise ValueError(
            f"Missing required columns in "
            f"{file_path}: {missing_columns}"
        )

    df = df.dropna(
        subset=[
            "customer_question",
            "intent",
        ]
    ).copy()

    df["customer_question"] = (
        df["customer_question"]
        .astype(str)
        .str.strip()
    )

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
            f"Invalid labels found in "
            f"{file_path}: {invalid_labels}"
        )

    df["label"] = df["intent"].map(
        LABEL_TO_ID
    )

    return df.reset_index(drop=True)


# ---------------------------------------------------------
# PyTorch dataset
# ---------------------------------------------------------

class IntentDataset(Dataset):
    """Tokenized insurance-intent dataset."""

    def __init__(
        self,
        dataframe: pd.DataFrame,
        tokenizer,
        max_length: int,
    ):
        self.questions = (
            dataframe["customer_question"].tolist()
        )

        self.labels = dataframe["label"].tolist()

        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.questions)

    def __getitem__(self, index):
        question = self.questions[index]
        label = self.labels[index]

        encoding = self.tokenizer(
            question,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )

        return {
            "input_ids": (
                encoding["input_ids"].squeeze(0)
            ),
            "attention_mask": (
                encoding["attention_mask"].squeeze(0)
            ),
            "labels": torch.tensor(
                label,
                dtype=torch.long,
            ),
        }


# ---------------------------------------------------------
# Training
# ---------------------------------------------------------

def train_one_epoch(
    model,
    data_loader,
    optimizer,
    device,
):
    """Train the classifier for one epoch."""

    model.train()

    total_loss = 0.0

    for batch in data_loader:

        input_ids = batch["input_ids"].to(
            device
        )

        attention_mask = batch[
            "attention_mask"
        ].to(device)

        labels = batch["labels"].to(device)

        optimizer.zero_grad()

        output = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
        )

        loss = output.loss

        loss.backward()

        optimizer.step()

        total_loss += loss.item()

    average_loss = (
        total_loss / len(data_loader)
    )

    return average_loss


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

def evaluate_model(
    model,
    data_loader,
    device,
):
    """Evaluate model on validation data."""

    model.eval()

    total_loss = 0.0
    actual_labels = []
    predicted_labels = []

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

            output = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )

            total_loss += output.loss.item()

            predictions = torch.argmax(
                output.logits,
                dim=1,
            )

            actual_labels.extend(
                labels.cpu().numpy()
            )

            predicted_labels.extend(
                predictions.cpu().numpy()
            )

    average_loss = (
        total_loss / len(data_loader)
    )

    accuracy = accuracy_score(
        actual_labels,
        predicted_labels,
    )

    macro_f1 = f1_score(
        actual_labels,
        predicted_labels,
        average="macro",
        zero_division=0,
    )

    return {
        "loss": average_loss,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "actual_labels": actual_labels,
        "predicted_labels": predicted_labels,
    }


# ---------------------------------------------------------
# Save model
# ---------------------------------------------------------

def save_model(
    model,
    tokenizer,
    metrics,
):
    """Save fine-tuned model and label metadata."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    metadata = {
        "base_model": MODEL_NAME,
        "labels": LABEL_TO_ID,
        "validation_accuracy": (
            metrics["accuracy"]
        ),
        "validation_macro_f1": (
            metrics["macro_f1"]
        ),
        "max_length": MAX_LENGTH,
    }

    metadata_path = (
        OUTPUT_DIR / "training_metadata.json"
    )

    with metadata_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=2,
        )


# ---------------------------------------------------------
# Main training flow
# ---------------------------------------------------------

def main():

    set_seed(RANDOM_SEED)

    print("Loading datasets...")

    train_df = load_dataset(TRAIN_FILE)

    validation_df = load_dataset(
        VALIDATION_FILE
    )

    print(
        f"Training records: {len(train_df)}"
    )

    print(
        "Validation records: "
        f"{len(validation_df)}"
    )

    print("\nLabel mapping:")

    for label, label_id in LABEL_TO_ID.items():
        print(f"{label} -> {label_id}")

    print(
        f"\nLoading tokenizer: {MODEL_NAME}"
    )

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME
    )

    print(
        f"Loading pretrained model: {MODEL_NAME}"
    )

    model = (
        AutoModelForSequenceClassification
        .from_pretrained(
            MODEL_NAME,
            num_labels=len(LABEL_TO_ID),
            label2id=LABEL_TO_ID,
            id2label=ID_TO_LABEL,
        )
    )

    train_dataset = IntentDataset(
        dataframe=train_df,
        tokenizer=tokenizer,
        max_length=MAX_LENGTH,
    )

    validation_dataset = IntentDataset(
        dataframe=validation_df,
        tokenizer=tokenizer,
        max_length=MAX_LENGTH,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(f"\nTraining device: {device}")

    model.to(device)

    optimizer = AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
    )

    best_macro_f1 = -1.0
    best_metrics = None

    print("\nStarting fine-tuning...")

    for epoch in range(EPOCHS):

        print(
            "\n"
            "========================================"
        )

        print(
            f"Epoch {epoch + 1}/{EPOCHS}"
        )

        print(
            "========================================"
        )

        train_loss = train_one_epoch(
            model=model,
            data_loader=train_loader,
            optimizer=optimizer,
            device=device,
        )

        validation_metrics = evaluate_model(
            model=model,
            data_loader=validation_loader,
            device=device,
        )

        print(
            f"Training loss: "
            f"{train_loss:.4f}"
        )

        print(
            f"Validation loss: "
            f"{validation_metrics['loss']:.4f}"
        )

        print(
            f"Validation accuracy: "
            f"{validation_metrics['accuracy']:.4f}"
        )

        print(
            f"Validation Macro-F1: "
            f"{validation_metrics['macro_f1']:.4f}"
        )

        if (
            validation_metrics["macro_f1"]
            > best_macro_f1
        ):
            best_macro_f1 = (
                validation_metrics["macro_f1"]
            )

            best_metrics = validation_metrics

            save_model(
                model=model,
                tokenizer=tokenizer,
                metrics=validation_metrics,
            )

            print(
                "Best model saved to: "
                f"{OUTPUT_DIR}"
            )

    print("\n========================================")
    print("TRAINING COMPLETED")
    print("========================================")

    print(
        f"Best validation Macro-F1: "
        f"{best_macro_f1:.4f}"
    )

    print(
        "\nBest validation classification report:"
    )

    target_names = [
        ID_TO_LABEL[index]
        for index in range(len(ID_TO_LABEL))
    ]

    print(
        classification_report(
            best_metrics["actual_labels"],
            best_metrics["predicted_labels"],
            target_names=target_names,
            zero_division=0,
        )
    )

    print(
        f"\nFine-tuned model saved at: "
        f"{OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()