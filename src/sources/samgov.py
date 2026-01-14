"""SAM.gov Contract Opportunities API source integration.

Uses the official SAM.gov Opportunities API:
https://open.gsa.gov/api/opportunities-api/

Requires SAM_GOV_API_KEY environment variable.
Get your free API key from: https://beta.sam.gov/
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import httpx

from ..models import (
    Opportunity, OpportunityBatch, Source, Client, BudgetType
)
from ..config import settings
from .base import BaseSource

logger = logging.getLogger(__name__)

# SAM.gov API constants
SAM_API_BASE = "https://api.sam.gov/opportunities/v2/search"

# Set-aside codes - SDVOSB is priority!
SET_ASIDE_CODES = {
    "SDVOSB": "Service-Disabled Veteran-Owned Small Business",
    "VOSB": "Veteran-Owned Small Business", 
    "SBA": "Small Business Set-Aside",
    "8A": "8(a) Set-Aside",
    "HUBZone": "HUBZone Set-Aside",
    "WOSB": "Women-Owned Small Business",
    "EDWOSB": "Economically Disadvantaged WOSB",
}


class SAMGovSource(BaseSource):
    """Fetches federal contract opportunities from SAM.gov.

    Requires SAM_GOV_API_KEY environment variable to be set.
    Get your key from: https://beta.sam.gov/ (Account -> API Keys)
    """

    def __init__(self):
        self._client = None

    @property
    def source_type(self) -> Source:
        return Source.SAM_GOV

    @property
    def name(self) -> str:
        return "SAM.gov"

    def is_configured(self) -> bool:
        """Check if API key is present."""
        return bool(settings.sam_gov_api_key)

    def _get_client(self) -> httpx.AsyncClient:
        """Lazily create HTTP client."""
        if self._client is None:
            if not self.is_configured():
                raise ValueError(
                    "SAM.gov not configured. "
                    "Set SAM_GOV_API_KEY in .env file."
                )
            self._client = httpx.AsyncClient(
                headers={
                    "X-Api-Key": settings.sam_gov_api_key,
                    "Accept": "application/json",
                },
                timeout=30.0
            )
        return self._client

    async def fetch_opportunities(
        self,
        keywords: Optional[list[str]] = None,
        min_budget: Optional[float] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
        # SAM.gov specific filters
        naics_codes: Optional[list[str]] = None,
        set_aside_types: Optional[list[str]] = None,
        posted_from: Optional[datetime] = None,
        response_deadline_from: Optional[datetime] = None,
    ) -> OpportunityBatch:
        """Fetch contract opportunities from SAM.gov.

        Args:
            keywords: Search terms for title/description
            min_budget: Not directly supported, filtered post-fetch
            limit: Max results (API max is 1000)
            cursor: Page offset (as string number)
            naics_codes: Filter by NAICS codes (e.g., ["541611", "541618"])
            set_aside_types: Filter by set-aside (e.g., ["SDVOSB", "SBA"])
            posted_from: Only opportunities posted after this date
            response_deadline_from: Only open opportunities

        Returns:
            OpportunityBatch with normalized opportunities
        """
        try:
            client = self._get_client()

            # Build query parameters
            params = {
                "limit": min(limit, 1000),
                "api_key": settings.sam_gov_api_key,
                "postedFrom": (posted_from or datetime.now() - timedelta(days=30)).strftime("%m/%d/%Y"),
                "active": "true",  # Only active opportunities
            }

            # Add pagination offset
            if cursor:
                params["offset"] = int(cursor)

            # Add keyword search
            if keywords:
                params["q"] = " OR ".join(keywords)

            # Add NAICS filter (use configured defaults if not specified)
            naics = naics_codes or settings.sam_gov_naics_codes
            if naics:
                params["ncode"] = ",".join(naics)

            # Add set-aside filter (default to SDVOSB-relevant)
            set_asides = set_aside_types or settings.sam_gov_set_asides
            if set_asides:
                params["typeOfSetAside"] = ",".join(set_asides)

            logger.info(f"Fetching from SAM.gov with params: {params}")

            response = await client.get(SAM_API_BASE, params=params)
            response.raise_for_status()
            data = response.json()

            opportunities = []
            for opp in data.get("opportunitiesData", []):
                try:
                    normalized = self._normalize_opportunity(opp)
                    if normalized:
                        # Apply min_budget filter if specified
                        if min_budget and normalized.budget_max:
                            if normalized.budget_max < min_budget:
                                continue
                        opportunities.append(normalized)
                except Exception as e:
                    logger.warning(f"Failed to normalize opportunity {opp.get('noticeId')}: {e}")

            # Calculate next cursor
            total_records = data.get("totalRecords", 0)
            current_offset = int(cursor or 0)
            next_cursor = None
            if current_offset + limit < total_records:
                next_cursor = str(current_offset + limit)

            logger.info(f"Fetched {len(opportunities)} opportunities from SAM.gov")

            return OpportunityBatch(
                source=Source.SAM_GOV,
                opportunities=opportunities,
                next_cursor=next_cursor
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"SAM.gov API error: {e.response.status_code} - {e.response.text}")
            return OpportunityBatch(
                source=Source.SAM_GOV,
                opportunities=[],
                error=f"API error: {e.response.status_code}"
            )
        except Exception as e:
            logger.error(f"SAM.gov fetch failed: {e}")
            return OpportunityBatch(
                source=Source.SAM_GOV,
                opportunities=[],
                error=str(e)
            )

    def _normalize_opportunity(self, raw: dict) -> Optional[Opportunity]:
        """Convert SAM.gov API response to Opportunity model."""
        notice_id = raw.get("noticeId")
        if not notice_id:
            return None

        # Parse dates
        posted_at = self._parse_date(raw.get("postedDate"))
        if not posted_at:
            posted_at = datetime.now()

        # Extract budget/award info if available
        budget_min = None
        budget_max = None
        award_info = raw.get("award", {})
        if award_info:
            budget_max = award_info.get("amount")
            budget_min = award_info.get("amount")

        # Build description with key details
        description_parts = [
            raw.get("description", ""),
            f"\n\n**Set-Aside:** {raw.get('typeOfSetAsideDescription', 'None')}",
            f"**NAICS:** {raw.get('naicsCode', 'N/A')}",
            f"**Response Deadline:** {raw.get('responseDeadLine', 'See solicitation')}",
        ]

        # Create client/agency info
        agency = Client(
            id=raw.get("organizationId", notice_id),
            username=raw.get("fullParentPathName", raw.get("organizationName", "Unknown Agency")),
            location=raw.get("officeAddress", {}).get("state") if raw.get("officeAddress") else None,
        )

        # Build URL to opportunity
        url = f"https://sam.gov/opp/{notice_id}/view"

        return Opportunity(
            id=notice_id,
            source=Source.SAM_GOV,
            url=url,
            title=raw.get("title", "Untitled"),
            description="\n".join(description_parts),
            skills=self._extract_skills(raw),
            budget_type=BudgetType.FIXED,
            budget_min=budget_min,
            budget_max=budget_max,
            client=agency,
            posted_at=posted_at,
        )

    def _extract_skills(self, raw: dict) -> list[str]:
        """Extract relevant tags/skills from opportunity."""
        skills = []

        # Add NAICS code as skill
        if raw.get("naicsCode"):
            skills.append(f"NAICS:{raw['naicsCode']}")

        # Add set-aside type
        if raw.get("typeOfSetAside"):
            skills.append(raw["typeOfSetAside"])

        # Add contract type
        if raw.get("type"):
            skills.append(raw["type"])

        # Add classification
        if raw.get("classificationCode"):
            skills.append(f"PSC:{raw['classificationCode']}")

        return skills

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse SAM.gov date formats."""
        if not date_str:
            return None

        # SAM.gov uses various formats
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%m/%d/%Y",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.replace("Z", "+00:00"), fmt)
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
