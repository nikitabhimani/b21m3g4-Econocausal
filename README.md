# EconoCausal

EconoCausal is a causal customer-behaviour and discount-optimisation platform. It includes a synthetic customer-data generator, PostgreSQL data layer, FastAPI backend, and Next.js dashboard.

## Repository layout

- `data/` — generated customer data and its summary
- `scripts/generate_data.py` — reproducible synthetic-data generator
- `backend/` — database SQL, data utilities, and FastAPI application
- `backend/scripts/` — database load, validation, and export commands
- `frontend/` — Next.js dashboard
- `docs/database.md` — detailed database notes

## Prerequisites

- Python 3.8+
- Node.js and npm
- PostgreSQL 15+ or Docker Compose

Install the Python dependencies:

```bash
python3 -m pip install -r backend/requirements.txt
```

## Data

The checked-in dataset is accompanied by `data/dataset_summary.json`. To generate a reproducible dataset:

```bash
python3 -m scripts.generate_data --customers 100000 --seed 42 --treatment-rate 0.35
```

The generator validates customer IDs, missing values, treatment and purchase flags, discount rules, purchase logic, and consistency of the synthetic individual treatment effect (ITE).

## Database setup

Start PostgreSQL with Docker Compose, if needed:

```bash
docker compose up -d db
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/econocausal
```

Then apply the schema, seed rows, and customer CSV:

```bash
./scripts/setup_db.sh
```

Apply the supplementary indexes and summary views:

```bash
psql "$DATABASE_URL" -f backend/indexes.sql
psql "$DATABASE_URL" -f backend/views.sql
```

Validate the loaded data:

```bash
python3 backend/scripts/validate_db.py
```

Export customers for downstream use:

```bash
python3 backend/scripts/export_data.py --format csv --out data/customers_export.csv
python3 backend/scripts/export_data.py --format json --out data/customers_export.json
```

See [the database guide](docs/database.md) for local PostgreSQL setup and command details.

> Note: `data/customers.csv` is currently used together with the seed rows during bootstrap. Regenerating the CSV before running `setup_db.sh` can introduce duplicate seeded customer IDs; resolve that dataset/seed overlap before using regeneration in the bootstrap workflow.

## Run the application

Start the FastAPI development server:

```bash
uvicorn backend.app.main:app --reload --port 8001
```

Start the Next.js dashboard in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Service ports

- Backend API: `http://127.0.0.1:8001/api`
- Frontend dashboard: `http://localhost:3000`

## API endpoints

- `/api/health` — service health status
- `/api/summary` — customer counts, conversions, and revenue
- `/api/customers/{customer_id}` — a customer record
- `/api/causal/summary` — causal-model summary metrics
- `/api/causal/ite` — customers ranked by ITE
- `/api/recommendations` — budget-optimised customer recommendations

## Current data-layer status

The data layer currently provides the customer schema, model-run and recommendation tables, seed data, CSV loading, database validation, generic CSV/JSON exports, indexes, and customer/revenue summary views. Campaign and prediction tables, additional summary views, dedicated model/dashboard exports, and an idempotent refresh workflow are still planned.
