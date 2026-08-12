import importlib.util
from pathlib import Path


def test_validate_script_present():
    path = Path("backend") / "scripts" / "validate_db.py"
    assert path.exists(), "validate_db.py should exist"


def test_export_script_present():
    path = Path("backend") / "scripts" / "export_data.py"
    assert path.exists(), "export_data.py should exist"
