"""Run the reproducible causal pipeline from the repository root."""
from __future__ import annotations

import subprocess
import sys
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STEPS = (
    ROOT / "causal_ml" / "train.py",
    ROOT / "causal_ml" / "predict.py",
    ROOT / "causal_ml" / "diagnostics.py",
    ROOT / "causal_ml" / "refutation_tests.py",
    ROOT / "scripts" / "generate_uplift_outputs.py",
)

OUTPUTS = ROOT / "outputs"
MANIFEST = OUTPUTS / "artifact_manifest.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    environment = os.environ.copy()
    environment["PIPELINE_RUN_ID"] = run_id
    for step in STEPS:
        subprocess.run([sys.executable, str(step)], cwd=ROOT, env=environment, check=True)

    artifact_names = (
        "model.joblib",
        "model_meta.json",
        "causal_predictions.csv",
        "causal_summary.json",
        "uplift_results.json",
        "recommendations.json",
        "scenario_comparison.json",
        "refutation_report.json",
    )
    manifest = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": {
            name: {"sha256": _sha256(OUTPUTS / name), "bytes": (OUTPUTS / name).stat().st_size}
            for name in artifact_names
            if (OUTPUTS / name).exists()
        },
    }
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Causal pipeline completed successfully. Artifact run: {run_id}")


if __name__ == "__main__":
    main()
