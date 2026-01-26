# TODO

## Phase 1: Critical Fixes (This Week)

- [ ] **1.1** Fix scoring weights: Keywords 50%, Phase 25%, Set-Aside 25%, Budget 0%
- [ ] **1.2** Add `score_phase()` - prioritize Sources Sought (r) over Solicitations (o)
- [ ] **1.3** Add `score_setaside()` - SDVOSB > VOSB > SBA > Small Business > Full & Open
- [ ] **1.4** Add negative keywords filter (construction, janitorial, etc.)
- [ ] **1.5** Extend lookback to 90 days
- [ ] **1.6** Add NAICS codes: 541513, 541990, 541330, 541613

## Phase 2: Enhanced Intelligence (This Month)

- [ ] **2.1** Store notice_type, set_aside, response_deadline in Opportunity model
- [ ] **2.2** Update SAM.gov normalizer to capture new fields
- [ ] **2.3** Add LLM scoring (gpt-4o-mini semantic fit analysis)
- [ ] **2.4** Phase Zero alerts (Industry Day, Draft RFP detection → Signal)
- [ ] **2.5** Add SBIR.gov source for R&D/MVP funding opportunities

## Phase 3: Strategic Expansion (Q2)

- [ ] **3.1** Tradewinds integration (DoD AI marketplace)
- [ ] **3.2** Teaming intelligence (track prime awards for sub opportunities)
- [ ] **3.3** Agency forecast monitoring (VA, DHS, HHS)
- [ ] **3.4** GSA Schedule pursuit → eBuy access

## Blocked

- **Upwork API**: Denied (need to respond/reapply)
- **GSA eBuy**: Requires GSA Schedule (application needed)

## Reference

See `IMPLEMENTATION-PLAN.md` for full details.
See `eval/samgov-eval_council-summary.md` for council findings.
