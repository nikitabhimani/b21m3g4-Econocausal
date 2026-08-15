#!/usr/bin/env bash
set -euo pipefail

# Repeatable replacement of all database data using seed.sql and DATASET_PATH.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT_DIR/scripts/setup_db.sh" --refresh
