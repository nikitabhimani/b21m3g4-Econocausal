# Econocausal

This repository now includes a starter backend API and shared data contract for the causal discount optimization project.

## Quick start

1. Generate the data:
   - `python -m scripts.generate_data`
2. Run the backend API:
   - `uvicorn backend.app.main:app --reload`

## Shared contract

- Data source: `data/customers.csv`
- API base path: `/api`
- Main endpoints:
  - `/api/health`
  - `/api/summary`
  - `/api/customers/{customer_id}`
  - `/api/causal/summary`
  - `/api/causal/ite`
  - `/api/recommendations`
