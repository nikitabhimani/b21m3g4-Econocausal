# Model Evaluation Results — T-Learner vs DML

Evaluated against ground-truth `true_ite` on 20% held-out test set.

| Model | MAE | Correlation with true_ite |
|---|---|---|
| T-Learner | 0.085173 | 0.4233 |
| DML (LinearDML + LightGBM) | 0.080110 | 0.4961 |

**Conclusion:** DML outperforms T-Learner on both metrics — ~6% lower error,
~17% higher correlation with ground truth.

**Key finding:** DML's performance is highly sensitive to which columns are
treated as covariates (X, drives heterogeneity) vs confounders (W, drives
bias-adjustment). Initially restricting covariates to only `age`/`tenure_months`
collapsed correlation to ~0.0007, because the generator's true_ite formula
depends on several other variables (previous_campaign_response, website_visits,
days_since_last_purchase, historical_revenue, customer_segment) for
heterogeneity. Including these in the covariate set restored correlation to 0.496.

**Note:** DML still raises a "co-variance matrix is underdetermined" warning,
likely due to overlap between covariate and confounder column sets (customer_segment
appears in both). Point estimates remain valid; confidence intervals should not
be trusted yet without further investigation.