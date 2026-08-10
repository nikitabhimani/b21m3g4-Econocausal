# Suggested Implementation Approach

## Project

Causal Customer Behavior & Discount Optimization

## Proposed Approach

The proposed system will use causal machine learning to estimate how a
specific intervention, such as a discount, may change an individual
customer's purchase probability.

The suggested implementation follows the pipeline:

Historical Customer/Campaign Data
        ↓
Causal DAG
        ↓
Confounder Identification
        ↓
Double Machine Learning / ITE
        ↓
Uplift & Qini Analysis
        ↓
Budget-Constrained Optimization
        ↓
Discount Recommendation Dashboard

## Suggested Components

### 1. Data Preparation
- Collect or identify suitable historical customer and campaign data.
- Clean and preprocess customer, treatment, and outcome variables.
- Perform exploratory data analysis.

### 2. Causal Modeling
- Define the causal relationships using a Directed Acyclic Graph (DAG).
- Identify potential confounding variables.
- Define treatment, outcome, and relevant covariates.

### 3. Treatment Effect Estimation
- Apply Double Machine Learning.
- Estimate treatment effects for individual or customer segments.
- Analyze treatment-effect heterogeneity.

### 4. Uplift Analysis
- Rank customers according to estimated incremental response.
- Evaluate targeting performance using uplift analysis and Qini curves.

### 5. Discount Optimization
- Define a campaign budget constraint.
- Use estimated treatment effects to identify customers who are expected
  to generate the highest incremental value.
- Explore constrained optimization using SciPy.

### 6. Recommendation Dashboard
- Display customer treatment effects.
- Show uplift and Qini analysis.
- Present recommended customers for intervention.
- Display estimated incremental impact and budget utilization.

## Suggested Technology Stack

- Python
- Pandas / NumPy
- Scikit-learn
- EconML
- SciPy
- Matplotlib / Plotly
- Streamlit

## Expected Outcome

A prototype decision-support system that combines causal inference,
uplift modeling, and optimization to support more effective
customer-level discount targeting.

## Note

This document represents the team's suggested implementation approach.
Dataset selection, feature definitions, model configuration,
optimization formulation, and final system architecture will be
finalized during project development.