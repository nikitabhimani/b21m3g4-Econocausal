# EconoCausal

Causal Customer Behavior & Discount Optimization platform. This repository contains the synthetic data generator, the FastAPI backend, and the Next.js mock dashboard.

## Quick Start

### 1. Generate the Data
Ensure you have the required Python dependencies installed, then run the generator:
```bash
python -m scripts.generate_data
```

### 2. Run the Backend API
Run the FastAPI development server on port `8001` (to prevent IPv6 loopback binding conflicts on port 8000):
```bash
uvicorn backend.app.main:app --reload --port 8001
```

### 3. Run the Frontend Mock Dashboard
Start the Next.js client-side application:
```bash
cd frontend
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your web browser.

## Service Ports

- **Backend API**: `http://127.0.0.1:8001/api`
- **Frontend Dashboard**: `http://localhost:3000`

## API Endpoints

- `/api/health` - Service health status
- `/api/summary` - General customer metrics (conversions, counts, revenue)
- `/api/customers/{customer_id}` - Details of a single customer
- `/api/causal/summary` - Summary metrics of Causal ML (ATE, share of persuadables)
- `/api/causal/ite` - Top customers ranked by Individual Treatment Effect (ITE)
- `/api/recommendations` - Target customer lists optimized under a campaign budget
