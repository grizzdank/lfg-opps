"""Output handlers for opportunities."""

from .cli import run_dashboard, print_quick_list, console
from .email import send_digest, test_email_config

__all__ = ["run_dashboard", "print_quick_list", "console", "send_digest", "test_email_config"]
