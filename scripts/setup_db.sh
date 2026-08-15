#!/usr/bin/env bash
set -euo pipefail

# Idempotently apply the complete database foundation. Use --refresh to replace
# all data with the seed rows and the configured customer dataset.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REFRESH=false

if [[ "${1:-}" == "--refresh" ]]; then
  REFRESH=true
elif [[ $# -gt 0 ]]; then
  echo "Usage: $0 [--refresh]" >&2
  exit 2
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: Set DATABASE_URL, e.g. postgresql://user:pass@localhost:5432/econocausal" >&2
  exit 2
fi

apply_sql() {
  psql -v ON_ERROR_STOP=1 "$DATABASE_URL" -f "$1"
}

apply_sql "$ROOT_DIR/backend/schema.sql"
for migration in "$ROOT_DIR"/backend/migrations/*.sql; do
  apply_sql "$migration"
done

if [[ "$REFRESH" == true ]]; then
  echo "Refreshing database data"
  psql -v ON_ERROR_STOP=1 "$DATABASE_URL" -c 'TRUNCATE TABLE recommendations, predictions, customers, model_runs, campaigns RESTART IDENTITY CASCADE'
fi

apply_sql "$ROOT_DIR/backend/seed.sql"
apply_sql "$ROOT_DIR/backend/views.sql"
apply_sql "$ROOT_DIR/backend/indexes.sql"

echo "Loading ${DATASET_PATH:-$ROOT_DIR/data/customers.csv}"
python3 "$ROOT_DIR/backend/scripts/load_data.py" --input "${DATASET_PATH:-$ROOT_DIR/data/customers.csv}" --batch-size "${BATCH_SIZE:-5000}"
echo "Database setup complete."
