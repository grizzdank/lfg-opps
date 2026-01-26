"""Tests for the scoring engine."""

from datetime import datetime

import pytest

from src.config import settings
from src.models import BudgetType, Client, Opportunity, Source
from src.scoring import OpportunityScorer


def make_opportunity(
    *,
    source: Source = Source.FREELANCER,
    budget_max: float = 5000,
    budget_type: BudgetType = BudgetType.FIXED,
    client_rating: float = 4.5,
    title: str = "Test Project",
    description: str = "A test project",
) -> Opportunity:
    """Factory for test opportunities."""
    return Opportunity(
        id="test_1",
        source=source,
        url="https://example.com/test",
        title=title,
        description=description,
        skills=["python", "api"],
        budget_type=budget_type,
        budget_min=budget_max * 0.8,
        budget_max=budget_max,
        client=Client(
            id="client_1",
            username="testclient",
            rating=client_rating,
            review_count=10,
            total_spent=15000,
            hire_count=8,
            payment_verified=True,
            location="United States",
        ),
        posted_at=datetime.now(),
    )


class TestBudgetScoring:
    """Test budget score calculation."""

    def test_high_budget_scores_high(self):
        scorer = OpportunityScorer()
        opp = make_opportunity(budget_max=30000)
        score = scorer.score_budget(opp)
        assert score == 100

    def test_mid_budget_scores_mid(self):
        scorer = OpportunityScorer()
        opp = make_opportunity(budget_max=7500)
        score = scorer.score_budget(opp)
        assert score == 80

    def test_low_budget_scores_low(self):
        scorer = OpportunityScorer()
        opp = make_opportunity(budget_max=3000)
        score = scorer.score_budget(opp)
        assert score == 60


class TestClientScoring:
    """Test client quality score calculation."""

    def test_excellent_client_scores_high(self):
        scorer = OpportunityScorer()
        opp = make_opportunity(client_rating=4.9)
        score = scorer.score_client(opp)
        assert score >= 80

    def test_verified_payment_adds_points(self):
        scorer = OpportunityScorer()
        opp = make_opportunity()
        opp.client.payment_verified = True
        score_verified = scorer.score_client(opp)

        opp.client.payment_verified = False
        score_unverified = scorer.score_client(opp)

        assert score_verified > score_unverified


class TestKeywordScoring:
    """Test keyword matching."""

    def test_ai_keywords_match(self):
        scorer = OpportunityScorer()
        opp = make_opportunity(title="AI Workflow Automation", description="Need help with machine learning integration")
        score, matched = scorer.score_keywords(opp)
        assert score > 0
        assert any("ai" in kw.lower() for kw in matched)

    def test_mvp_keywords_match(self):
        scorer = OpportunityScorer()
        opp = make_opportunity(title="MVP Development for Startup", description="Rapid prototype needed")
        score, matched = scorer.score_keywords(opp)
        assert score > 0
        assert any("mvp" in kw.lower() or "prototype" in kw.lower() for kw in matched)


class TestCompositeScoring:
    """Test full scoring pipeline."""

    def test_score_populates_all_fields(self):
        scorer = OpportunityScorer()
        opp = make_opportunity()
        scorer.score(opp)

        assert opp.budget_score > 0
        assert opp.client_score > 0
        assert opp.total_score > 0

    def test_filter_respects_per_source_min_budget(self, monkeypatch: pytest.MonkeyPatch):
        # Use Upwork source to avoid Freelancer max cap interaction.
        monkeypatch.setattr(settings, "upwork_min_budget", 5000, raising=False)

        scorer = OpportunityScorer(min_budget=0)  # global fallback shouldn't matter
        opportunities = [
            make_opportunity(source=Source.UPWORK, budget_max=3000),
            make_opportunity(source=Source.UPWORK, budget_max=10000),
        ]
        results = scorer.score_and_filter(opportunities)
        assert len(results.opportunities) == 1
        assert results.opportunities[0].budget_max == 10000

    def test_freelancer_max_budget_cap_excludes_over_cap(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(settings, "fln_max_budget", 2500, raising=False)

        scorer = OpportunityScorer(min_budget=0, min_score=0)
        opportunities = [
            make_opportunity(source=Source.FREELANCER, budget_max=2000),
            make_opportunity(source=Source.FREELANCER, budget_max=3000),
        ]
        results = scorer.score_and_filter(opportunities, apply_score_filter=False)
        assert [o.budget_max for o in results.opportunities] == [2000]

    def test_sam_defaults_do_not_apply_global_min_score(self, monkeypatch: pytest.MonkeyPatch):
        # Global min_score high, SAM min_score default 0
        monkeypatch.setattr(settings, "min_score", 99, raising=False)
        monkeypatch.setattr(settings, "sam_min_score", 0, raising=False)
        monkeypatch.setattr(settings, "sam_min_budget", 0, raising=False)

        scorer = OpportunityScorer()
        opportunities = [
            make_opportunity(source=Source.SAM_GOV, budget_max=0, title="Some notice", description="federal contract"),
        ]
        results = scorer.score_and_filter(opportunities)
        assert len(results.opportunities) == 1


class TestPhase1Scoring:
    """Test Phase 1 scoring methods: phase (notice type), set-aside, and negative keywords."""

    def test_score_phase_sources_sought(self):
        """Sources Sought should score 100."""
        scorer = OpportunityScorer()
        opp = make_opportunity(source=Source.SAM_GOV, title="Sources Sought for AI Services")
        opp.notice_type = "Sources Sought"

        score = scorer.score_phase(opp)
        assert score == 100

    def test_score_phase_solicitation(self):
        """Solicitation should score 50."""
        scorer = OpportunityScorer()
        opp = make_opportunity(source=Source.SAM_GOV, title="Solicitation for IT Services")
        opp.notice_type = "Solicitation"

        score = scorer.score_phase(opp)
        assert score == 50

    def test_score_phase_non_samgov(self):
        """Non-SAM.gov sources should return default phase score of 50."""
        scorer = OpportunityScorer()

        # Test Freelancer source
        opp_fln = make_opportunity(source=Source.FREELANCER, title="Some project")
        score_fln = scorer.score_phase(opp_fln)
        assert score_fln == 50

        # Test Upwork source
        opp_upwork = make_opportunity(source=Source.UPWORK, title="Another project")
        score_upwork = scorer.score_phase(opp_upwork)
        assert score_upwork == 50

    def test_score_setaside_sdvosb(self):
        """SDVOSB in description/tags should score 100."""
        scorer = OpportunityScorer()

        # Test SDVOSB in description
        opp_desc = make_opportunity(
            source=Source.SAM_GOV,
            title="Federal Contract",
            description="This is an SDVOSB set-aside opportunity",
        )
        score_desc = scorer.score_setaside(opp_desc)
        assert score_desc == 100

        # Test SDVOSB in skills/tags
        opp_tags = make_opportunity(
            source=Source.SAM_GOV,
            title="Federal Contract",
            description="Some federal opportunity",
        )
        opp_tags.skills = ["IT Services", "SDVOSB"]
        score_tags = scorer.score_setaside(opp_tags)
        assert score_tags == 100

        # Test SDVOSB in set_aside field
        opp_setaside = make_opportunity(
            source=Source.SAM_GOV,
            title="Federal Contract",
            description="Some federal opportunity",
        )
        opp_setaside.set_aside = "SDVOSB"
        score_setaside = scorer.score_setaside(opp_setaside)
        assert score_setaside == 100

    def test_score_setaside_full_open(self):
        """Full & Open (no set-aside, not Sources Sought) should score 30."""
        scorer = OpportunityScorer()
        opp = make_opportunity(
            source=Source.SAM_GOV,
            title="Federal Contract",
            description="Full and open competition for IT services",
        )
        opp.notice_type = "Solicitation"  # Not Sources Sought
        opp.set_aside = ""

        score = scorer.score_setaside(opp)
        assert score == 30

    def test_score_setaside_sources_sought_creates_opportunity(self):
        """Sources Sought without set-aside should score 60 (opportunity to create set-aside)."""
        scorer = OpportunityScorer()
        opp = make_opportunity(
            source=Source.SAM_GOV,
            title="Sources Sought for Cloud Services",
            description="Seeking information from qualified vendors",
        )
        opp.notice_type = "Sources Sought"
        opp.set_aside = ""  # No set-aside yet

        score = scorer.score_setaside(opp)
        assert score == 60

    def test_negative_keywords_zero_score(self):
        """Negative keywords should result in a keyword score of 0."""
        scorer = OpportunityScorer()

        # Test with a negative keyword in description
        opp = make_opportunity(
            source=Source.SAM_GOV,
            title="Construction Project",
            description="Need construction services for building maintenance",
        )
        score, matched = scorer.score_keywords(opp)
        assert score == 0

    def test_negative_keywords_matched_list(self):
        """Matched list should contain NEGATIVE: prefix for negative keywords."""
        scorer = OpportunityScorer()

        # Test with "janitorial" negative keyword
        opp = make_opportunity(
            source=Source.SAM_GOV,
            title="Janitorial Services",
            description="Janitorial and custodial support services",
        )
        score, matched = scorer.score_keywords(opp)
        assert score == 0
        assert len(matched) == 1
        assert matched[0].startswith("NEGATIVE:")
        assert "janitorial" in matched[0].lower()
