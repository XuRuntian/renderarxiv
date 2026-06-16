from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Optional, List

from renderpapers.models import Paper

if TYPE_CHECKING:
    from renderpapers.query import StructuredQuery


class PaperSearchError(RuntimeError):
    """Raised when a paper source cannot complete a search."""


class PaperSource(Protocol):
    name: str

    def search(
        self,
        query: str,
        max_results: int = 50,
        sort_by: str = "relevance",
        sort_order: str = "descending",
        category: Optional[str] = None,
        venues: Optional[List[str]] = None,
        days_limit: Optional[int] = None,
        use_cache: bool = True,
        cache_ttl_hours: float = 24,
        retry_on_rate_limit: bool = False,
        rate_limit_retries: int = 1,
        retry_wait_seconds: float = 30,
        structured_query: StructuredQuery | None = None,
    ) -> List[Paper]:
        ...

    def fetch_one(
        self,
        identifier: str,
        use_cache: bool = True,
        cache_ttl_hours: float = 24,
        retry_on_rate_limit: bool = False,
        rate_limit_retries: int = 1,
        retry_wait_seconds: float = 30,
    ) -> Optional[Paper]:
        ...
