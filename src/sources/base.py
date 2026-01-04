"""Abstract base class for opportunity sources."""

from abc import ABC, abstractmethod
from typing import Optional

from ..models import OpportunityBatch, Source


class BaseSource(ABC):
    """Abstract base class for all opportunity sources.

    Each platform (Freelancer, Upwork, etc.) implements this interface
    to provide a consistent way to fetch and normalize opportunities.
    """

    @property
    @abstractmethod
    def source_type(self) -> Source:
        """Return the source enum for this provider."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this source."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if this source has valid credentials configured."""
        pass

    @abstractmethod
    async def fetch_opportunities(
        self,
        keywords: Optional[list[str]] = None,
        min_budget: Optional[float] = None,
        limit: int = 50,
        cursor: Optional[str] = None
    ) -> OpportunityBatch:
        """Fetch opportunities from this source.

        Args:
            keywords: Optional list of keywords to search for
            min_budget: Minimum budget threshold (if supported by API)
            limit: Maximum number of results to return
            cursor: Pagination cursor from previous request

        Returns:
            OpportunityBatch containing normalized opportunities
        """
        pass

    def __repr__(self) -> str:
        configured = "✓" if self.is_configured() else "✗"
        return f"<{self.name} [{configured}]>"
