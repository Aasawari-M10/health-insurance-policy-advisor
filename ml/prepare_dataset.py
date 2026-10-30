from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


# --------------------------------------------------
# Paths
# --------------------------------------------------

INPUT_FILE = Path("data/intent_training.csv")
OUTPUT_DIR = Path("data/intent_splits")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# Allowed intent labels
# --------------------------------------------------

VALID_INTENTS = {
    "benefit",
    "waiting_period",
    "exclusion",
    "documentation",
    "escalation",
}


def load_dataset() -> pd.DataFrame:
    """Load the synthetic intent-classification dataset."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print(f"Original rows: {len(df)}")

    return df


def validate_columns(df: pd.DataFrame) -> None:
    """Check that required columns are available."""

    required_columns = {
        "query_id",
        "customer_question",
        "intent",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate the classifier dataset."""

    # Remove rows with missing values
    df = df.dropna(
        subset=["customer_question", "intent"]
    )

    # Ensure text fields are strings
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

    # Remove empty questions
    df = df[
        df["customer_question"].str.len() > 0
    ]

    # Check labels
    invalid_labels = set(df["intent"]) - VALID_INTENTS

    if invalid_labels:
        raise ValueError(
            f"Invalid intent labels found: {invalid_labels}"
        )

    # Remove exact duplicate question + intent combinations
    df = df.drop_duplicates(
        subset=[
            "customer_question",
            "intent",
        ]
    )

    # Shuffle reproducibly
    df = df.sample(
        frac=1,
        random_state=42,
    ).reset_index(drop=True)

    print(f"Rows after cleaning: {len(df)}")

    return df


def show_class_distribution(df: pd.DataFrame) -> None:
    """Display number of samples for each intent."""

    print("\nIntent distribution:")

    print(
        df["intent"]
        .value_counts()
        .sort_index()
    )


def create_splits(df: pd.DataFrame):
    """
    Create:

    70% training
    15% validation
    15% testing

    using stratification.
    """

    # First split:
    # 70% train
    # 30% temporary
    train_df, temp_df = train_test_split(
        df,
        test_size=0.30,
        random_state=42,
        stratify=df["intent"],
    )

    # Split remaining 30% equally:
    # 15% validation
    # 15% test
    validation_df, test_df = train_test_split(
        temp_df,
        test_size=0.50,
        random_state=42,
        stratify=temp_df["intent"],
    )

    return train_df, validation_df, test_df


def save_splits(
    train_df,
    validation_df,
    test_df,
) -> None:
    """Save dataset splits."""

    train_df.to_csv(
        OUTPUT_DIR / "train.csv",
        index=False,
    )

    validation_df.to_csv(
        OUTPUT_DIR / "validation.csv",
        index=False,
    )

    test_df.to_csv(
        OUTPUT_DIR / "test.csv",
        index=False,
    )


def main():
    df = load_dataset()

    validate_columns(df)

    df = clean_dataset(df)

    show_class_distribution(df)

    train_df, validation_df, test_df = (
        create_splits(df)
    )

    save_splits(
        train_df,
        validation_df,
        test_df,
    )

    print("\nDataset split completed.")

    print(f"Training rows: {len(train_df)}")
    print(
        f"Validation rows: {len(validation_df)}"
    )
    print(f"Testing rows: {len(test_df)}")

    print("\nTraining distribution:")
    print(
        train_df["intent"]
        .value_counts()
        .sort_index()
    )

    print("\nValidation distribution:")
    print(
        validation_df["intent"]
        .value_counts()
        .sort_index()
    )

    print("\nTesting distribution:")
    print(
        test_df["intent"]
        .value_counts()
        .sort_index()
    )


if __name__ == "__main__":
    main()