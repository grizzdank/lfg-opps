"""Upwork opportunity source integration (stub).

This is a placeholder implementation. Full integration requires:
1. Apply for Upwork API access: https://support.upwork.com/hc/en-us/articles/115015857647
2. Wait for approval (~2 weeks)
3. Implement OAuth 2.0 flow
4. Use GraphQL API for job search

Upwork API Documentation: https://www.upwork.com/developer/documentation/graphql/api/docs/index.html
"""

import logging
from typing import Optional
from datetime import datetime

from ..models import Opportunity, OpportunityBatch, Source, Client, BudgetType
from ..config import settings
from .base import BaseSource

logger = logging.getLogger(__name__)


class UpworkSource(BaseSource):
    """Upwork opportunity source.

    STATUS: Awaiting API approval

    To enable:
    1. Apply for API key at Upwork Developer portal
    2. Set UPWORK_CLIENT_ID, UPWORK_CLIENT_SECRET, UPWORK_ACCESS_TOKEN in .env
    3. Complete the OAuth flow implementation below
    """

    def __init__(self):
        self._client = None

    @property
    def source_type(self) -> Source:
        return Source.UPWORK

    @property
    def name(self) -> str:
        return "Upwork"

    def is_configured(self) -> bool:
        """Check if Upwork credentials are configured."""
        return bool(
            settings.upwork_client_id and
            settings.upwork_client_secret and
            settings.upwork_access_token
        )

    async def fetch_opportunities(
        self,
        keywords: Optional[list[str]] = None,
        min_budget: Optional[float] = None,
        limit: int = 50,
        cursor: Optional[str] = None
    ) -> OpportunityBatch:
        """Fetch job opportunities from Upwork.

        NOTE: This is a stub implementation. Full implementation pending API approval.
        """
        if not self.is_configured():
            logger.warning(
                "Upwork not configured. Apply for API access at: "
                "https://support.upwork.com/hc/en-us/articles/115015857647"
            )
            return OpportunityBatch(
                source=Source.UPWORK,
                opportunities=[],
                error="Upwork API not configured. Awaiting API approval."
            )

        # TODO: Implement once API access is approved
        # The implementation will use Upwork's GraphQL API:
        #
        # query {
        #   marketplaceJobPostings(
        #     searchParameters: {
        #       query: "AI automation MVP"
        #       budgetMin: 2500
        #       sortBy: RECENCY
        #     }
        #     first: 50
        #   ) {
        #     edges {
        #       node {
        #         id
        #         title
        #         description
        #         budget { amount currency }
        #         client { ... }
        #       }
        #     }
        #   }
        # }

        logger.info("Upwork integration not yet implemented")
        return OpportunityBatch(
            source=Source.UPWORK,
            opportunities=[],
            error="Upwork integration pending. See upwork.py for implementation notes."
        )

    def _normalize_job(self, job: dict) -> Opportunity:
        """Convert Upwork job posting to normalized Opportunity.

        Placeholder for when API is available.
        """
        # This will be implemented once we have actual API response format
        raise NotImplementedError("Upwork normalization pending API access")


# Instructions for completing the integration
IMPLEMENTATION_NOTES = """
## Upwork API Integration Checklist

### 1. Apply for API Access
- Go to: https://support.upwork.com/hc/en-us/articles/115015857647
- Use LFG Consultants company profile
- Describe use case: "Internal tool to monitor relevant consulting opportunities"
- Expected approval time: ~2 weeks

### 2. OAuth 2.0 Setup
After approval, you'll receive:
- Client ID (UPWORK_CLIENT_ID)
- Client Secret (UPWORK_CLIENT_SECRET)

You'll need to implement the OAuth flow to get an access token:
1. Redirect user to Upwork authorization URL
2. User grants permission
3. Exchange auth code for access token
4. Store and refresh token as needed

### 3. GraphQL API
Upwork uses GraphQL. Key endpoints:
- Job search: marketplaceJobPostings
- Job details: jobPosting(id: "...")
- Client info: client(id: "...")

### 4. Rate Limits
- 40,000 requests/day
- Implement exponential backoff
- Cache results to minimize API calls

### 5. Environment Variables
Add to .env:
UPWORK_CLIENT_ID=your_client_id
UPWORK_CLIENT_SECRET=your_client_secret
UPWORK_ACCESS_TOKEN=your_access_token
"""


if __name__ == "__main__":
    print(IMPLEMENTATION_NOTES)
