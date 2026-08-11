from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Econocausal API",
    description="Causal uplift and discount optimization service",
    version="0.1.0",
)

app.include_router(router)
