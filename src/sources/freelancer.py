"""Freelancer.com opportunity source integration.

Uses the official Freelancer SDK: https://github.com/freelancer/freelancer-sdk-python
"""

import os
from datetime import datetime
from typing import Optional
import logging

from ..models import (
    Opportunity, OpportunityBatch, Source, Client, BudgetType
)
from ..config import settings
from .base import BaseSource

logger = logging.getLogger(__name__)


class FreelancerSource(BaseSource):
    """Fetches opportunities from Freelancer.com using their official SDK.

    Requires FLN_OAUTH_TOKEN environment variable to be set.
    Get your token from: https://developers.freelancer.com/
    """

    def __init__(self):
        self._session = None

    @property
    def source_type(self) -> Source:
        return Source.FREELANCER

    @property
    def name(self) -> str:
        return "Freelancer.com"

    def is_configured(self) -> bool:
        """Check if OAuth token is present."""
        return bool(settings.fln_oauth_token)

    def _get_session(self):
        """Lazily create SDK session."""
        if self._session is None:
            if not self.is_configured():
                raise ValueError(
                    "Freelancer.com not configured. "
                    "Set FLN_OAUTH_TOKEN in .env file."
                )
            # Import SDK only when needed
            from freelancersdk.session import Session
            self._session = Session(
                oauth_token=settings.fln_oauth_token,
                url=settings.fln_url
            )
        return self._session

    async def fetch_opportunities(
        self,
        keywords: Optional[list[str]] = None,
        min_budget: Optional[float] = None,
        max_budget: Optional[float] = 2500,
        limit: int = 50,
        cursor: Optional[str] = None
    ) -> OpportunityBatch:
        """Fetch projects from Freelancer.com.

        Args:
            keywords: Search terms (will be OR'd together)
            min_budget: Minimum budget filter
            max_budget: Maximum budget filter (default: $2500 for short projects)
            limit: Max results (API max is 100)
            cursor: Offset for pagination (as string)

        Returns:
            OpportunityBatch with normalized opportunities
        """
        try:
            from freelancersdk.resources.projects import (
                search_projects,
                create_search_projects_filter
            )
            from freelancersdk.exceptions import ProjectsNotFoundException

            session = self._get_session()

            # Build search query
            query = " OR ".join(keywords) if keywords else "AI automation MVP"

            # Build filter
            search_filter = create_search_projects_filter(
                sort_field="time_submitted",
                or_search_query=True
            )

            # Add budget filters if supported
            if min_budget:
                search_filter["min_avg_price"] = min_budget
            if max_budget:
                search_filter["max_avg_price"] = max_budget

            # Parse cursor to offset
            offset = int(cursor) if cursor else 0

            # Request extra fields
            project_details = {
                "full_description": True,
                "jobs": True,  # Skills/categories
            }
            user_details = {
                "employer_reputation": True,
                "employer_reputation_extra": True,
                "status": True,
            }

            logger.info(f"Searching Freelancer.com: '{query}' (offset={offset}, max_budget=${max_budget})")

            result = search_projects(
                session=session,
                query=query,
                search_filter=search_filter,
                project_details=project_details,
                user_details=user_details,
                limit=min(limit, 100),  # API max
                offset=offset,
                active_only=True
            )

            if not result or "projects" not in result:
                return OpportunityBatch(
                    source=Source.FREELANCER,
                    opportunities=[],
                    next_cursor=None
                )

            # Normalize projects to Opportunity model
            opportunities = []
            for proj in result.get("projects", []):
                try:
                    opp = self._normalize_project(proj, result.get("users", {}))
                    opportunities.append(opp)
                except Exception as e:
                    logger.warning(f"Failed to normalize project {proj.get('id')}: {e}")

            # Calculate next cursor
            next_cursor = None
            if len(opportunities) == limit:
                next_cursor = str(offset + limit)

            logger.info(f"Fetched {len(opportunities)} opportunities from Freelancer.com")

            return OpportunityBatch(
                source=Source.FREELANCER,
                opportunities=opportunities,
                next_cursor=next_cursor
            )

        except ProjectsNotFoundException:
            logger.info("No projects found matching criteria")
            return OpportunityBatch(
                source=Source.FREELANCER,
                opportunities=[],
                next_cursor=None
            )
        except Exception as e:
            logger.error(f"Freelancer.com API error: {e}")
            return OpportunityBatch(
                source=Source.FREELANCER,
                opportunities=[],
                error=str(e)
            )

    def _normalize_project(self, proj: dict, users: dict | None) -> Opportunity:
        """Convert Freelancer project to normalized Opportunity."""

        project_id = str(proj.get("id", ""))
        owner_id = str(proj.get("owner_id", ""))

        # Get owner/client info
        client = None
        if owner_id and users and owner_id in users:
            user = users[owner_id]
            reputation = user.get("employer_reputation", {})

            client = Client(
                id=owner_id,
                username=user.get("username"),
                rating=reputation.get("overall", 0),
                review_count=reputation.get("reviews", 0),
                total_spent=reputation.get("earnings", 0),  # API calls it earnings
                hire_count=reputation.get("complete", 0),
                payment_verified=user.get("status", {}).get("payment_verified", False),
                location=user.get("location", {}).get("country", {}).get("name"),
            )

        # Determine budget type and values
        budget_type = BudgetType.UNKNOWN
        budget_min = None
        budget_max = None
        hourly_min = None
        hourly_max = None

        if proj.get("type") == "hourly":
            budget_type = BudgetType.HOURLY
            hourly_info = proj.get("hourly_project_info") or {}
            hourly_min = hourly_info.get("rate_min")
            hourly_max = hourly_info.get("rate_max")
        else:
            budget_type = BudgetType.FIXED
            budget_obj = proj.get("budget") or {}
            budget_min = budget_obj.get("minimum")
            budget_max = budget_obj.get("maximum")

        # Extract skills from jobs
        skills = []
        jobs = proj.get("jobs") or []
        for job in jobs:
            if isinstance(job, dict):
                skills.append(job.get("name", ""))
            elif isinstance(job, str):
                skills.append(job)

        # Parse timestamp
        submitted = proj.get("time_submitted", 0)
        posted_at = datetime.fromtimestamp(submitted) if submitted else datetime.now()

        return Opportunity(
            id=f"fl_{project_id}",
            source=Source.FREELANCER,
            url=f"https://www.freelancer.com/projects/{proj.get('seo_url', project_id)}",
            title=proj.get("title", "Untitled"),
            description=proj.get("description", proj.get("preview_description", "")),
            skills=skills,
            budget_type=budget_type,
            budget_min=budget_min,
            budget_max=budget_max,
            hourly_min=hourly_min,
            hourly_max=hourly_max,
            client=client,
            posted_at=posted_at
        )


# For quick testing
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    async def test():
        source = FreelancerSource()
        print(f"Configured: {source.is_configured()}")

        if source.is_configured():
            # Fetch short projects under $2500 (default max_budget)
            batch = await source.fetch_opportunities(
                keywords=["AI", "automation", "MVP"],
                max_budget=2500,  # Filter for short projects
                limit=5
            )
            print(f"Fetched {len(batch.opportunities)} short projects (<$2500)")
            for opp in batch.opportunities:
                print(f"  - {opp.title} ({opp.budget_display})")

    asyncio.run(test())
