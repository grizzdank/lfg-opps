"""Configuration management for LFG Opportunity Finder."""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Freelancer.com
    fln_oauth_token: str = Field(default="", description="Freelancer OAuth token")
    fln_url: str = Field(
        default="https://www.freelancer.com",
        description="Freelancer API URL"
    )

    # Upwork
    upwork_client_id: str = Field(default="", description="Upwork OAuth client ID")
    upwork_client_secret: str = Field(default="", description="Upwork OAuth secret")
    upwork_access_token: str = Field(default="", description="Upwork access token")

    # Email
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_user: str = Field(default="", description="SMTP username")
    smtp_password: str = Field(default="", description="SMTP password")
    email_to: str = Field(default="", description="Recipient email")
    email_from: str = Field(
        default="LFG Opportunity Finder <noreply@lfgconsultants.com>",
        description="Sender email"
    )

    # Scoring
    min_budget: float = Field(default=2500, description="Minimum project budget")
    min_score: float = Field(default=60, description="Minimum score to surface")
    max_results_per_run: int = Field(default=50, description="Max results per API call")

    # Weights (must sum to 1.0)
    budget_weight: float = Field(default=0.4, description="Budget score weight")
    client_weight: float = Field(default=0.4, description="Client quality weight")
    keyword_weight: float = Field(default=0.2, description="Keyword match weight")

    # Runtime
    check_interval: int = Field(default=60, description="Check interval in minutes")
    db_path: str = Field(default="data/opportunities.db", description="SQLite DB path")
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
        "ai", "artificial intelligence", "machine learning", "ml",
        "automation", "workflow", "automate", "chatbot", "gpt",
        "claude", "llm", "generative ai", "gen ai", "ai agent",
        "intelligent automation", "rpa", "process automation"
    ],
    "mvp_development": [
        "mvp", "minimum viable product", "prototype", "rapid development",
        "startup", "proof of concept", "poc", "quick turnaround",
        "fast development", "agile", "lean", "sprint"
    ],
    "change_management": [
        "change management", "ocm", "organizational change",
        "digital transformation", "transformation", "adoption",
        "training", "process improvement", "erp", "crm",
        "implementation", "migration", "rollout"
    ],
    "smb_focus": [
        "small business", "smb", "sme", "startup", "growing company",
        "scale", "efficiency", "cost effective", "budget conscious"
    ]
}

# Flatten for quick lookup
ALL_KEYWORDS = set()
for category in KEYWORDS.values():
    ALL_KEYWORDS.update(kw.lower() for kw in category)
