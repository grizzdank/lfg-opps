# AGENTS.md - LFG Opportunity Finder

Instructions for AI agents working on this codebase.

## Project Overview

Automated discovery and scoring system for consulting opportunities targeting [LFG Consultants](https://lfgconsultants.com/) services:
- AI Workflow Design & Integration
- Rapid MVP Development
- Organizational Change Management (OCM)

## Architecture

```
src/
├── config.py       # Settings via pydantic-settings, keyword definitions
├── models.py       # Pydantic models: Opportunity, Client, ScoredResults
├── main.py         # CLI entry point (click)
├── sources/        # Platform integrations (async fetch)
├── scoring/        # Composite scoring engine
└── output/         # CLI dashboard (Rich) + email digest
```

## Key Patterns

### Adding a New Source
1. Create `src/sources/newplatform.py`
2. Extend `BaseSource` abstract class
3. Implement `fetch_opportunities()` returning `OpportunityBatch`
4. Normalize platform data to `Opportunity` model
5. Register in `src/sources/__init__.py`

### Scoring Algorithm
Composite score = (budget × 0.4) + (client × 0.4) + (keywords × 0.2)

Weights configurable in `.env`. All component scores normalize to 0-100.

### Data Flow
```
Sources → fetch_opportunities() → [Opportunity] → OpportunityScorer → ScoredResults → CLI/Email
```

## Development Notes

### Environment
- Python 3.10+
- Dependencies in `requirements.txt`
- Credentials in `.env` (never commit)

### Running
```bash
python -m src.main           # Interactive dashboard
python -m src.main --quick   # Non-interactive list
python -m src.main --email   # Send digest
```

### Testing
```bash
pytest tests/
```

## Current Status

| Source | Status | Notes |
|--------|--------|-------|
| Freelancer.com | Ready | Uses official SDK, needs OAuth token |
| Upwork | Stub | Awaiting API approval (~2 weeks) |

## TODOs for Future Development

- [ ] SQLite persistence for deduplication and history
- [ ] Upwork GraphQL integration (after API approval)
- [ ] Response tracking (applied → interview → contract)
- [ ] Claude API integration for proposal drafts
- [ ] Slack/Discord webhook notifications

## Conventions

- Use `async/await` for all API calls
- Pydantic models for all data structures
- Rich library for terminal output
- Logging via Python `logging` module
- Type hints on all functions

## Files to Never Modify Without Understanding

- `src/models.py` - Core data structures, changes cascade everywhere
- `src/scoring/scorer.py` - Scoring weights affect opportunity ranking
- `src/config.py` - Keywords define what opportunities match

## Commit Message Format

Use conventional commits:
```
feat: add new opportunity source
fix: correct budget calculation for hourly projects
docs: update README with setup instructions
refactor: extract email template to separate file
```
