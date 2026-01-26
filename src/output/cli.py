"""CLI dashboard for viewing opportunities.

Uses Rich library for beautiful terminal output.
"""

import webbrowser
from datetime import datetime
from typing import Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..config import settings
from ..models import Opportunity, ScoredResults, Source


console = Console()


def score_color(score: float) -> str:
    """Get color for score value."""
    if score >= 85:
        return "green"
    if score >= 70:
        return "yellow"
    if score >= 60:
        return "orange1"
    return "red"


def source_abbrev(source: Source) -> str:
    """Short source abbreviation."""
    return {
        Source.FREELANCER: "FL",
        Source.UPWORK: "UW",
        Source.SAM_GOV: "SAM",
    }.get(source, "??")


def format_age(hours: float) -> str:
    """Format age in human-readable form."""
    if hours < 1:
        return f"{int(hours * 60)}m"
    if hours < 24:
        return f"{int(hours)}h"
    return f"{int(hours / 24)}d"


def create_summary_panel(results: ScoredResults) -> Panel:
    """Create summary statistics panel."""
    high_score = sum(1 for o in results.opportunities if o.total_score >= 85)
    med_score = sum(1 for o in results.opportunities if 70 <= o.total_score < 85)

    # Counts per source (always show, even if 0)
    by_source = results.after_score_filter_by_source or {s.value: 0 for s in Source}
    fl = by_source.get(Source.FREELANCER.value, 0)
    uw = by_source.get(Source.UPWORK.value, 0)
    sam = by_source.get(Source.SAM_GOV.value, 0)

    fl_min_score = settings.fln_min_score if settings.fln_min_score is not None else settings.min_score
    uw_min_budget = settings.upwork_min_budget if settings.upwork_min_budget is not None else settings.min_budget
    uw_min_score = settings.upwork_min_score if settings.upwork_min_score is not None else settings.min_score

    filters_line = (
        f"FL: max≤${settings.fln_max_budget:,.0f}, min_score≥{fl_min_score:.0f} "
        f"│ UW: min_budget≥${uw_min_budget:,.0f}, min_score≥{uw_min_score:.0f} "
        f"│ SAM: min_budget≥${settings.sam_min_budget:,.0f}, min_score≥{settings.sam_min_score:.0f}, "
        f"sdvo_only={str(settings.sam_sdvo_only).lower()}, naics={len(settings.sam_gov_naics_codes)}"
    )

    text = Text()
    text.append(f"Fetched: {results.total_fetched}", style="white")
    text.append("  ", style="white")
    text.append("│ ", style="dim")
    text.append("  ", style="white")
    text.append(f"After filters: {results.total_after_score_filter}", style="white")
    text.append("\n")

    text.append(f"By source: FL {fl}  UW {uw}  SAM {sam}", style="white")
    text.append("\n")

    text.append(filters_line, style="dim")
    text.append("\n")

    text.append(f"Score 85+: {high_score}", style="green bold")
    text.append("  ", style="white")
    text.append("│ ", style="dim")
    text.append("  ", style="white")
    text.append(f"Score 70-84: {med_score}", style="yellow")

    return Panel(
        text,
        title=f"[bold]LFG Opportunity Finder[/bold] - {datetime.now().strftime('%b %d, %Y %H:%M')}",
        border_style="blue",
    )


def create_opportunity_table(opportunities: list[Opportunity]) -> Table:
    """Create table of opportunities. Numbers are always 1-N for easy selection."""
    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        row_styles=["", "dim"],
    )

    table.add_column("#", style="dim", width=3)
    table.add_column("Score", justify="center", width=8)
    table.add_column("Title", width=45, overflow="ellipsis")
    table.add_column("Budget", justify="right", width=12)
    table.add_column("Client", justify="center", width=8)
    table.add_column("Age", justify="right", width=5)
    table.add_column("Src", justify="center", width=3)

    for i, opp in enumerate(opportunities, start=1):  # Always 1-N on each page
        score_text = Text()
        score_text.append(f"{opp.score_emoji} {opp.total_score:.0f}")

        client_score = Text()
        if opp.client and opp.client.rating:
            client_score.append(f"★{opp.client.rating:.1f}", style="yellow")
        else:
            client_score.append("—", style="dim")

        table.add_row(
            str(i),
            score_text,
            opp.title[:45],
            opp.budget_display,
            client_score,
            format_age(opp.age_hours),
            source_abbrev(opp.source),
        )

    return table


def show_opportunity_detail(opp: Opportunity) -> None:
    """Display detailed view of a single opportunity."""
    console.clear()

    # Header
    title_text = Text(opp.title, style="bold white")
    console.print(Panel(title_text, border_style="blue"))

    # Scores
    score_table = Table(box=None, show_header=False)
    score_table.add_column("Label", style="dim")
    score_table.add_column("Value")

    score_table.add_row(
        "Total Score",
        Text(
            f"{opp.score_emoji} {opp.total_score:.0f}/100",
            style=score_color(opp.total_score) + " bold",
        ),
    )
    score_table.add_row("Budget Score", f"{opp.budget_score:.0f}/100")
    score_table.add_row("Client Score", f"{opp.client_score:.0f}/100")
    score_table.add_row("Keyword Score", f"{opp.keyword_score:.0f}/100")

    if opp.matched_keywords:
        score_table.add_row("Matched Keywords", ", ".join(opp.matched_keywords[:5]))

    console.print(Panel(score_table, title="[bold]Scores[/bold]", border_style="green"))

    # Details
    detail_table = Table(box=None, show_header=False)
    detail_table.add_column("Label", style="dim", width=15)
    detail_table.add_column("Value")

    detail_table.add_row("Budget", opp.budget_display)
    detail_table.add_row("Posted", opp.posted_at.strftime("%Y-%m-%d %H:%M"))
    detail_table.add_row("Source", opp.source.value.title())

    if opp.skills:
        detail_table.add_row("Skills", ", ".join(opp.skills[:8]))

    if opp.client:
        client_info = []
        if opp.client.username:
            client_info.append(f"@{opp.client.username}")
        if opp.client.rating:
            client_info.append(f"★{opp.client.rating:.1f}")
        if opp.client.hire_count:
            client_info.append(f"{opp.client.hire_count} hires")
        if opp.client.payment_verified:
            client_info.append("✓ Verified")
        detail_table.add_row("Client", " │ ".join(client_info))

        if opp.client.location:
            detail_table.add_row("Location", opp.client.location)

    console.print(Panel(detail_table, title="[bold]Details[/bold]", border_style="cyan"))

    # Description
    desc = opp.description[:1000] + "..." if len(opp.description) > 1000 else opp.description
    console.print(Panel(desc, title="[bold]Description[/bold]", border_style="yellow"))

    console.print(f"\n[dim]URL:[/dim] {opp.url}")


def run_dashboard(results: ScoredResults, page_size: int = 10) -> None:
    """Interactive dashboard for browsing opportunities.

    Controls:
        n/p: Next/Previous page
        1-9: View opportunity details
        o: Open selected in browser
        q: Quit
    """
    opportunities = results.opportunities
    total = len(opportunities)
    page = 0
    selected_idx: Optional[int] = None

    while True:
        console.clear()

        start = page * page_size
        end = min(start + page_size, total)
        page_opps = opportunities[start:end]
        max_pages = (total + page_size - 1) // page_size

        # Show summary
        console.print(create_summary_panel(results))
        console.print()

        # Show table
        if not page_opps:
            console.print("[yellow]No opportunities found matching your criteria.[/yellow]")
        else:
            console.print(create_opportunity_table(page_opps))

        # Navigation
        console.print()
        nav_text = Text()
        nav_text.append(f"Page {page + 1}/{max_pages} ", style="dim")
        nav_text.append("│ ", style="dim")
        nav_text.append("[n]", style="cyan")
        nav_text.append("ext ", style="dim")
        nav_text.append("[p]", style="cyan")
        nav_text.append("rev ", style="dim")
        nav_text.append(f"[1-{len(page_opps)}]", style="cyan")
        nav_text.append(" details ", style="dim")
        nav_text.append("[o]", style="cyan")
        nav_text.append("pen ", style="dim")
        nav_text.append("[q]", style="cyan")
        nav_text.append("uit", style="dim")
        console.print(nav_text)

        # Get input
        try:
            key = console.input("\n> ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            break

        if key == "q":
            break
        if key == "n" and end < total:
            page += 1
        elif key == "p" and page > 0:
            page -= 1
        elif key.isdigit() and 1 <= int(key) <= len(page_opps):
            selected_idx = start + int(key) - 1
            show_opportunity_detail(opportunities[selected_idx])
            console.input("\n[dim]Press Enter to go back...[/dim]")
        elif key == "o" and selected_idx is not None:
            webbrowser.open(opportunities[selected_idx].url)
            console.print("[green]Opened in browser[/green]")
        elif key == "o" and page_opps:
            # Open first on page if none selected
            webbrowser.open(page_opps[0].url)
            console.print(f"[green]Opened {page_opps[0].title} in browser[/green]")

    console.print("\n[dim]Goodbye![/dim]")


def print_quick_list(results: ScoredResults, limit: int = 10) -> None:
    """Print a quick non-interactive list of top opportunities."""
    console.print(create_summary_panel(results))
    console.print()

    if not results.opportunities:
        console.print("[yellow]No opportunities found.[/yellow]")
        return

    table = create_opportunity_table(results.opportunities[:limit])
    console.print(table)

    console.print(
        f"\n[dim]Showing top {min(limit, len(results.opportunities))} of {len(results.opportunities)} opportunities[/dim]"
    )
