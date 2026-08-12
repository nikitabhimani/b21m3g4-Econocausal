# EconoCausal

EconoCausal is an end-to-end causal customer-behavior and discount-optimization platform. It includes a synthetic customer-data generator, PostgreSQL data layer, an interactive causal machine learning pipeline, a FastAPI backend, and a Next.js dashboard.

---

## Repository Layout

- `causal_ml/` — Causal machine learning pipeline (config, preprocessing, estimators, train/predict/diagnostics scripts)
- `data/` — Generated customer data and its summary
- `outputs/` — Causal model artifacts (`model.joblib`), target predictions (`causal_predictions.csv`), performance summaries, and training metadata history
- `backend/` — Database SQL, data utilities, and FastAPI application
- `frontend/` — Next.js dashboard
- `scripts/generate_data.py` — Reproducible synthetic-data generator
- `docs/database.md` — Detailed database notes

---

## Prerequisites

- Python 3.8+
- Node.js and npm
- PostgreSQL 15+ or Docker Compose

Install the Python dependencies:

```bash
python3 -m pip install -r backend/requirements.txt
```

---

## Causal Machine Learning Pipeline

EconoCausal features an integrated Causal ML pipeline supporting **T-Learner**, **X-Learner**, and **Double Machine Learning (DML)** models using `scikit-learn` and `econml`.

### 1. Configure hyperparameters
Tune feature sets, estimator details, and tree parameters inside [`causal_ml/config.yaml`](file:///c:/Users/Acer-Nitro/Desktop/experience/ds/causal_ml/config.yaml):
```yaml
model:
  type: "t_learner"  # Options: t_learner, x_learner, dml
  base_estimator: "gradient_boosting"  # Options: gradient_boosting, random_forest, linear
  seed: 42
  hyperparameters:
    n_estimators: 100
    max_depth: 4
    min_samples_split: 10
    learning_rate: 0.1
```

### 2. Preprocess and train model
Preprocess features, run class imbalance checks, and serialize the trained pipeline:
```bash
python causal_ml/train.py
```

### 3. Run predictions
Generate baseline probabilities, treated probabilities, and predicted individual treatment effects (ITE) for customers:
```bash
python causal_ml/predict.py
```

### 4. Execute diagnostics
Compute precision metrics (MAE, RMSE, correlation), evaluate Qini targeting coefficient curves, and write registries:
```bash
python causal_ml/diagnostics.py
```

---

## Database Setup

Start PostgreSQL with Docker Compose, if needed:

```bash
docker compose up -d db
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/econocausal
```

Then apply the schema, seed rows, and customer CSV:

```bash
./scripts/setup_db.sh
```

Apply the supplementary indexes and summary views:

```bash
psql "$DATABASE_URL" -f backend/indexes.sql
psql "$DATABASE_URL" -f backend/views.sql
```

Validate the loaded data:

```bash
python3 backend/scripts/validate_db.py
```

Export customers for downstream use:

```bash
python3 backend/scripts/export_data.py --format csv --out data/customers_export.csv
python3 backend/scripts/export_data.py --format json --out data/customers_export.json
```

See [the database guide](docs/database.md) for local PostgreSQL setup and command details.

---

## Run the Application

Start the FastAPI development server:

```bash
uvicorn backend.app.main:app --reload --port 8001
```

Start the Next.js dashboard in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Service Ports

- Backend API: `http://127.0.0.1:8001/api`
- Frontend dashboard: `http://localhost:3000`

---

## API Endpoints

- `GET  /api/health` — service health status
- `GET  /api/summary` — customer counts, conversions, and revenue
- `GET  /api/customers/{customer_id}` — a detailed customer record
- `GET  /api/causal/summary` — causal-model summary metrics (MAE, Qini, etc.)
- `GET  /api/causal/ite` — customer records ranked by predicted uplift
- `GET  /api/recommendations` — budget-optimised target discount recommendations
- `POST /api/causal/retrain` — triggers causal model retraining, updates config, and refreshes metrics dynamically
