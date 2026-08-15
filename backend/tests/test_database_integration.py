"""Live PostgreSQL checks. Run with DATABASE_URL set; otherwise pytest skips it."""
import os
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
DATABASE_URL = os.environ.get("DATABASE_URL")


@pytest.mark.skipif(not DATABASE_URL, reason="DATABASE_URL is required for live PostgreSQL integration checks")
def test_setup_refresh_views_validation_and_exports(tmp_path):
    env = {**os.environ, "DATABASE_URL": DATABASE_URL, "DATASET_PATH": str(ROOT / "data" / "test_customers.csv"), "BATCH_SIZE": "2"}
    subprocess.run([str(ROOT / "scripts" / "refresh_db.sh")], cwd=ROOT, env=env, check=True)
    subprocess.run([str(ROOT / "scripts" / "setup_db.sh")], cwd=ROOT, env=env, check=True)
    subprocess.run(
        ["python3", "backend/scripts/load_data.py", "--input", "data/test_customers.json", "--batch-size", "2"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    subprocess.run(["python3", "backend/scripts/validate_db.py"], cwd=ROOT, env=env, check=True)
    subprocess.run(["python3", "backend/scripts/export_data.py", "--dataset", "model-input", "--out", str(tmp_path / "model.csv")], cwd=ROOT, env=env, check=True)
    subprocess.run(["python3", "backend/scripts/export_data.py", "--dataset", "dashboard", "--out", str(tmp_path / "dashboard.csv")], cwd=ROOT, env=env, check=True)
    assert (tmp_path / "model.csv").stat().st_size > 0
    assert (tmp_path / "dashboard.csv").stat().st_size > 0
