"""
EconoCausal - Synthetic Causal Dataset Generator

Generates a realistic customer/campaign dataset containing:

- Customer demographics
- Historical behavior
- Engagement
- Customer segments
- Non-random treatment assignment
- Multiple discount levels
- Heterogeneous treatment effects
- Binary purchase outcome
- Purchase revenue
- Ground-truth treatment effects

IMPORTANT:
The true treatment effect is intentionally NOT used as an input feature.
It is retained only for evaluating the causal ML model later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class GeneratorConfig:
    """Configuration for the synthetic data generator."""

    n_customers: int = 100_000
    seed: int = 42

    # Treatment configuration
    treatment_probability: float = 0.35
    discount_levels: tuple[float, ...] = (
        0.00,
        0.05,
        0.10,
        0.15,
        0.20,
    )

    # Outcome configuration
    purchase_window_days: int = 30

    # Revenue configuration
    min_purchase_value: float = 20.0
    max_purchase_value: float = 2_000.0


class EconoCausalDataGenerator:
    """
    Generates synthetic data for causal inference experiments.

    The data-generating process intentionally contains confounding:

        Customer characteristics
                 |
          +------+------+
          |             |
          v             v
       Treatment      Purchase

    This allows us to test whether Double Machine Learning can
    recover treatment effects in the presence of confounding.
    """

    SEGMENTS = [
        "budget",
        "standard",
        "premium",
        "vip",
    ]

    def __init__(self, config: Optional[GeneratorConfig] = None):
        self.config = config or GeneratorConfig()
        self.rng = np.random.default_rng(self.config.seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self) -> pd.DataFrame:
        """Generate the complete synthetic customer dataset."""

        self._validate_config()

        n = self.config.n_customers

        customer_id = np.arange(1, n + 1)

        # --------------------------------------------------------------
        # 1. Demographics
        # --------------------------------------------------------------

        age = np.clip(
            self.rng.normal(
                loc=36,
                scale=11,
                size=n,
            ),
            18,
            75,
        ).round().astype(int)

        tenure_months = np.clip(
            self.rng.gamma(
                shape=2.5,
                scale=14,
                size=n,
            ),
            1,
            120,
        ).round().astype(int)

        # --------------------------------------------------------------
        # 2. Customer segment
        # --------------------------------------------------------------

        segment = self.rng.choice(
            self.SEGMENTS,
            size=n,
            p=[0.20, 0.50, 0.23, 0.07],
        )

        segment_order = {
            "budget": 0,
            "standard": 1,
            "premium": 2,
            "vip": 3,
        }

        segment_score = np.array(
            [segment_order[value] for value in segment],
            dtype=float,
        )

        # --------------------------------------------------------------
        # 3. Historical customer behavior
        # --------------------------------------------------------------

        segment_multiplier = np.select(
            [
                segment == "budget",
                segment == "standard",
                segment == "premium",
                segment == "vip",
            ],
            [
                0.75,
                1.00,
                1.40,
                1.90,
            ],
            default=1.0,
        )

        historical_orders = np.maximum(
            0,
            self.rng.poisson(
                lam=3.5 * segment_multiplier
                + 0.025 * tenure_months
            ),
        ).astype(int)

        avg_order_value = np.clip(
            self.rng.lognormal(
                mean=np.log(75 * segment_multiplier),
                sigma=0.45,
                size=n,
            ),
            20,
            500,
        )

        historical_revenue = (
            historical_orders * avg_order_value
        )

        historical_revenue *= self.rng.lognormal(
            mean=0,
            sigma=0.15,
            size=n,
        )

        historical_revenue = np.round(
            historical_revenue,
            2,
        )

        # --------------------------------------------------------------
        # 4. Recency
        # --------------------------------------------------------------

        days_since_last_purchase = np.clip(
            self.rng.gamma(
                shape=2.0,
                scale=18.0,
                size=n,
            ),
            1,
            180,
        ).round().astype(int)

        # --------------------------------------------------------------
        # 5. Digital engagement
        # --------------------------------------------------------------

        website_visits = np.maximum(
            0,
            self.rng.poisson(
                lam=5
                + 0.015 * historical_orders
                + 2.5 * segment_score
            ),
        ).astype(int)

        email_opens = np.maximum(
            0,
            self.rng.poisson(
                lam=3
                + 0.35 * website_visits
                + 1.2 * segment_score
            ),
        ).astype(int)

        email_clicks = np.minimum(
            email_opens,
            np.maximum(
                0,
                self.rng.poisson(
                    lam=0.25
                    + 0.10 * email_opens
                ),
            ),
        ).astype(int)

        # --------------------------------------------------------------
        # 6. Previous campaign response
        # --------------------------------------------------------------

        engagement_score = (
            0.25 * np.log1p(website_visits)
            + 0.35 * np.log1p(email_opens)
            + 0.60 * np.log1p(email_clicks)
            + 0.20 * segment_score
        )

        previous_response_probability = self._sigmoid(
            -2.0
            + 0.80 * engagement_score
            + 0.0005 * historical_revenue
            - 0.012 * days_since_last_purchase
        )

        previous_campaign_response = (
            self.rng.random(n)
            < previous_response_probability
        ).astype(int)

        # --------------------------------------------------------------
        # 7. Price sensitivity
        # --------------------------------------------------------------
        #
        # This variable influences treatment assignment and treatment
        # response but is intentionally NOT included in the final
        # observed feature set.
        #
        # This creates a realistic latent component while still keeping
        # the observed dataset useful for causal inference.
        # --------------------------------------------------------------

        price_sensitivity = np.clip(
            self.rng.normal(
                loc=0.0,
                scale=1.0,
                size=n,
            ),
            -2.5,
            2.5,
        )

        # --------------------------------------------------------------
        # 8. Baseline purchase probability
        # --------------------------------------------------------------

        baseline_logit = (
            -2.60
            + 0.025 * (age - 35)
            + 0.012 * tenure_months
            + 0.0007 * historical_revenue
            + 0.10 * np.log1p(historical_orders)
            - 0.018 * days_since_last_purchase
            + 0.10 * np.log1p(website_visits)
            + 0.06 * np.log1p(email_opens)
            + 0.15 * previous_campaign_response
            + 0.18 * segment_score
            - 0.35 * price_sensitivity
        )

        baseline_purchase_probability = self._sigmoid(
            baseline_logit
        )

        # --------------------------------------------------------------
        # 9. Treatment assignment
        # --------------------------------------------------------------
        #
        # IMPORTANT:
        # Treatment is deliberately NOT randomized.
        #
        # Higher-value / more engaged customers have a higher probability
        # of receiving a discount.
        #
        # This creates confounding.
        # --------------------------------------------------------------

        treatment_logit = (
            -1.00
            + 0.0009 * historical_revenue
            + 0.20 * np.log1p(historical_orders)
            + 0.14 * np.log1p(website_visits)
            + 0.20 * previous_campaign_response
            + 0.25 * segment_score
            - 0.015 * days_since_last_purchase
            - 0.20 * price_sensitivity
        )

        # Shift treatment probability so that the approximate treatment
        # rate is controlled around the requested level.
        treatment_logit += self._calibrate_logit(
            treatment_logit,
            self.config.treatment_probability,
        )

        treatment_probability = self._sigmoid(
            treatment_logit
        )

        treatment_received = (
            self.rng.random(n)
            < treatment_probability
        ).astype(int)

        # --------------------------------------------------------------
        # 10. Discount assignment
        # --------------------------------------------------------------

        discount_percentage = np.zeros(n)

        treated_indices = np.where(
            treatment_received == 1
        )[0]

        if len(treated_indices) > 0:

            # Only calculate discount scores for treated customers.
            #
            # Higher-value and more engaged customers are more likely
            # to receive larger discounts.
            discount_score = (
                0.50 * segment_score[treated_indices]
                + 0.0005 * historical_revenue[treated_indices]
                + 0.15 * previous_campaign_response[treated_indices]
                - 0.01 * days_since_last_purchase[treated_indices]
                - 0.20 * price_sensitivity[treated_indices]
                + self.rng.normal(
                    0,
                    0.7,
                    size=len(treated_indices),
                )
            )

            # Convert scores to percentile ranks.
            ranks = (
                pd.Series(discount_score)
                .rank(
                    method="first",
                    pct=True,
                )
                .to_numpy()
            )

            # Available non-zero discount levels.
            discount_levels = np.array(
                self.config.discount_levels[1:],
                dtype=float,
            )

            # Map percentile → discount level.
            level_indices = np.minimum(
                (
                    ranks * len(discount_levels)
                ).astype(int),
                len(discount_levels) - 1,
            )

            discount_percentage[
                treated_indices
            ] = discount_levels[level_indices]

        # --------------------------------------------------------------
        # 11. Heterogeneous treatment effect
        # --------------------------------------------------------------
        #
        # Treatment effect depends on customer characteristics.
        #
        # This is what makes ITE estimation meaningful.
        # --------------------------------------------------------------

        discount_effect = (
            0.75 * discount_percentage
            + 3.0 * discount_percentage**2
        )

        responsiveness = (
            0.60
            + 0.20 * previous_campaign_response
            + 0.10 * np.log1p(website_visits)
            + 0.08 * segment_score
            - 0.15 * price_sensitivity
        )

        recency_effect = np.exp(
            -days_since_last_purchase / 90.0
        )

        true_ite = (
            discount_effect
            * responsiveness
            * recency_effect
        )

        # Additional nonlinear customer-specific effect.
        true_ite += (
            0.015
            * np.sin(historical_revenue / 100)
            * discount_percentage
        )

        # Treatment effect is defined relative to no treatment.
        true_ite = np.clip(
            true_ite,
            -0.05,
            0.80,
        )

        # --------------------------------------------------------------
        # 12. Potential outcomes
        # --------------------------------------------------------------

        # Control potential outcome.
        purchase_probability_control = np.clip(
            baseline_purchase_probability,
            0.001,
            0.999,
        )

        # Treatment potential outcome.
        #
        # IMPORTANT:
        # The actual ITE must always equal:
        #
        #   P(Y=1 | T=1, X) - P(Y=1 | T=0, X)
        #
        # Therefore, calculate the treatment probability first and then
        # derive the final ITE from the two potential outcomes.
        raw_treatment_probability = (
            purchase_probability_control
            + true_ite
        )

        purchase_probability_treatment = np.clip(
            raw_treatment_probability,
            0.001,
            0.999,
        )

        # Recalculate ITE after probability clipping so that the
        # ground-truth relationship is mathematically consistent.
        true_ite = (
            purchase_probability_treatment
            - purchase_probability_control
        )

        true_ite = np.round(
            true_ite,
            10,
        )

        # --------------------------------------------------------------
        # 13. Observed purchase
        # --------------------------------------------------------------

        observed_purchase_probability = np.where(
            treatment_received == 1,
            purchase_probability_treatment,
            purchase_probability_control,
        )

        purchase = (
            self.rng.random(n)
            < observed_purchase_probability
        ).astype(int)

        # --------------------------------------------------------------
        # 14. Purchase value
        # --------------------------------------------------------------

        purchase_value = np.zeros(n)

        purchased_indices = np.where(
            purchase == 1
        )[0]

        if len(purchased_indices) > 0:

            purchase_value[purchased_indices] = np.clip(
                self.rng.lognormal(
                    mean=np.log(
                        avg_order_value[purchased_indices]
                    ),
                    sigma=0.35,
                ),
                self.config.min_purchase_value,
                self.config.max_purchase_value,
            )

        purchase_value = np.round(
            purchase_value,
            2,
        )

        # --------------------------------------------------------------
        # 15. Campaign economics
        # --------------------------------------------------------------

        discount_cost = (
            purchase_value
            * discount_percentage
        )

        net_revenue = (
            purchase_value
            - discount_cost
        )

        # --------------------------------------------------------------
        # 16. Build final dataframe
        # --------------------------------------------------------------

        df = pd.DataFrame(
            {
                "customer_id": customer_id,

                # Demographics
                "age": age,
                "tenure_months": tenure_months,

                # Customer profile
                "customer_segment": segment,

                # Historical behavior
                "historical_orders": historical_orders,
                "historical_revenue": historical_revenue,
                "avg_order_value": np.round(
                    avg_order_value,
                    2,
                ),
                "days_since_last_purchase": (
                    days_since_last_purchase
                ),

                # Engagement
                "website_visits": website_visits,
                "email_opens": email_opens,
                "email_clicks": email_clicks,
                "previous_campaign_response": (
                    previous_campaign_response
                ),

                # Treatment
                "treatment_received": treatment_received,
                "discount_percentage": discount_percentage,

                # Outcome
                "purchase": purchase,
                "purchase_value": purchase_value,

                # Economics
                "discount_cost": np.round(
                    discount_cost,
                    2,
                ),
                "net_revenue": np.round(
                    net_revenue,
                    2,
                ),

                # Ground truth / evaluation only
                "true_baseline_purchase_probability": (
                    purchase_probability_control
                ),
                "true_treatment_purchase_probability": (
                    purchase_probability_treatment
                ),
                "true_ite": true_ite,

                # Treatment assignment probability
                "true_treatment_probability": (
                    treatment_probability
                ),
            }
        )

        # Round probability columns for cleaner CSV output.
        probability_columns = [
            "true_baseline_purchase_probability",
            "true_treatment_purchase_probability",
            "true_ite",
            "true_treatment_probability",
        ]

        df[probability_columns] = df[
            probability_columns
        ].round(10)

        return df

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    @staticmethod
    def _sigmoid(x: np.ndarray) -> np.ndarray:
        """Numerically stable sigmoid."""

        x = np.clip(x, -50, 50)

        return 1.0 / (
            1.0 + np.exp(-x)
        )

    @staticmethod
    def _calibrate_logit(
        logits: np.ndarray,
        target_probability: float,
    ) -> float:
        """
        Find an approximate intercept adjustment so that the average
        sigmoid(logit + adjustment) is close to target_probability.
        """

        target_probability = np.clip(
            target_probability,
            0.01,
            0.99,
        )

        low = -20.0
        high = 20.0

        for _ in range(60):

            midpoint = (
                low + high
            ) / 2.0

            probability = np.mean(
                EconoCausalDataGenerator._sigmoid(
                    logits + midpoint
                )
            )

            if probability < target_probability:
                low = midpoint
            else:
                high = midpoint

        return (
            low + high
        ) / 2.0

    def _validate_config(self) -> None:
        """Validate generator configuration."""

        if self.config.n_customers <= 0:
            raise ValueError(
                "n_customers must be greater than 0."
            )

        if not 0 < self.config.treatment_probability < 1:
            raise ValueError(
                "treatment_probability must be between 0 and 1."
            )

        if len(self.config.discount_levels) < 2:
            raise ValueError(
                "At least two discount levels are required."
            )

        if self.config.discount_levels[0] != 0.0:
            raise ValueError(
                "The first discount level must be 0.0."
            )

        if any(
            discount < 0 or discount > 1
            for discount in self.config.discount_levels
        ):
            raise ValueError(
                "Discount levels must be between 0 and 1."
            )

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def summary(df: pd.DataFrame) -> dict:
        """Return useful dataset-level statistics."""

        treated = df[
            df["treatment_received"] == 1
        ]

        control = df[
            df["treatment_received"] == 0
        ]

        return {
            "customers": len(df),
            "treated_customers": len(treated),
            "control_customers": len(control),
            "treatment_rate": (
                len(treated) / len(df)
            ),
            "purchase_rate": df[
                "purchase"
            ].mean(),
            "treated_purchase_rate": (
                treated["purchase"].mean()
                if len(treated)
                else 0.0
            ),
            "control_purchase_rate": (
                control["purchase"].mean()
                if len(control)
                else 0.0
            ),
            "average_true_ite": df[
                "true_ite"
            ].mean(),
            "median_true_ite": df[
                "true_ite"
            ].median(),
            "average_purchase_value": df[
                "purchase_value"
            ].mean(),
            "total_revenue": df[
                "purchase_value"
            ].sum(),
            "total_discount_cost": df[
                "discount_cost"
            ].sum(),
        }
if __name__ == "__main__":

    config = GeneratorConfig(n_customers=100_000)

    generator = EconoCausalDataGenerator(config)

    df = generator.generate()

    output_path = "data/econocausal_dataset.csv"
    df.to_csv(output_path, index=False)

    print("Dataset generated successfully!")
    print(f"Shape: {df.shape}")
    print(f"Saved to: {output_path}")
