from __future__ import annotations

from ..repositories import get_customer_repository


def load_customer_data():
    return get_customer_repository().dataframe()


def build_summary() -> dict:
    return get_customer_repository().summary()


def get_customer_by_id(customer_id: int) -> dict | None:
    return get_customer_repository().get_customer(customer_id)


def list_customers(*, offset: int, limit: int, segment: str | None, search: str | None) -> tuple[list[dict], int]:
    return get_customer_repository().list_customers(offset=offset, limit=limit, segment=segment, search=search)
