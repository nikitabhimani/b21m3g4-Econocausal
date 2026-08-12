import os
from pathlib import Path


def test_customers_csv_exists_and_nonempty():
    csv_path = Path("data") / "customers.csv"
    assert csv_path.exists(), f"Expected {csv_path} to exist"
    assert csv_path.stat().st_size > 0, "customers.csv appears empty"


def test_schema_contains_customers_table():
    schema_path = Path("backend") / "schema.sql"
    assert schema_path.exists(), "backend/schema.sql missing"
    content = schema_path.read_text(encoding="utf-8").lower()
    assert "create table" in content and "customers" in content, "schema.sql should define customers table"
