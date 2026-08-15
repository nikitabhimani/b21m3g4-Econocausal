# Model Evaluation Results — T-Learner vs DML

Evaluated against ground-truth `true_ite` on 20% held-out test set.

| Model | MAE | Correlation with true_ite |
|---|---|---|
| T-Learner | 0.084909 | 0.4101 |
| DML (LinearDML) | 0.080390 | 0.4956 |

**Conclusion:** DML outperforms T-Learner on both metrics — ~5% lower error,
~21% higher correlation with ground truth. This matches theoretical expectation
given the dataset's deliberate confounding structure.

**Note:** DML raised a "co-variance matrix is underdetermined" warning — point
estimates (ITE values) remain valid, but confidence intervals/inference from
this model should not be trusted yet. To be investigated separately.