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

## 2026-01-26 06:50 - Parallel Queries, Per-Source Cache, Award Filtering

### Changes Made
- `src/sources/sam_gov.py`: Parallelized NAICS queries with `asyncio.gather` (~10s vs ~45s sequential)
- `src/sources/sam_gov.py`: Added `ACTIVE_NOTICE_TYPES` filter to exclude awards/justifications
- `src/main.py`: Refactored to support per-source cache invalidation (`--refresh sam`, `--refresh fl,uw`, `--refresh all`)
- `src/main.py`: New functions `fetch_with_cache()`, `fetch_sources()`, `fetch_single_source()` for cleaner separation
- `src/output/cli.py`: Fixed page 2+ selector bug (numbers now 1-N per page, matching input expectations)

### Current Status
- **Working**: All 11 NAICS queries fire in parallel, dramatically faster SAM.gov fetches
- **Working**: Per-source cache — can refresh just SAM while keeping Freelancer cached
- **Working**: Award notices filtered out, only active solicitations shown
- **Fixed**: TUI item selector now works correctly on all pages

### Next Steps
- Upwork integration still pending API approval
- Consider adding response deadline filtering for SAM.gov (hide expired)
- May want to add sorting options in TUI (by score, date, budget)

## 2026-01-26 09:15 - Phase 1 Code Review & Bug Fixes

### Changes Made
- `src/sources/sam_gov.py`: Fixed critical bug — award notices slipping through filter (changed blacklist to whitelist approach)
- `src/sources/sam_gov.py`: Added `response_deadline` to Opportunity constructor
- `src/models.py`: Added `response_deadline: Optional[datetime]` field
- `tests/test_scoring.py`: Added 8 new tests for Phase 1 scoring (phase, set-aside, negative keywords)
- `TODO.md`: Marked all Phase 1 items complete

### Current Status
- **Fixed**: Award notices (like sam.gov/opp/9593a6713b8d452c8f4b7c4b91317727) no longer score — whitelist filter rejects unknown notice types
- **Working**: Phase 1 complete — scoring weights (50% keyword, 25% phase, 25% set-aside), NAICS expansion, negative keywords, 90-day lookback
- **Tests**: 19 passing (11 original + 8 new Phase 1 tests)

### Next Steps
- Phase 2: LLM scoring (optional enhancement), SBIR.gov source, Phase Zero alerts
- Phase 3: Tradewinds integration, teaming intelligence, agency forecasts
- Consider adding `response_deadline` filtering to hide expired opportunities
