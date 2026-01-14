"""Main entry point for LFG Opportunity Finder.

Usage:
    python -m src.main              # Run interactive dashboard
    python -m src.main --quick      # Print top 10 and exit
    python -m src.main --email      # Send email digest
    python -m src.main --schedule   # Run on schedule
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

import click
from dotenv import load_dotenv

from .config import settings, KEYWORDS
from .models import Source
from .sources import FreelancerSource, SAMGovSource
from .sources.upwork import UpworkSource
from .sources.samgov import SAMGovSource
from .scoring import OpportunityScorer
from .output import run_dashboard, print_quick_list, console, send_digest

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def get_search_keywords() -> list[str]:
    """Get flattened list of search keywords for APIs."""
    # Use top keywords from each category for search
    keywords = []
    for category, kw_list in KEYWORDS.items():
        keywords.extend(kw_list[:3])  # Top 3 from each category
    return list(set(keywords))


async def fetch_all_opportunities():
    """Fetch opportunities from all configured sources."""
    sources = [
        FreelancerSource(),
        UpworkSource(),
        SAMGovSource()
    ]

    all_opportunities = []
    keywords = get_search_keywords()

    for source in sources:
        if not source.is_configured():
            console.print(f"[yellow]⚠ {source.name} not configured, skipping[/yellow]")
            continue

        console.print(f"[cyan]Fetching from {source.name}...[/cyan]")

        try:
            batch = await source.fetch_opportunities(
                keywords=keywords,
                min_budget=settings.min_budget,
                limit=settings.max_results_per_run
            )

            if batch.error:
                console.print(f"[red]✗ {source.name}: {batch.error}[/red]")
            else:
                console.print(f"[green]✓ {source.name}: {len(batch.opportunities)} opportunities[/green]")
                all_opportunities.extend(batch.opportunities)

        except Exception as e:
            console.print(f"[red]✗ {source.name} error: {e}[/red]")
            logger.exception(f"Error fetching from {source.name}")

    return all_opportunities


@click.command()
@click.option("--quick", "-q", is_flag=True, help="Print top opportunities and exit")
@click.option("--email", "-e", is_flag=True, help="Send email digest")
@click.option("--limit", "-l", default=10, help="Number of results to show/email")
@click.option("--schedule", "-s", is_flag=True, help="Run on schedule (every CHECK_INTERVAL minutes)")
@click.option("--dry-run", is_flag=True, help="Fetch and score but don't output")
def main(quick: bool, email: bool, limit: int, schedule: bool, dry_run: bool):
    """LFG Opportunity Finder - Discover consulting opportunities.

    Searches Freelancer.com and Upwork for projects matching
    LFG Consultants' services: AI workflows, MVP development,
    and change management.
    """
    console.print()
    console.print("[bold blue]LFG Opportunity Finder[/bold blue]")
    console.print(f"[dim]Minimum budget: ${settings.min_budget:,.0f} | Minimum score: {settings.min_score}[/dim]")
    console.print()

    if schedule:
        run_scheduled(quick, email, limit)
    else:
        run_once(quick, email, limit, dry_run)


def run_once(quick: bool, email: bool, limit: int, dry_run: bool):
    """Run a single fetch and display cycle."""
    # Fetch
    opportunities = asyncio.run(fetch_all_opportunities())

    if not opportunities:
        console.print("\n[yellow]No opportunities found. Check your API credentials.[/yellow]")
        sys.exit(1)

    # Score
    console.print("\n[cyan]Scoring opportunities...[/cyan]")
    scorer = OpportunityScorer()
    results = scorer.score_and_filter(opportunities)

    if dry_run:
        console.print(f"\n[green]Dry run complete. {len(results.opportunities)} opportunities scored.[/green]")
        return

    # Output
    if email:
        console.print("\n[cyan]Sending email digest...[/cyan]")
        if send_digest(results, limit):
            console.print(f"[green]✓ Email sent to {settings.email_to}[/green]")
        else:
            console.print("[red]✗ Failed to send email. Check SMTP settings.[/red]")

    if quick:
        console.print()
        print_quick_list(results, limit)
    else:
        run_dashboard(results)


def run_scheduled(quick: bool, email: bool, limit: int):
    """Run on a schedule."""
    import schedule
    import time

    interval = settings.check_interval

    console.print(f"[cyan]Running every {interval} minutes. Press Ctrl+C to stop.[/cyan]")

    def job():
        console.print(f"\n[dim]--- {datetime.now().strftime('%Y-%m-%d %H:%M')} ---[/dim]")
        run_once(quick=True, email=email, limit=limit, dry_run=False)

    # Run immediately
    job()

    # Schedule future runs
    schedule.every(interval).minutes.do(job)

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped.[/dim]")


if __name__ == "__main__":
    main()
