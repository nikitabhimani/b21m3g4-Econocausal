# Database setup and data loading

This document explains how to create the PostgreSQL database, apply the schema, seed data, load the generated CSV, and run validations.

Prerequisites
- `psql` client available
- Python 3.8+
- `DATABASE_URL` environment variable set to a Postgres DSN, e.g. `postgresql://user:pass@localhost:5432/econocausal`
- Optional: Docker and `docker-compose` if using the provided `docker-compose.yml`.

Files
- `backend/schema.sql`: DDL for tables
- `backend/seed.sql`: small seed rows for smoke tests
- `backend/views.sql`: useful views for dashboards
- `backend/indexes.sql`: recommended index DDL
- `backend/scripts/load_data.py`: bulk loader (CSV -> Postgres)
- `backend/scripts/validate_db.py`: validation checks against DB
- `backend/scripts/export_data.py`: export customers table to CSV/JSON

Quick setup (local Postgres)
1. Generate data CSV (if missing):
```
python3 scripts/generate_data.py --customers 100000 --seed 42 --treatment-rate 0.35
```
2. Ensure `DATABASE_URL` is set, then run the setup helper:
```
export DATABASE_URL=postgresql://user:pass@localhost:5432/econocausal
./scripts/setup_db.sh
```

Run validations
```
python3 backend/scripts/validate_db.py
```

Export data
```
python3 backend/scripts/export_data.py --format csv --out data/customers_export.csv
```

Notes
- `scripts/setup_db.sh` uses `psql` to apply `backend/schema.sql` and `backend/seed.sql`, then runs the Python loader. If you prefer a containerized setup, use `docker-compose.yml`.
- The export script uses `COPY` for CSV exports for performance.
