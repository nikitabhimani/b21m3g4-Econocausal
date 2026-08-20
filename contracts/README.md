# Shared data contracts (frozen v1)

`customer_dataset.schema.json` is the versioned source of truth for Person 1's customer input. CSV headers must match its property names; JSON input must be either an array of customer objects or an object with a `customers` array. `campaign_id` is optional to preserve the existing generated dataset.

Downstream contracts are frozen as v1 JSON Schemas: `causal_prediction.schema.json`, `causal_summary.schema.json`, `uplift_results.schema.json`, and `recommendation.schema.json`. Causal predictions use `customer_id`, `baseline_probability`, `treatment_probability`, and `ite`; recommendations additionally carry `predicted_ite`, `recommended_discount`, `expected_profit`, and `expected_cost`. These fields map directly to `predictions` and `recommendations`.
