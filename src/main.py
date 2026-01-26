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
from .models import Opportunity, Source
from .sources import FreelancerSource, SAMGovSource
from .sources.upwork import UpworkSource
from .scoring import OpportunityScorer
from .storage import OpportunityStore
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


def paginate_control(page: int, cursor: str | None, source_type: Source) -> tuple[bool, float]:
    """Control pagination behavior per source.

    Args:
        page: Current page number (0-indexed, so page=0 is the first fetch)
        cursor: Next page cursor (None means this would be the first page)
        source_type: Which source we're fetching from

    Returns:
        tuple of (should_continue: bool, delay_seconds: float)
    """
    limits = {
        Source.SAM_GOV: (10, 0.3),      # 10 pages, 0.3s delay (lots of federal opps)
        Source.FREELANCER: (3, 0.2),    # 3 pages, 0.2s delay (quality drops fast)
        Source.UPWORK: (5, 0.3),        # 5 pages, 0.3s delay
    }
    max_pages, delay = limits.get(source_type, (5, 0.3))

    if page >= max_pages:
        return (False, 0)
    return (True, delay if page > 0 else 0)


async def fetch_with_cache(store: OpportunityStore, refresh_sources: set[Source]) -> list[Opportunity]:
    """Fetch opportunities with per-source caching."""
    sources = [
        (FreelancerSource(), Source.FREELANCER),
        (UpworkSource(), Source.UPWORK),
        (SAMGovSource(), Source.SAM_GOV),
    ]

    all_opportunities: list[Opportunity] = []
    sources_to_fetch: list[tuple] = []

    # Check each source's cache
    for source_obj, source_type in sources:
        if not source_obj.is_configured():
            console.print(f"[yellow]⚠ {source_obj.name} not configured, skipping[/yellow]")
            continue

        needs_refresh = source_type in refresh_sources
        cache_age = store.get_cache_age_hours(source=source_type)

        if not needs_refresh and cache_age is not None and cache_age < settings.cache_ttl_hours:
            # Load from cache
            cached = store.load_opportunities(max_age_hours=settings.cache_ttl_hours, source=source_type)
            console.print(f"[dim]✓ {source_obj.name}: {len(cached)} from cache ({cache_age:.1f}h old)[/dim]")
            all_opportunities.extend(cached)
        else:
            # Queue for fresh fetch
            reason = "refresh requested" if needs_refresh else "cache stale/empty"
            sources_to_fetch.append((source_obj, source_type, reason))

    # Fetch fresh data for queued sources
    if sources_to_fetch:
        fresh = await fetch_sources([(s, t) for s, t, _ in sources_to_fetch])
        all_opportunities.extend(fresh)

        # Save fresh data to cache
        for source_obj, source_type, _ in sources_to_fetch:
            source_opps = [o for o in fresh if o.source == source_type]
            if source_opps:
                store.save_opportunities(source_opps)
                console.print(f"[dim]Cached {len(source_opps)} {source_obj.name} opportunities[/dim]")

    return all_opportunities


async def fetch_sources(sources: list[tuple]) -> list[Opportunity]:
    """Fetch from specific sources."""
    all_opportunities = []
    keywords = get_search_keywords()

    for source, source_type in sources:
        console.print(f"[cyan]Fetching from {source.name}...[/cyan]")
        opps = await fetch_single_source(source, source_type, keywords)
        all_opportunities.extend(opps)

    return all_opportunities


async def fetch_single_source(source, source_type: Source, keywords: list[str]) -> list[Opportunity]:
    """Fetch opportunities from a single source with pagination."""
    try:
        fetch_kwargs = {"keywords": keywords, "limit": settings.max_results_per_run}

        if source_type == Source.FREELANCER:
            fetch_kwargs["min_budget"] = settings.min_budget
            fetch_kwargs["max_budget"] = settings.fln_max_budget
        elif source_type == Source.UPWORK:
            fetch_kwargs["min_budget"] = settings.upwork_min_budget if settings.upwork_min_budget is not None else settings.min_budget
        elif source_type == Source.SAM_GOV:
            fetch_kwargs["keywords"] = None
            fetch_kwargs["min_budget"] = settings.sam_min_budget
            fetch_kwargs["naics_codes"] = settings.sam_gov_naics_codes
            fetch_kwargs["sdvosb_only"] = settings.sam_sdvo_only

        source_opportunities = []
        cursor = None
        page = 0

        while True:
            should_continue, delay = paginate_control(page, cursor, source_type)
            if not should_continue:
                break

            if delay > 0:
                await asyncio.sleep(delay)

            fetch_kwargs["cursor"] = cursor
            batch = await source.fetch_opportunities(**fetch_kwargs)

            if batch.error:
                console.print(f"[red]✗ {source.name}: {batch.error}[/red]")
                break

            source_opportunities.extend(batch.opportunities)
            cursor = batch.next_cursor
            page += 1

            if not cursor:
                break

        if source_opportunities:
            console.print(f"[green]✓ {source.name}: {len(source_opportunities)} opportunities ({page} page(s))[/green]")

        return source_opportunities

    except Exception as e:
        console.print(f"[red]✗ {source.name} error: {e}[/red]")
        logger.exception(f"Error fetching from {source.name}")
        return []


async def fetch_all_opportunities():
    """Fetch opportunities from all configured sources (no caching)."""
    sources = [
        (FreelancerSource(), Source.FREELANCER),
        (UpworkSource(), Source.UPWORK),
        (SAMGovSource(), Source.SAM_GOV),
    ]

    configured = [(s, t) for s, t in sources if s.is_configured()]
    for s, _ in sources:
        if not s.is_configured():
            console.print(f"[yellow]⚠ {s.name} not configured, skipping[/yellow]")

    return await fetch_sources(configured)


@click.command()
@click.option("--quick", "-q", is_flag=True, help="Print top opportunities and exit")
@click.option("--email", "-e", is_flag=True, help="Send email digest")
@click.option("--limit", "-l", default=10, help="Number of results to show/email")
@click.option("--schedule", "-s", is_flag=True, help="Run on schedule (every CHECK_INTERVAL minutes)")
@click.option("--dry-run", is_flag=True, help="Fetch and score but don't output")
@click.option("--refresh", "-r", default="", help="Force refresh: 'all', or sources like 'sam,freelancer'")
def main(quick: bool, email: bool, limit: int, schedule: bool, dry_run: bool, refresh: str):
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
        run_once(quick, email, limit, dry_run, refresh)


def parse_refresh_sources(refresh: str) -> set[Source]:
    """Parse refresh argument into set of sources to refresh."""
    if not refresh:
        return set()
    if refresh.lower() == "all":
        return {Source.FREELANCER, Source.UPWORK, Source.SAM_GOV}

    source_map = {
        "sam": Source.SAM_GOV, "sam_gov": Source.SAM_GOV, "samgov": Source.SAM_GOV,
        "freelancer": Source.FREELANCER, "fl": Source.FREELANCER,
        "upwork": Source.UPWORK, "uw": Source.UPWORK,
    }
    sources = set()
    for name in refresh.lower().split(","):
        name = name.strip()
        if name in source_map:
            sources.add(source_map[name])
    return sources


def run_once(quick: bool, email: bool, limit: int, dry_run: bool, refresh: str = ""):
    """Run a single fetch and display cycle."""
    store = OpportunityStore(settings.get_db_path())
    refresh_sources = parse_refresh_sources(refresh)

    opportunities: list[Opportunity] = []

    # Per-source cache check (fetch_with_cache handles saving)
    if settings.cache_ttl_hours > 0:
        opportunities = asyncio.run(fetch_with_cache(store, refresh_sources))
    else:
        opportunities = asyncio.run(fetch_all_opportunities())

    if not opportunities:
        console.print("\n[yellow]No opportunities found. Check your API credentials.[/yellow]")
        sys.exit(1)

    # Score
    console.print("\n[cyan]Scoring opportunities...[/cyan]")
    scorer = OpportunityScorer()
    results = scorer.score_and_filter(opportunities)

    # Update cache with scores
    if settings.cache_ttl_hours > 0 and results.opportunities:
        scores = {opp.id: opp.total_score for opp in results.opportunities}
        store.save_opportunities([opp for opp in results.opportunities], scores)

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
        run_once(quick=True, email=email, limit=limit, dry_run=False, refresh="all")

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
