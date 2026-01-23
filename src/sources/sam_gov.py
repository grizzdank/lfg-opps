"""SAM.gov Get Opportunities Public API v2 source integration.

Docs: https://open.gsa.gov/api/get-opportunities-public-api/
Endpoint: https://api.sam.gov/opportunities/v2/search

Auth: API key provided as query param: api_key
Required params: postedFrom, postedTo (MM/dd/yyyy)

This source normalizes SAM.gov opportunities into the project's Opportunity model.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx

from ..config import settings
from ..models import BudgetType, Client, Opportunity, OpportunityBatch, Source
from .base import BaseSource

logger = logging.getLogger(__name__)

SAM_API_BASE = "https://api.sam.gov/opportunities/v2/search"

# Common set-aside codes (SAM.gov values can vary by notice)
SET_ASIDE_SDVOSB = "SDVOSB"


class SAMGovSource(BaseSource):
    """Fetch federal contract opportunities from SAM.gov."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    @property
    def source_type(self) -> Source:
        return Source.SAM_GOV

    @property
    def name(self) -> str:
        return "SAM.gov"

    def is_configured(self) -> bool:
        return bool(settings.sam_gov_api_key)

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            if not self.is_configured():
                raise ValueError(
                    "SAM.gov not configured. Set SAM_GOV_API_KEY in your .env file."
                )
            # Auth is via query param, but we still set Accept header.
            self._client = httpx.AsyncClient(
                headers={"Accept": "application/json"},
                timeout=httpx.Timeout(30.0),
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
        sdvosb_only: bool = False,
        posted_from: Optional[datetime] = None,
        posted_to: Optional[datetime] = None,
    ) -> OpportunityBatch:
        """Fetch contract opportunities from SAM.gov.

        Notes:
          - postedFrom/postedTo are required by the API (MM/dd/yyyy)
          - Budget isn't consistently present; we post-filter when available.

        Args:
            keywords: Optional list of keywords; applied to title search.
            min_budget: Minimum budget threshold; applied after normalization.
            limit: Max results per page (API supports larger, we cap sanely).
            cursor: Pagination offset as a string integer.
            naics_codes: Optional NAICS codes to filter (ncode).
            sdvosb_only: If True, add typeOfSetAside=SDVOSB.
            posted_from: Start date (defaults to 30 days ago).
            posted_to: End date (defaults to today).

        Returns:
            OpportunityBatch
        """
        if not self.is_configured():
            return OpportunityBatch(
                source=Source.SAM_GOV,
                opportunities=[],
                error="SAM.gov not configured (missing SAM_GOV_API_KEY)",
            )

        client = self._get_client()

        # Defaults for required date range.
        posted_from = posted_from or (datetime.now() - timedelta(days=30))
        posted_to = posted_to or datetime.now()

        # Pagination: cursor is offset
        try:
            offset = int(cursor) if cursor else 0
        except ValueError:
            offset = 0

        # Title keyword search
        title_query = None
        if keywords:
            # SAM's `title` param behaves like keyword matching; keep it simple.
            title_query = " ".join([k.strip() for k in keywords if k and k.strip()]) or None

        # NAICS
        naics = naics_codes if naics_codes is not None else settings.sam_gov_naics_codes
        naics_param = ",".join([c.strip() for c in naics if c and c.strip()]) if naics else None

        params: dict[str, Any] = {
            "api_key": settings.sam_gov_api_key,
            "postedFrom": posted_from.strftime("%m/%d/%Y"),
            "postedTo": posted_to.strftime("%m/%d/%Y"),
            "limit": min(max(limit, 1), 1000),
            "offset": max(offset, 0),
        }

        if title_query:
            params["q"] = title_query  # 'q' searches title + description; 'title' is too narrow

        if naics_param:
            params["ncode"] = naics_param

        if sdvosb_only:
            params["typeOfSetAside"] = SET_ASIDE_SDVOSB

        logger.info(
            "SAM.gov search postedFrom=%s postedTo=%s limit=%s offset=%s sdvosb_only=%s naics=%s title=%s",
            params["postedFrom"],
            params["postedTo"],
            params["limit"],
            params["offset"],
            sdvosb_only,
            naics_param,
            title_query,
        )

        try:
            resp = await client.get(SAM_API_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()

            raw_list = data.get("opportunitiesData") or []
            total_records = int(data.get("totalRecords") or 0)

            opportunities: list[Opportunity] = []
            for raw in raw_list:
                try:
                    opp = self._normalize_opportunity(raw)
                    if not opp:
                        continue
                    if min_budget is not None:
                        # Prefer budget_max when present; otherwise budget_min.
                        budget_val = opp.budget_max if opp.budget_max is not None else opp.budget_min
                        if budget_val is not None and budget_val < min_budget:
                            continue
                    opportunities.append(opp)
                except Exception as e:
                    logger.warning(
                        "Failed to normalize SAM.gov opportunity noticeId=%s: %s",
                        (raw or {}).get("noticeId"),
                        e,
                    )

            next_cursor = None
            # API uses offset/limit; next page exists if offset+limit < total.
            if (offset + params["limit"]) < total_records and len(raw_list) > 0:
                next_cursor = str(offset + params["limit"])

            return OpportunityBatch(
                source=Source.SAM_GOV,
                opportunities=opportunities,
                next_cursor=next_cursor,
            )

        except httpx.HTTPStatusError as e:
            body = None
            try:
                body = e.response.text
            except Exception:
                body = None
            logger.error(
                "SAM.gov HTTP error %s. Response: %s",
                e.response.status_code,
                (body[:5000] if body else "<no body>"),
            )
            return OpportunityBatch(
                source=Source.SAM_GOV,
                opportunities=[],
                error=f"SAM.gov API error: {e.response.status_code}",
            )
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error("SAM.gov network error: %s", e)
            return OpportunityBatch(
                source=Source.SAM_GOV,
                opportunities=[],
                error="SAM.gov network/timeout error",
            )
        except Exception as e:
            logger.exception("SAM.gov fetch failed")
            return OpportunityBatch(
                source=Source.SAM_GOV,
                opportunities=[],
                error=str(e),
            )

    def _normalize_opportunity(self, raw: dict) -> Optional[Opportunity]:
        notice_id = raw.get("noticeId") or raw.get("solicitationNumber")
        if not notice_id:
            return None

        posted_at = self._parse_date(raw.get("postedDate")) or datetime.now()

        # Attempt to derive a budget/award amount when present.
        budget_min: float | None = None
        budget_max: float | None = None

        award = raw.get("award") or {}
        if isinstance(award, dict):
            amt = award.get("amount") or award.get("awardAmount")
            try:
                if amt is not None:
                    budget_min = float(amt)
                    budget_max = float(amt)
            except (TypeError, ValueError):
                pass

        # Agency/office
        agency_name = (
            raw.get("fullParentPathName")
            or raw.get("organizationName")
            or raw.get("department")
            or "Unknown Agency"
        )

        office_addr = raw.get("officeAddress") or {}
        location = None
        if isinstance(office_addr, dict):
            location = office_addr.get("state") or office_addr.get("city")

        client = Client(
            id=str(raw.get("organizationId") or agency_name),
            username=str(agency_name),
            location=location,
        )

        naics_code = raw.get("naicsCode") or raw.get("naics")
        set_aside_desc = raw.get("typeOfSetAsideDescription") or raw.get("typeOfSetAside")
        response_deadline = raw.get("responseDeadLine") or raw.get("responseDeadline")

        description = raw.get("description") or ""
        extra_lines = []
        if set_aside_desc:
            extra_lines.append(f"Set-Aside: {set_aside_desc}")
        if naics_code:
            extra_lines.append(f"NAICS: {naics_code}")
        if response_deadline:
            extra_lines.append(f"Response Deadline: {response_deadline}")

        if extra_lines:
            description = (description + "\n\n" + "\n".join(extra_lines)).strip()

        # URL format commonly works as /opp/{noticeId}/view
        url = f"https://sam.gov/opp/{notice_id}/view"

        skills = self._extract_tags(raw)

        return Opportunity(
            id=f"sam_{notice_id}",
            source=Source.SAM_GOV,
            url=url,
            title=raw.get("title") or "Untitled",
            description=description,
            skills=skills,
            budget_type=BudgetType.FIXED,
            budget_min=budget_min,
            budget_max=budget_max,
            client=client,
            posted_at=posted_at,
        )

    def _extract_tags(self, raw: dict) -> list[str]:
        tags: list[str] = []

        naics_code = raw.get("naicsCode") or raw.get("naics")
        if naics_code:
            tags.append(f"NAICS:{naics_code}")

        set_aside = raw.get("typeOfSetAside")
        if set_aside:
            tags.append(str(set_aside))

        psc = raw.get("classificationCode")
        if psc:
            tags.append(f"PSC:{psc}")

        notice_type = raw.get("type")
        if notice_type:
            tags.append(str(notice_type))

        return tags

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None

        cleaned = date_str.replace("Z", "+00:00")

        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S",
            "%m/%d/%Y",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(cleaned, fmt)
            except ValueError:
                continue

        logger.debug("Could not parse SAM.gov date: %s", date_str)
        return None

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
