# Database setup and data loading

This document explains how to create the PostgreSQL database, apply the schema, seed data, load the generated CSV, and run validations.

Prerequisites
- `psql` client available
- Python 3.8+
- `DATABASE_URL` environment variable set to a Postgres DSN, e.g. `postgresql://user:pass@localhost:5432/econocausal`
- Optional: Docker and `docker-compose` if using the provided `docker-compose.yml`.

Files
- `contracts/customer_dataset.schema.json`: frozen v1 customer import contract
- `backend/schema.sql`: canonical DDL for customers, campaigns, model runs, predictions, and recommendations
- `backend/migrations/`: additive upgrades for existing databases
- `backend/seed.sql`: idempotent smoke-test campaign and customer rows
- `backend/views.sql`: useful views for dashboards
- `backend/indexes.sql`: recommended index DDL
- `backend/scripts/load_data.py`: batched, structured-logging bulk loader (CSV or JSON -> Postgres)
- `backend/scripts/validate_db.py`: validation checks against DB
- `backend/scripts/export_data.py`: export customers table to CSV/JSON

Quick setup (local Postgres)
1. Generate production data CSV (if missing):
```
python3 scripts/generate_data.py --customers 100000 --seed 42 --treatment-rate 0.35
```
2. Ensure `DATABASE_URL` is set, then run the setup helper:
```
export DATABASE_URL=postgresql://user:pass@localhost:5432/econocausal
./scripts/setup_db.sh
```

The command may be safely rerun: seed rows are upserted and customer imports
upsert by `customer_id`. It applies schema, migrations, views, and indexes.

Replace all database data with the seed rows and an input dataset:

```
DATASET_PATH=data/demo_customers.csv BATCH_SIZE=1000 ./scripts/refresh_db.sh
```

`data/demo_customers.csv` is a demo fixture, while `data/test_customers.csv`
and `data/test_customers.json` are minimal test fixtures. The large
`data/customers.csv` remains the production-size synthetic dataset.

Import JSON directly:

```
python3 backend/scripts/load_data.py --input data/test_customers.json --batch-size 2
```

Run validations
```
python3 backend/scripts/validate_db.py
```

Export data
```
python3 backend/scripts/export_data.py --dataset model-input --format csv --out data/model_input.csv
python3 backend/scripts/export_data.py --dataset dashboard --format csv --out data/dashboard.csv
```

`model-input` contains causal-model features, treatment, and outcome. The
`dashboard` export adds latest stored prediction and recommendation fields.

Notes
- `scripts/setup_db.sh` uses `psql` to apply schema, migrations, seed data, views, and indexes before running the loader. If you prefer a containerized setup, use `docker-compose.yml`.
- The export script uses `COPY` for CSV exports for performance.
