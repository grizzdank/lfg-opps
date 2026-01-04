"""Main scoring engine for opportunities.

Combines budget, client quality, and keyword scores into a composite score.
"""

import logging
from typing import Optional

from ..models import Opportunity, ScoredResults, BudgetType
from ..config import settings, ALL_KEYWORDS, KEYWORDS

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
        budget_weight: float = None,
        client_weight: float = None,
        keyword_weight: float = None,
        min_budget: float = None,
        min_score: float = None
    ):
        self.budget_weight = budget_weight or settings.budget_weight
        self.client_weight = client_weight or settings.client_weight
        self.keyword_weight = keyword_weight or settings.keyword_weight
        self.min_budget = min_budget or settings.min_budget
        self.min_score = min_score or settings.min_score

        # Validate weights sum to 1.0
        total = self.budget_weight + self.client_weight + self.keyword_weight
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total}, not 1.0. Normalizing...")
            self.budget_weight /= total
            self.client_weight /= total
            self.keyword_weight /= total

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
            elif budget >= 10000:
                return 95
            elif budget >= 5000:
                return 80
            elif budget >= 2500:
                return 60
            elif budget >= 1000:
                return 40
            else:
                return 20

        elif opp.budget_type == BudgetType.HOURLY:
            rate = opp.hourly_max or opp.hourly_min or 0

            if rate >= 100:
                return 100
            elif rate >= 75:
                return 95
            elif rate >= 50:
                return 85
            elif rate >= 35:
                return 70
            elif rate >= 25:
                return 50
            else:
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
            premium_locations = ["united states", "united kingdom", "canada",
                               "australia", "germany", "netherlands", "switzerland"]
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

        matched = []
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
            opp.budget_score * self.budget_weight +
            opp.client_score * self.client_weight +
            opp.keyword_score * self.keyword_weight
        )

        return opp

    def score_and_filter(
        self,
        opportunities: list[Opportunity],
        apply_budget_filter: bool = True,
        apply_score_filter: bool = True
    ) -> ScoredResults:
        """Score all opportunities and apply filters.

        Args:
            opportunities: Raw opportunities to score
            apply_budget_filter: Remove opps below min_budget
            apply_score_filter: Remove opps below min_score

        Returns:
            ScoredResults with filtered, sorted opportunities
        """
        total_fetched = len(opportunities)

        # Budget filter first (before scoring to save computation)
        if apply_budget_filter:
            filtered = []
            for opp in opportunities:
                budget = opp.budget_max or opp.budget_min or 0
                if opp.budget_type == BudgetType.HOURLY:
                    # Estimate based on 40 hours
                    hourly = opp.hourly_max or opp.hourly_min or 0
                    budget = hourly * 40

                if budget >= self.min_budget:
                    filtered.append(opp)
            opportunities = filtered

        total_after_budget = len(opportunities)

        # Score all
        for opp in opportunities:
            self.score(opp)

        # Score filter
        if apply_score_filter:
            opportunities = [o for o in opportunities if o.total_score >= self.min_score]

        total_after_score = len(opportunities)

        # Sort by total score descending
        opportunities.sort(key=lambda o: o.total_score, reverse=True)

        logger.info(
            f"Scoring: {total_fetched} fetched → "
            f"{total_after_budget} after budget filter → "
            f"{total_after_score} after score filter"
        )

        return ScoredResults(
            opportunities=opportunities,
            total_fetched=total_fetched,
            total_after_budget_filter=total_after_budget,
            total_after_score_filter=total_after_score
        )
