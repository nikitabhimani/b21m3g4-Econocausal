import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_loader_module():
    spec = importlib.util.spec_from_file_location("load_data", ROOT / "backend" / "scripts" / "load_data.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_contract_matches_loader_required_columns():
    contract = json.loads((ROOT / "contracts" / "customer_dataset.schema.json").read_text())
    loader = load_loader_module()
    assert set(loader.REQUIRED_COLUMNS) == set(contract["required"])


def test_json_fixture_loads_and_batches():
    loader = load_loader_module()
    rows = list(loader.read_rows(ROOT / "data" / "test_customers.json", "json"))
    assert len(rows) == 3
    assert [len(batch) for batch in loader.batches(rows, 2)] == [2, 1]


def test_all_database_artifacts_are_wired_into_setup():
    setup = (ROOT / "scripts" / "setup_db.sh").read_text()
    assert "migrations" in setup and "views.sql" in setup and "indexes.sql" in setup
    schema = (ROOT / "backend" / "schema.sql").read_text().lower()
    for table in ("customers", "campaigns", "model_runs", "predictions", "recommendations"):
        assert f"create table if not exists {table}" in schema
    views = (ROOT / "backend" / "views.sql").read_text().lower()
    assert "campaign_summary" in views and "treatment_summary" in views


def test_dedicated_fixture_and_export_definitions_exist():
    assert (ROOT / "data" / "demo_customers.csv").exists()
    assert (ROOT / "data" / "test_customers.csv").exists()
    export_source = (ROOT / "backend" / "scripts" / "export_data.py").read_text()
    assert '"model-input"' in export_source and '"dashboard"' in export_source
