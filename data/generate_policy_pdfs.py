import json
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


DATA_DIR = Path("data")
OUTPUT_DIR = DATA_DIR / "documents"

PLANS_FILE = DATA_DIR / "plans.csv"
CLAUSES_FILE = DATA_DIR / "policy_clauses.jsonl"
BENEFITS_FILE = DATA_DIR / "benefit_schedule.csv"


def load_policy_clauses():
    clauses = []

    with CLAUSES_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            if line.strip():
                clauses.append(
                    json.loads(line)
                )

    return clauses


def get_styles():

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="PolicyTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=20,
            spaceAfter=15,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#0F2747"),
            spaceBefore=12,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ClauseHeading",
            parent=styles["Heading3"],
            fontSize=11,
            textColor=colors.HexColor("#0078D4"),
            spaceBefore=8,
            spaceAfter=4,
        )
    )

    return styles


def create_policy_pdf(
    plan,
    clauses,
    benefit_schedule,
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plan_name = plan["plan_name"]
    plan_id = plan["plan_id"]
    version = plan["version"]

    safe_name = (
        plan_name
        .replace(" ", "_")
        .replace("/", "_")
    )

    output_file = (
        OUTPUT_DIR
        / f"{safe_name}_{version}.pdf"
    )

    document = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50,
    )

    styles = get_styles()

    story = []

    # -------------------------------------------------
    # Title
    # -------------------------------------------------

    story.append(
        Paragraph(
            plan_name,
            styles["PolicyTitle"],
        )
    )

    story.append(
        Paragraph(
            f"Fictional Policy Document - Version {version}",
            styles["Heading2"],
        )
    )

    story.append(
        Spacer(
            1,
            0.2 * inch,
        )
    )

    # -------------------------------------------------
    # Disclaimer
    # -------------------------------------------------

    story.append(
        Paragraph(
            "<b>Important:</b> "
            "This is synthetic policy data created "
            "only for the Health Insurance Policy "
            "Advisor capstone project. It does not "
            "represent a real insurance product.",
            styles["BodyText"],
        )
    )

    story.append(
        Spacer(
            1,
            0.25 * inch,
        )
    )

    # -------------------------------------------------
    # Plan Information
    # -------------------------------------------------

    story.append(
        Paragraph(
            "1. Plan Information",
            styles["SectionHeading"],
        )
    )

    plan_table_data = [
        ["Field", "Value"],
        ["Plan ID", plan_id],
        ["Plan Name", plan_name],
        ["Version", version],
        [
            "Effective Date",
            str(plan["effective_date"]),
        ],
        ["Status", plan["status"]],
    ]

    plan_table = Table(
        plan_table_data,
        colWidths=[
            1.7 * inch,
            3.5 * inch,
        ],
    )

    plan_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#0F2747"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(plan_table)

    story.append(
        Spacer(
            1,
            0.25 * inch,
        )
    )

    # -------------------------------------------------
    # Policy Sections
    # -------------------------------------------------

    sections = [
        (
            "Benefits",
            "benefit",
        ),
        (
            "Waiting Periods",
            "waiting_period",
        ),
        (
            "Exclusions",
            "exclusion",
        ),
        (
            "Required Documentation",
            "documentation",
        ),
    ]

    section_number = 2

    for section_name, category in sections:

        matching_clauses = [
            clause
            for clause in clauses
            if (
                clause["plan_id"] == plan_id
                and
                clause["version"] == version
                and
                clause["category"] == category
            )
        ]

        story.append(
            Paragraph(
                f"{section_number}. "
                f"{section_name}",
                styles["SectionHeading"],
            )
        )

        if not matching_clauses:

            story.append(
                Paragraph(
                    "No synthetic clauses are "
                    "available for this section.",
                    styles["BodyText"],
                )
            )

        for clause in matching_clauses:

            story.append(
                Paragraph(
                    (
                        f"<b>Clause ID:</b> "
                        f"{clause['clause_id']}"
                    ),
                    styles["ClauseHeading"],
                )
            )

            story.append(
                Paragraph(
                    (
                        f"<b>Section:</b> "
                        f"{clause['section']}"
                    ),
                    styles["BodyText"],
                )
            )

            story.append(
                Spacer(
                    1,
                    0.05 * inch,
                )
            )

            story.append(
                Paragraph(
                    clause["text"],
                    styles["BodyText"],
                )
            )

            story.append(
                Spacer(
                    1,
                    0.15 * inch,
                )
            )

        section_number += 1

    # -------------------------------------------------
    # Benefit Schedule
    # -------------------------------------------------

    story.append(
        Paragraph(
            f"{section_number}. Benefit Schedule",
            styles["SectionHeading"],
        )
    )

    matching_benefits = benefit_schedule[
        (
            benefit_schedule["plan_id"]
            == plan_id
        )
        &
        (
            benefit_schedule["version"]
            == version
        )
    ]

    if not matching_benefits.empty:

        benefit_rows = [
            [
                "Benefit ID",
                "Limit Type",
                "Synthetic Amount",
                "Waiting Days",
            ]
        ]

        for _, benefit in (
            matching_benefits.iterrows()
        ):

            benefit_rows.append(
                [
                    benefit["benefit_id"],
                    benefit["limit_type"],
                    str(
                        benefit[
                            "synthetic_amount"
                        ]
                    ),
                    str(
                        benefit["waiting_days"]
                    ),
                ]
            )

        benefit_table = Table(
            benefit_rows,
            repeatRows=1,
        )

        benefit_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#0078D4"
                        ),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "PADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(benefit_table)

    else:

        story.append(
            Paragraph(
                "No synthetic benefit schedule "
                "is available.",
                styles["BodyText"],
            )
        )

    # -------------------------------------------------
    # Final notice
    # -------------------------------------------------

    story.append(PageBreak())

    story.append(
        Paragraph(
            "Synthetic Data Notice",
            styles["SectionHeading"],
        )
    )

    story.append(
        Paragraph(
            "This document was generated from "
            "fictional synthetic policy data for "
            "demonstration, development, testing, "
            "retrieval and evaluation purposes only.",
            styles["BodyText"],
        )
    )

    document.build(story)

    print(
        f"Created: {output_file}"
    )


def main():

    plans = pd.read_csv(
        PLANS_FILE
    )

    benefit_schedule = pd.read_csv(
        BENEFITS_FILE
    )

    clauses = load_policy_clauses()

    print(
        f"Plans loaded: {len(plans)}"
    )

    print(
        f"Clauses loaded: {len(clauses)}"
    )

    for _, plan in plans.iterrows():

        create_policy_pdf(
            plan=plan,
            clauses=clauses,
            benefit_schedule=benefit_schedule,
        )

    print(
        "\nSynthetic policy PDFs "
        "generated successfully."
    )


if __name__ == "__main__":
    main()