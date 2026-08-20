"""Run the reproducible causal pipeline from the repository root."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STEPS = (
    ROOT / "causal_ml" / "train.py",
    ROOT / "causal_ml" / "predict.py",
    ROOT / "causal_ml" / "diagnostics.py",
    ROOT / "causal_ml" / "refutation_tests.py",
)


def main() -> None:
    for step in STEPS:
        subprocess.run([sys.executable, str(step)], cwd=ROOT, check=True)
    print("Causal pipeline completed successfully.")


if __name__ == "__main__":
    main()
