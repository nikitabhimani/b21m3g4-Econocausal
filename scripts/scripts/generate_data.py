"""
EconoCausal - Dataset Generation Script

Usage:

    python scripts/generate_data.py

Optional:

    python scripts/generate_data.py --customers 100000 --seed 42

Output:

    data/customers.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from backend.data.generator import (
    EconoCausalDataGenerator,
    GeneratorConfig,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"

OUTPUT_FILE = DATA_DIR / "customers.csv"

SUMMARY_FILE = DATA_DIR / "dataset_summary.json"


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate synthetic causal customer data "
            "for the EconoCausal project."
        )
    )

    parser.add_argument(
        "--customers",
        type=int,
        default=100_000,
        help="Number of customers to generate.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed.",
    )

    parser.add_argument(
        "--treatment-rate",
        type=float,
        default=0.35,
        help=(
            "Approximate treatment rate. "
            "Example: 0.35 = 35%%."
        ),
    )

    return parser.parse_args()


def validate_dataset(df: pd.DataFrame) -> None:
    """Run basic validation checks."""

    required_columns = [
        "customer_id",
        "age",
        "tenure_months",
        "customer_segment",
        "historical_orders",
        "historical_revenue",
        "avg_order_value",
        "days_since_last_purchase",
        "website_visits",
        "email_opens",
        "email_clicks",
        "previous_campaign_response",
        "treatment_received",
        "discount_percentage",
        "purchase",
        "purchase_value",
        "discount_cost",
        "net_revenue",
        "true_baseline_purchase_probability",
        "true_treatment_purchase_probability",
        "true_ite",
        "true_treatment_probability",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    # Customer IDs must be unique.
    if df["customer_id"].duplicated().any():
        raise ValueError(
            "customer_id contains duplicates."
        )

    # No null values.
    if df.isnull().any().any():
        null_columns = df.columns[
            df.isnull().any()
        ].tolist()

        raise ValueError(
            "Dataset contains null values in: "
            + ", ".join(null_columns)
        )

    # Treatment must be binary.
    treatment_values = set(
        df["treatment_received"].unique()
    )

    if not treatment_values.issubset({0, 1}):
        raise ValueError(
            "treatment_received must contain only 0 and 1."
        )

    # Purchase must be binary.
    purchase_values = set(
        df["purchase"].unique()
    )

    if not purchase_values.issubset({0, 1}):
        raise ValueError(
            "purchase must contain only 0 and 1."
        )

    # Discount must be valid.
    if (
        (df["discount_percentage"] < 0).any()
        or (df["discount_percentage"] > 1).any()
    ):
        raise ValueError(
            "Invalid discount_percentage detected."
        )

    # Control customers should not receive discounts.
    invalid_control_discounts = df[
        (df["treatment_received"] == 0)
        & (df["discount_percentage"] != 0)
    ]

    if len(invalid_control_discounts) > 0:
        raise ValueError(
            "Control customers have a non-zero discount."
        )

    # Treated customers should have a positive discount.
    invalid_treated_discounts = df[
        (df["treatment_received"] == 1)
        & (df["discount_percentage"] <= 0)
    ]

    if len(invalid_treated_discounts) > 0:
        raise ValueError(
            "Some treated customers have no discount."
        )

    # Purchase value should be zero when no purchase happened.
    invalid_purchase_values = df[
        (df["purchase"] == 0)
        & (df["purchase_value"] != 0)
    ]

    if len(invalid_purchase_values) > 0:
        raise ValueError(
            "Customers without a purchase have "
            "non-zero purchase_value."
        )

    # ITE should equal treatment probability difference
    # approximately.
    calculated_ite = (
        df["true_treatment_purchase_probability"]
        - df["true_baseline_purchase_probability"]
    )

    max_difference = np_abs_max(
        calculated_ite - df["true_ite"]
    )

    if max_difference > 1e-5:
        raise ValueError(
            "true_ite is inconsistent with potential outcomes."
        )


def np_abs_max(series: pd.Series) -> float:
    """Return maximum absolute value without requiring NumPy."""

    return float(
        series.abs().max()
    )


def print_dataset_report(
    df: pd.DataFrame,
) -> None:
    """Print useful information about generated data."""

    generator = EconoCausalDataGenerator()

    summary = generator.summary(df)

    print()
    print("=" * 70)
    print("EconoCausal Dataset Generated")
    print("=" * 70)

    print(
        f"Customers              : "
        f"{summary['customers']:,}"
    )

    print(
        f"Treated customers      : "
        f"{summary['treated_customers']:,}"
    )

    print(
        f"Control customers      : "
        f"{summary['control_customers']:,}"
    )

    print(
        f"Treatment rate         : "
        f"{summary['treatment_rate']:.2%}"
    )

    print(
        f"Overall purchase rate  : "
        f"{summary['purchase_rate']:.2%}"
    )

    print(
        f"Treated purchase rate  : "
        f"{summary['treated_purchase_rate']:.2%}"
    )

    print(
        f"Control purchase rate  : "
        f"{summary['control_purchase_rate']:.2%}"
    )

    print(
        f"Average true ITE       : "
        f"{summary['average_true_ite']:.4f}"
    )

    print(
        f"Median true ITE        : "
        f"{summary['median_true_ite']:.4f}"
    )

    print(
        f"Average purchase value : "
        f"₹{summary['average_purchase_value']:,.2f}"
    )

    print(
        f"Total revenue          : "
        f"₹{summary['total_revenue']:,.2f}"
    )

    print(
        f"Total discount cost    : "
        f"₹{summary['total_discount_cost']:,.2f}"
    )

    print()
    print("Customer segments:")
    print(
        df["customer_segment"]
        .value_counts()
        .to_string()
    )

    print()
    print("Discount distribution:")
    print(
        df["discount_percentage"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print()
    print("Dataset shape:")
    print(df.shape)

    print()
    print("Columns:")
    print(", ".join(df.columns))

    print("=" * 70)
    print()


def main() -> None:
    """Generate and save the dataset."""

    args = parse_arguments()

    if args.customers <= 0:
        raise ValueError(
            "--customers must be greater than 0."
        )

    if not 0 < args.treatment_rate < 1:
        raise ValueError(
            "--treatment-rate must be between 0 and 1."
        )

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    config = GeneratorConfig(
        n_customers=args.customers,
        seed=args.seed,
        treatment_probability=args.treatment_rate,
    )

    print()
    print(
        f"Generating {args.customers:,} customers..."
    )

    generator = EconoCausalDataGenerator(
        config=config
    )

    df = generator.generate()

    print("Running dataset validation...")

    validate_dataset(df)

    print("Validation passed.")

    # --------------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # --------------------------------------------------------------
    # Save summary JSON
    # --------------------------------------------------------------

    summary = generator.summary(df)

    summary["configuration"] = {
        "n_customers": args.customers,
        "seed": args.seed,
        "treatment_rate_target": args.treatment_rate,
        "discount_levels": list(
            config.discount_levels
        ),
        "purchase_window_days": (
            config.purchase_window_days
        ),
    }

    with open(
        SUMMARY_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            summary,
            file,
            indent=4,
        )

    print_dataset_report(df)

    print(
        f"CSV saved to:\n"
        f"  {OUTPUT_FILE}"
    )

    print(
        f"\nSummary saved to:\n"
        f"  {SUMMARY_FILE}"
    )


if __name__ == "__main__":
    main()