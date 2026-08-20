from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

import pandas as pd

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ModuleNotFoundError:  # Keeps file-mode tooling usable without PostgreSQL extras.
    psycopg2 = None
    RealDictCursor = None


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CUSTOMER_PATH = PROJECT_ROOT / "data" / "customers.csv"


class CustomerRepository(Protocol):
    def dataframe(self) -> pd.DataFrame: ...
    def list_customers(self, *, offset: int, limit: int, segment: str | None, search: str | None) -> tuple[list[dict], int]: ...
    def get_customer(self, customer_id: int) -> dict | None: ...
    def summary(self) -> dict: ...


class FileCustomerRepository:
    def dataframe(self) -> pd.DataFrame:
        return pd.read_csv(CUSTOMER_PATH)

    def list_customers(self, *, offset: int, limit: int, segment: str | None, search: str | None) -> tuple[list[dict], int]:
        df = self.dataframe()
        if segment:
            df = df[df["customer_segment"] == segment]
        if search:
            df = df[df["customer_id"].astype(str).str.contains(search, regex=False)]
        total = len(df)
        return df.sort_values("customer_id").iloc[offset : offset + limit].to_dict(orient="records"), total

    def get_customer(self, customer_id: int) -> dict | None:
        row = self.dataframe().loc[lambda data: data["customer_id"] == customer_id]
        return None if row.empty else row.iloc[0].to_dict()

    def summary(self) -> dict:
        return _summary_from_frame(self.dataframe())


class PostgresCustomerRepository:
    def __init__(self, database_url: str):
        if psycopg2 is None:
            raise RuntimeError("psycopg2-binary is required for PostgreSQL API mode.")
        self.database_url = database_url

    def _query(self, statement: str, params: tuple = ()) -> list[dict]:
        with psycopg2.connect(self.database_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(statement, params)
                return [dict(row) for row in cur.fetchall()]

    def dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self._query("SELECT * FROM customers ORDER BY customer_id"))

    def list_customers(self, *, offset: int, limit: int, segment: str | None, search: str | None) -> tuple[list[dict], int]:
        clauses, params = [], []
        if segment:
            clauses.append("customer_segment = %s")
            params.append(segment)
        if search:
            clauses.append("customer_id::text LIKE %s")
            params.append(f"%{search}%")
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        total = self._query(f"SELECT COUNT(*) AS total FROM customers{where}", tuple(params))[0]["total"]
        rows = self._query(
            f"SELECT * FROM customers{where} ORDER BY customer_id OFFSET %s LIMIT %s",
            tuple(params + [offset, limit]),
        )
        return rows, int(total)

    def get_customer(self, customer_id: int) -> dict | None:
        rows = self._query("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))
        return rows[0] if rows else None

    def summary(self) -> dict:
        rows = self._query("SELECT * FROM customer_summary")
        if not rows:
            return _summary_from_frame(self.dataframe())
        return {key: _native(value) for key, value in rows[0].items()}


def _native(value):
    return value.item() if hasattr(value, "item") else value


def _summary_from_frame(df: pd.DataFrame) -> dict:
    return {
        "customers": int(len(df)),
        "treated_customers": int((df["treatment_received"] == 1).sum()),
        "control_customers": int((df["treatment_received"] == 0).sum()),
        "treatment_rate": float(df["treatment_received"].mean()),
        "purchase_rate": float(df["purchase"].mean()),
        "average_true_ite": float(df["true_ite"].mean()),
        "total_revenue": float(df["purchase_value"].sum()),
        "total_discount_cost": float(df["discount_cost"].sum()),
    }


def get_customer_repository() -> CustomerRepository:
    database_url = os.environ.get("DATABASE_URL")
    return PostgresCustomerRepository(database_url) if database_url else FileCustomerRepository()
