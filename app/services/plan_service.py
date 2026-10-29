from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/plans.csv")


def get_all_plans():
    df = pd.read_csv(DATA_PATH)

    return df.to_dict(orient="records")


def get_active_plan_version(plan_id: str):
    df = pd.read_csv(DATA_PATH)

    matching_plans = df[
        (df["plan_id"] == plan_id)
        & (df["status"] == "active")
    ]

    if matching_plans.empty:
        return None

    return matching_plans.iloc[0].to_dict()