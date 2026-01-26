# LFG Opportunity Finder - Development Log

## 2026-01-05 13:45 - Initial Setup & Freelancer Integration

### Changes Made
- Created `.env` with Freelancer OAuth token (username: davegraham8)
- Fixed null-safety bugs in `src/sources/freelancer.py:177,206,211` (handle None users/budget/jobs)
- Added MIT License
- Created GitHub repo: https://github.com/grizzdank/lfg-opps
- Set up Python venv with all dependencies installed

### Current Status
- **Working**: Freelancer.com API integration, scoring engine, CLI dashboard, email digest
- **Blocked**: Upwork integration (awaiting API approval ~2 weeks)
- **Decision**: Skip $99 Freelancer verification - platform analysis showed 75% of opportunities are under $2,500, and high-budget listings are often spam. Upwork is better for consulting.

### Next Steps
- Wait for Upwork API approval (applied today)
- Consider adding SQLite persistence for deduplication
- Test email digest with SMTP credentials when ready

## 2026-01-26 06:35 - Pagination, SAM.gov Fix, SQLite Caching

### Changes Made
- `src/main.py`: Added pagination loop with per-source limits (SAM 10 pages, Upwork 5, Freelancer 3)
- `src/sources/sam_gov.py`: Fixed multi-NAICS querying (API treats comma-separated as AND; now queries each separately and dedupes)
- `src/storage.py`: New SQLite cache module (OpportunityStore) with save/load/clear
- `src/config.py`: Added `cache_ttl_hours` setting (default 4h)
- Added `--refresh` flag to force fresh fetch ignoring cache

### Current Status
- **Working**: SAM.gov now returns 500+ opportunities (was 0), SQLite caching makes TUI instant on repeat runs
- **Note**: SAM.gov API is slow/flaky (30s timeouts common), but per-NAICS querying handles failures gracefully
- **Merged**: Remote had OCM/PM NAICS codes (611430, 541612) + keywords from Sue

### Next Steps
- Consider parallelizing SAM.gov NAICS queries to reduce fetch time
- Upwork integration still pending API approval
- May want to add cache invalidation by source (currently all-or-nothing)
