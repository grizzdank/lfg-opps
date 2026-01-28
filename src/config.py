"""Configuration management for LFG Opportunity Finder."""

from pathlib import Path
from typing import List

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Freelancer.com
    fln_oauth_token: str = Field(default="", description="Freelancer OAuth token")
    fln_url: str = Field(
        default="https://www.freelancer.com",
        description="Freelancer API URL",
    )

    # Upwork
    upwork_client_id: str = Field(default="", description="Upwork OAuth client ID")
    upwork_client_secret: str = Field(default="", description="Upwork OAuth secret")
    upwork_access_token: str = Field(default="", description="Upwork access token")

    # SAM.gov Federal Opportunities
    sam_gov_api_key: str = Field(default="", description="SAM.gov API key from beta.sam.gov")
    # Back-compat field name (SAM_GOV_NAICS_CODES) + new env var name (SAM_NAICS_CODES)
    sam_gov_naics_codes: List[str] = Field(
        default=[
            "541511",  # Custom Computer Programming
            "541512",  # Computer Systems Design
            "541519",  # Other Computer Related Services
            "541611",  # Administrative Management Consulting
            "541618",  # Other Management Consulting
            "541690",  # Other Scientific/Technical Consulting
            "518210",  # Computing Infrastructure (Cloud/AI)
            "541715",  # R&D in Physical/Engineering/Life Sciences (AI/ML R&D)
            "541614",  # Process/Logistics Consulting
            "611430",  # Professional Development Training
            "541612",  # Human Resources Consulting
            "541513",  # Computer Facilities Management (AI infra)
            "541990",  # All Other Professional Services (catch-all)
            "541330",  # Engineering Services (MVP/R&D)
            "541613",  # Marketing Consulting (CX, AI adoption)
        ],
        validation_alias=AliasChoices("SAM_NAICS_CODES", "SAM_GOV_NAICS_CODES"),
        description=(
            "NAICS codes for IT/AI/consulting/OCM opportunities. "
            "541511=Programming, 541512=Systems Design, 541519=Other IT, "
            "541611=Admin Mgmt, 541618=Other Mgmt, 541690=Scientific/Tech, "
            "518210=Cloud/AI Infra, 541715=R&D, 541614=Process Consulting, "
            "611430=Prof Dev Training, 541612=HR Consulting"
        ),
    )
    sam_gov_set_asides: List[str] = Field(
        default=["SDVOSB", "VOSB", "SBA"],
        description="Set-aside types to prioritize",
    )
    sam_sdvo_only: bool = Field(
        default=False,
        validation_alias=AliasChoices("SAM_SDVO_ONLY", "SAM_GOV_SDVO_ONLY"),
        description="If true, restrict SAM.gov results to SDVOSB set-asides only",
    )

    # Email
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_user: str = Field(default="", description="SMTP username")
    smtp_password: str = Field(default="", description="SMTP password")
    email_to: str = Field(default="", description="Recipient email")
    email_from: str = Field(
        default="LFG Opportunity Finder <noreply@lfgconsultants.com>",
        description="Sender email",
    )

    # Scoring (global defaults)
    min_budget: float = Field(default=2500, description="Minimum project budget")
    min_score: float = Field(default=60, description="Minimum score to surface")
    max_results_per_run: int = Field(default=50, description="Max results per API call")

    # Per-source filtering thresholds (fall back to MIN_BUDGET/MIN_SCORE when not set)
    # Freelancer.com: hard cap for fixed-price projects; bids >$2500 require $99 verification.
    fln_max_budget: float = Field(
        default=2500,
        validation_alias=AliasChoices("FLN_MAX_BUDGET"),
        description="Freelancer.com hard cap: exclude projects with budgets above this amount",
    )
    fln_min_score: float | None = Field(
        default=None,
        validation_alias=AliasChoices("FLN_MIN_SCORE"),
        description="Freelancer.com minimum score; defaults to MIN_SCORE when unset",
    )

    # Upwork: use explicit thresholds when configured.
    upwork_min_budget: float | None = Field(
        default=None,
        validation_alias=AliasChoices("UPWORK_MIN_BUDGET"),
        description="Upwork minimum budget; defaults to MIN_BUDGET when unset",
    )
    upwork_min_score: float | None = Field(
        default=None,
        validation_alias=AliasChoices("UPWORK_MIN_SCORE"),
        description="Upwork minimum score; defaults to MIN_SCORE when unset",
    )

    # SAM.gov: default to showing everything that matches keywords/NAICS.
    sam_min_budget: float = Field(
        default=0,
        validation_alias=AliasChoices("SAM_MIN_BUDGET"),
        description="SAM.gov minimum budget; default 0 because budget is often missing",
    )
    sam_min_score: float = Field(
        default=0,
        validation_alias=AliasChoices("SAM_MIN_SCORE"),
        description="SAM.gov minimum score; default 0 to show all matching opportunities",
    )

    # Weights (must sum to 1.0)
    budget_weight: float = Field(default=0.0, description="Budget score weight")
    client_weight: float = Field(default=0.0, description="Client quality weight")
    keyword_weight: float = Field(default=0.5, description="Keyword match weight")
    phase_weight: float = Field(default=0.25, description="Notice type scoring weight")
    setaside_weight: float = Field(default=0.25, description="SDVOSB prioritization weight")

    # SAM.gov specifics
    sam_lookback_days: int = Field(default=90, description="Days of history to fetch from SAM.gov")

    # Runtime
    check_interval: int = Field(default=60, description="Check interval in minutes")
    db_path: str = Field(default="data/opportunities.db", description="SQLite DB path")
    cache_ttl_hours: float = Field(default=4.0, description="Cache TTL in hours; 0 to disable")
    log_level: str = Field(default="INFO", description="Logging level")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_db_path(self) -> Path:
        """Get absolute path to database."""
        path = Path(self.db_path)
        if not path.is_absolute():
            path = Path(__file__).parent.parent / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


# Singleton instance
settings = Settings()


# Keywords for scoring - organized by service area
KEYWORDS = {
    "ai_workflow": [
        "ai",
        "artificial intelligence",
        "machine learning",
        "ml",
        "automation",
        "workflow",
        "automate",
        "chatbot",
        "gpt",
        "claude",
        "llm",
        "generative ai",
        "gen ai",
        "ai agent",
        "intelligent automation",
        "rpa",
        "process automation",
        "natural language processing",
        "nlp",
        "computer vision",
        "predictive analytics",
        "data science",
        "deep learning",
        "ai/ml",
        "responsible ai",
        "decision support",
    ],
    "mvp_development": [
        "mvp",
        "minimum viable product",
        "prototype",
        "rapid development",
        "startup",
        "proof of concept",
        "poc",
        "quick turnaround",
        "fast development",
        "agile",
        "lean",
        "sprint",
    ],
    "change_management": [
        "change management",
        "ocm",
        "organizational change",
        "digital transformation",
        "transformation",
        "adoption",
        "training",
        "process improvement",
        "erp",
        "crm",
        "implementation",
        "migration",
        "rollout",
        "stakeholder engagement",
        "user adoption",
        "technology adoption",
        "business process reengineering",
        "continuous improvement",
        "project management",
        "program management",
        "pmo",
        "organizational development",
        "workforce development",
        "professional development",
        "facilitation",
        "communications strategy",
        "readiness assessment",
        "training development",
        "learning management",
    ],
    "cloud_devops": [
        "cloud",
        "aws",
        "azure",
        "gcp",
        "kubernetes",
        "docker",
        "containerization",
        "infrastructure as code",
        "terraform",
        "ci/cd",
        "platform engineering",
        "saas",
        "paas",
        "serverless",
        "cloud native",
    ],
    "smb_focus": [
        "smb",
        "sme",
        "startup",
        "growing company",
        "scale",
        "efficiency",
        "cost effective",
        "budget conscious",
    ],
    "federal_consulting": [
        "federal",
        "government",
        "agency",
        "dod",
        "defense",
        "va",
        "contract",
        "task order",
        "idiq",
        "bpa",
        "it modernization",
        "systems integration",
        "cloud migration",
        "devops",
        "devsecops",
        "zero trust",
        "cybersecurity",
        "data analytics",
        "knowledge management",
        "section 508",
        "agile development",
        "software development",
        "web application",
        "microservices",
    ],
}

NEGATIVE_KEYWORDS = [
    "construction",
    "janitorial",
    "custodial",
    "paving",
    "roofing",
    "plumbing",
    "hvac",
    "landscaping",
    "food service",
    "laundry",
    "guard services",
    "hardware maintenance",
    "forklift",
    "truck driver",
]

# Flatten for quick lookup
ALL_KEYWORDS = set()
for category in KEYWORDS.values():
    ALL_KEYWORDS.update(kw.lower() for kw in category)
