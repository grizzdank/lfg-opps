"""Data models for opportunities and scoring."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, computed_field


class Source(str, Enum):
    """Supported opportunity sources."""
    FREELANCER = "freelancer"
    UPWORK = "upwork"
    SAM_GOV = "samgov"


class BudgetType(str, Enum):
    """Project budget types."""
    FIXED = "fixed"
    HOURLY = "hourly"
    UNKNOWN = "unknown"


class Client(BaseModel):
    """Client/employer information."""
    id: str
    username: Optional[str] = None
    rating: Optional[float] = None  # 0-5 scale
    review_count: Optional[int] = 0
    total_spent: Optional[float] = 0  # Total money spent on platform
    hire_count: Optional[int] = 0  # Number of freelancers hired
    payment_verified: bool = False
    location: Optional[str] = None
    member_since: Optional[datetime] = None


class Opportunity(BaseModel):
    """A consulting opportunity from any platform."""

    # Identity
    id: str = Field(description="Platform-specific unique ID")
    source: Source = Field(description="Which platform this came from")
    url: str = Field(description="Direct link to the opportunity")

    # Core details
    title: str
    description: str
    skills: list[str] = Field(default_factory=list)

    # Budget
    budget_type: BudgetType = BudgetType.UNKNOWN
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    hourly_min: Optional[float] = None
    hourly_max: Optional[float] = None

    # Client
    client: Optional[Client] = None

    # Metadata
    posted_at: datetime
    fetched_at: datetime = Field(default_factory=datetime.now)

    # Federal specific
    notice_type: str = Field(default="", description="SAM.gov notice type code (o, p, k, r, s)")
    set_aside: str = Field(default="", description="SAM.gov set-aside type")

    # Scoring (populated by scorer)
    budget_score: float = 0
    client_score: float = 0
    keyword_score: float = 0
    phase_score: float = 0
    setaside_score: float = 0
    total_score: float = 0
    matched_keywords: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def budget_display(self) -> str:
        """Human-readable budget string."""
        if self.budget_type == BudgetType.FIXED:
            if self.budget_min and self.budget_max:
                if self.budget_min == self.budget_max:
                    return f"${self.budget_min:,.0f}"
                return f"${self.budget_min:,.0f} - ${self.budget_max:,.0f}"
            elif self.budget_max:
                return f"Up to ${self.budget_max:,.0f}"
            elif self.budget_min:
                return f"${self.budget_min:,.0f}+"
        elif self.budget_type == BudgetType.HOURLY:
            if self.hourly_min and self.hourly_max:
                return f"${self.hourly_min:.0f}-${self.hourly_max:.0f}/hr"
            elif self.hourly_max:
                return f"Up to ${self.hourly_max:.0f}/hr"
        return "Not specified"

    @computed_field
    @property
    def age_hours(self) -> float:
        """Hours since posting."""
        delta = datetime.now() - self.posted_at
        return delta.total_seconds() / 3600

    @computed_field
    @property
    def score_emoji(self) -> str:
        """Visual indicator for score."""
        if self.total_score >= 85:
            return "🟢"
        elif self.total_score >= 70:
            return "🟡"
        elif self.total_score >= 60:
            return "🟠"
        return "🔴"


class OpportunityBatch(BaseModel):
    """A batch of fetched opportunities."""
    source: Source
    opportunities: list[Opportunity]
    fetched_at: datetime = Field(default_factory=datetime.now)
    next_cursor: Optional[str] = None  # For pagination
    error: Optional[str] = None


class ScoredResults(BaseModel):
    """Results after scoring and filtering."""
    opportunities: list[Opportunity]

    total_fetched: int
    total_after_budget_filter: int
    total_after_score_filter: int

    # Source breakdowns (keys are Source values: freelancer, upwork, samgov)
    fetched_by_source: dict[str, int] = Field(default_factory=dict)
    after_budget_filter_by_source: dict[str, int] = Field(default_factory=dict)
    after_score_filter_by_source: dict[str, int] = Field(default_factory=dict)

    generated_at: datetime = Field(default_factory=datetime.now)
