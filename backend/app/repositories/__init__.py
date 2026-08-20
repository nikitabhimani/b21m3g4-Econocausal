"""Runtime data sources for the API.

PostgreSQL is selected when DATABASE_URL is configured; local CSV/JSON files
remain an intentional development fallback.
"""

from .artifacts import ArtifactRepository
from .customers import CustomerRepository, get_customer_repository

__all__ = ["ArtifactRepository", "CustomerRepository", "get_customer_repository"]
