"""Main scoring engine for opportunities.

Combines budget, client quality, and keyword scores into a composite score.
"""

import logging

from ..config import KEYWORDS, settings
from ..models import BudgetType, Opportunity, ScoredResults, Source

logger = logging.getLogger(__name__)


class OpportunityScorer:
    """Scores opportunities based on budget, client quality, and keyword match.

    Scoring Philosophy:
    - Budget (40%): Higher budgets = more revenue potential
    - Client Quality (40%): Good clients = smoother projects, repeat business
    - Keywords (20%): Better match = higher conversion, less time wasted

    All scores are normalized to 0-100 scale before weighting.
    """

    def __init__(
        self,
        budget_weight: float | None = None,
        client_weight: float | None = None,
        keyword_weight: float | None = None,
        min_budget: float | None = None,
        min_score: float | None = None,
    ):
        # Global weights
        self.budget_weight = budget_weight or settings.budget_weight
        self.client_weight = client_weight or settings.client_weight
        self.keyword_weight = keyword_weight or settings.keyword_weight

        # Global defaults (used as fallbacks when per-source thresholds are unset)
        self.min_budget = min_budget if min_budget is not None else settings.min_budget
        self.min_score = min_score if min_score is not None else settings.min_score

        # Validate weights sum to 1.0
        total = self.budget_weight + self.client_weight + self.keyword_weight
        if abs(total - 1.0) > 0.01:
            logger.warning("Weights sum to %s, not 1.0. Normalizing...", total)
            self.budget_weight /= total
            self.client_weight /= total
            self.keyword_weight /= total

    def _estimated_budget(self, opp: Opportunity) -> float:
        """Best-effort comparable budget number for filtering.

        - FIXED: uses budget_max then budget_min.
        - HOURLY: estimates as hourly_rate * 40.
        - UNKNOWN/missing: returns 0.
        """
        if opp.budget_type == BudgetType.HOURLY:
            hourly = opp.hourly_max or opp.hourly_min or 0
            return float(hourly) * 40

        if opp.budget_type == BudgetType.FIXED:
            budget = opp.budget_max if opp.budget_max is not None else (opp.budget_min or 0)
            return float(budget or 0)

        # UNKNOWN
        budget = opp.budget_max if opp.budget_max is not None else (opp.budget_min or 0)
        return float(budget or 0)

    def _min_budget_for_source(self, source: Source) -> float:
        if source == Source.SAM_GOV:
            return settings.sam_min_budget
        if source == Source.UPWORK:
            return settings.upwork_min_budget if settings.upwork_min_budget is not None else self.min_budget
        # Freelancer (and default)
        return self.min_budget

    def _min_score_for_source(self, source: Source) -> float:
        if source == Source.SAM_GOV:
            return settings.sam_min_score
        if source == Source.UPWORK:
            return settings.upwork_min_score if settings.upwork_min_score is not None else self.min_score
        if source == Source.FREELANCER:
            return settings.fln_min_score if settings.fln_min_score is not None else self.min_score
        return self.min_score

    def _passes_source_budget_filters(self, opp: Opportunity) -> bool:
        est = self._estimated_budget(opp)

        # Freelancer hard cap (configurable)
        if opp.source == Source.FREELANCER:
            cap = settings.fln_max_budget
            if cap is not None and est and est > cap:
                return False

        # Minimum budgets (per-source)
        min_budget = self._min_budget_for_source(opp.source)
        return est >= min_budget

    def score_budget(self, opp: Opportunity) -> float:
        """Score based on project budget. Returns 0-100.

        Fixed price scoring:
            $2,500 - $5,000:   60 points
            $5,000 - $10,000:  80 points
            $10,000 - $25,000: 95 points
            $25,000+:          100 points

        Hourly scoring (assumes 40hr engagement):
            $50+/hr:  85 points
            $75+/hr:  95 points
            $100+/hr: 100 points
        """
        if opp.budget_type == BudgetType.FIXED:
            # Use max budget, or min if max not available
            budget = opp.budget_max or opp.budget_min or 0

            if budget >= 25000:
                return 100
            if budget >= 10000:
                return 95
            if budget >= 5000:
                return 80
            if budget >= 2500:
                return 60
            if budget >= 1000:
                return 40
            return 20

        if opp.budget_type == BudgetType.HOURLY:
            rate = opp.hourly_max or opp.hourly_min or 0

            if rate >= 100:
                return 100
            if rate >= 75:
                return 95
            if rate >= 50:
                return 85
            if rate >= 35:
                return 70
            if rate >= 25:
                return 50
            return 30

        # Unknown budget type
        return 50  # Neutral score

    def score_client(self, opp: Opportunity) -> float:
        """Score based on client quality. Returns 0-100.

        Factors (max 100 points total):
            - Rating 4.5+:      30 points
            - Payment verified: 20 points
            - 5+ previous hires: 20 points
            - $10K+ total spent: 15 points
            - Location (US/UK/CA/AU): 15 points (lower risk)
        """
        if not opp.client:
            return 40  # Unknown client, slightly below neutral

        score = 0
        client = opp.client

        # Rating (0-30 points)
        if client.rating:
            if client.rating >= 4.8:
                score += 30
            elif client.rating >= 4.5:
                score += 25
            elif client.rating >= 4.0:
                score += 15
            elif client.rating >= 3.5:
                score += 5

        # Payment verified (0-20 points)
        if client.payment_verified:
            score += 20

        # Previous hires (0-20 points)
        if client.hire_count:
            if client.hire_count >= 10:
                score += 20
            elif client.hire_count >= 5:
                score += 15
            elif client.hire_count >= 2:
                score += 10
            elif client.hire_count >= 1:
                score += 5

        # Total spent (0-15 points)
        if client.total_spent:
            if client.total_spent >= 50000:
                score += 15
            elif client.total_spent >= 10000:
                score += 12
            elif client.total_spent >= 5000:
                score += 8
            elif client.total_spent >= 1000:
                score += 4

        # Location bonus (0-15 points)
        if client.location:
            location = client.location.lower()
            premium_locations = [
                "united states",
                "united kingdom",
                "canada",
                "australia",
                "germany",
                "netherlands",
                "switzerland",
            ]
            if any(loc in location for loc in premium_locations):
                score += 15

        return min(score, 100)

    def score_keywords(self, opp: Opportunity) -> tuple[float, list[str]]:
        """Score based on keyword match. Returns (0-100 score, matched keywords).

        Each matched keyword category adds 25 points (max 100).
        Categories: AI/Workflow, MVP Development, Change Management, SMB Focus
        """
        text = f"{opp.title} {opp.description}".lower()
        skills_text = " ".join(opp.skills).lower()
        combined = f"{text} {skills_text}"

        matched: list[str] = []
        category_matches = {cat: False for cat in KEYWORDS}

        for category, keywords in KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in combined:
                    if not category_matches[category]:
                        category_matches[category] = True
                    if kw not in matched:
                        matched.append(kw)

        # 25 points per category matched
        categories_matched = sum(1 for m in category_matches.values() if m)
        score = min(categories_matched * 25, 100)

        return score, matched

    def score(self, opp: Opportunity) -> Opportunity:
        """Calculate all scores for an opportunity.

        Mutates the opportunity in-place and returns it.
        """
        opp.budget_score = self.score_budget(opp)
        opp.client_score = self.score_client(opp)
        keyword_score, matched = self.score_keywords(opp)
        opp.keyword_score = keyword_score
        opp.matched_keywords = matched

        # Composite score
        opp.total_score = (
            opp.budget_score * self.budget_weight
            + opp.client_score * self.client_weight
            + opp.keyword_score * self.keyword_weight
        )

        return opp

    def score_and_filter(
        self,
        opportunities: list[Opportunity],
        apply_budget_filter: bool = True,
        apply_score_filter: bool = True,
    ) -> ScoredResults:
        """Score all opportunities and apply filters.

        Per-source thresholds are applied so that one markets heuristics dont
        suppress another.

        Args:
            opportunities: Raw opportunities to score
            apply_budget_filter: Apply per-source budget filters (min budget + Freelancer cap)
            apply_score_filter: Apply per-source min score filters

        Returns:
            ScoredResults with filtered, sorted opportunities
        """
        total_fetched = len(opportunities)

        # Counts always include known sources, even if 0.
        fetched_by_source = {s.value: 0 for s in Source}
        for opp in opportunities:
            fetched_by_source[opp.source.value] = fetched_by_source.get(opp.source.value, 0) + 1

        # Budget filter first (before scoring to save computation)
        if apply_budget_filter:
            opportunities = [o for o in opportunities if self._passes_source_budget_filters(o)]

        after_budget_by_source = {s.value: 0 for s in Source}
        for opp in opportunities:
            after_budget_by_source[opp.source.value] = after_budget_by_source.get(opp.source.value, 0) + 1

        total_after_budget = len(opportunities)

        # Score all
        for opp in opportunities:
            self.score(opp)

        # Score filter (per-source)
        if apply_score_filter:
            opportunities = [
                o
                for o in opportunities
                if o.total_score >= self._min_score_for_source(o.source)
            ]

        after_score_by_source = {s.value: 0 for s in Source}
        for opp in opportunities:
            after_score_by_source[opp.source.value] = after_score_by_source.get(opp.source.value, 0) + 1

        total_after_score = len(opportunities)

        # Sort by total score descending
        opportunities.sort(key=lambda o: o.total_score, reverse=True)

        logger.info(
            "Scoring: %s fetched → %s after budget filter → %s after score filter",
            total_fetched,
            total_after_budget,
            total_after_score,
        )

        return ScoredResults(
            opportunities=opportunities,
            total_fetched=total_fetched,
            total_after_budget_filter=total_after_budget,
            total_after_score_filter=total_after_score,
            fetched_by_source=fetched_by_source,
            after_budget_filter_by_source=after_budget_by_source,
            after_score_filter_by_source=after_score_by_source,
        )
