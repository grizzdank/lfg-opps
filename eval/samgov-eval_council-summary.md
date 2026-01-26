# SAM.gov Scraper Evaluation — Council Summary

**Date:** 2026-01-26
**Participants:** codex, deepseek, gemini-flash, gemini-pro, sonnet
**Subject:** Effectiveness of `lfg-opps` for federal contract discovery

---

## Executive Summary

**Unanimous verdict:** The SAM.gov scraper is *technically sound but strategically limited*. All 5 models identified the same critical flaw: **the scoring algorithm actively suppresses the best opportunities** by weighting budget at 40% when budget data is missing from most early-stage federal postings.

The tool functions as a "passive filter" rather than an "active intelligence engine." To be effective for an SDVOSB boutique focused on AI/OCM, it needs to shift from late-stage solicitation scraping to early-stage opportunity shaping.

---

## 🔴 Critical Flaw: The Budget Blind Spot

**Consensus: 5/5 models agree**

| Model | Quote |
|-------|-------|
| **Gemini-Pro** | "You are effectively **penalizing the most valuable early-stage opportunities**" |
| **Sonnet** | "High-relevance, high-value Sources Sought notices will score poorly" |
| **Codex** | "40% of the score is frequently rendered useless" |
| **Gemini-Flash** | "40% of the score is effectively neutralized" |
| **DeepSeek** | "Budget scores frequently = 20-40 points instead of 60-100" |

**The Problem:**
- SAM.gov rarely includes budget until award stage
- Sources Sought (the highest-value notices) always have $0 budget
- Current 40% weight means best leads rank *lower* than generic IT contracts

**Fix:** Reduce budget weight to 0-20%. Use as metadata filter, not ranking signal.

---

## ✅ Strong Consensus Points (4-5 models agree)

### 1. Invert Scoring Weights
| Current | Recommended (Consensus) |
|---------|------------------------|
| Budget: 40% | Keywords/Semantic: 40-60% |
| Client: 40% | Procurement Phase: 20-30% |
| Keywords: 20% | Set-Aside Status: 20% |
| | Budget: 0-20% |

### 2. Missing NAICS Codes
All models recommend expanding from 11 to 15-25 codes:
- **541513** — Computer Facilities Management (AI infrastructure)
- **541990** — All Other Professional Services (catch-all for innovation)
- **541330** — Engineering Services (MVP/R&D)
- **541613** — Marketing Consulting (CX, internal AI adoption)

### 3. Focus Upstream: Sources Sought
All 5 models emphasize: by the time an RFP hits SAM.gov, it's often "wired" for an incumbent.

**High-value notice types to prioritize:**
- **r** — Sources Sought (shape the SOW, influence set-aside decision)
- **p** — Presolicitation (early warning)
- **s** — Special Notice (Industry Days, RFIs)

### 4. Missing Opportunity Sources
| Source | Why It Matters | Models Citing |
|--------|---------------|---------------|
| **SBIR/STTR** | Direct funding for AI R&D/MVPs | 5/5 |
| **Tradewinds** | DoD AI-specific marketplace | 4/5 |
| **GSA eBuy** | Where MAS task orders flow (dark to SAM) | 4/5 |
| **Agency Forecasts** | 6-18 month lead time | 3/5 |
| **OTAs/Consortia** | Fast-track AI procurement | 2/5 |

### 5. Replace Keyword Counting with LLM Scoring
**3/5 models recommend** passing the description to a cheap LLM:
> "Rate this opportunity 0-100 on fit for an AI & Change Management consultancy. Explain why."

This handles nuance that regex can't (e.g., "We need AI" vs "We do not accept AI-generated proposals").

---

## 💡 Unique Insights by Model

| Model | Insight |
|-------|---------|
| **Gemini-Pro** | Don't just *find* SDVOSB set-asides — *create* them by responding to Unrestricted Sources Sought. If LFG + one other SDVOSB respond, the CO is encouraged to set it aside. |
| **Sonnet** | "Phase Zero Detection" — alert on notices containing "Industry Day" or "Draft RFP" — these are highest-value for OCM/AI firms. |
| **Codex** | Track "Notice of Intent to Sole Source" to identify competitors winning and approach them for sub-contracting. |
| **DeepSeek** | Provided actual code examples for `FederalScorer` class with phase/agency scoring. Most implementation-ready. |
| **Gemini-Flash** | "Dark portals" framing — GSA eBuy and agency-specific portals are invisible to SAM.gov scrapers. |

---

## 📋 Prioritized Recommendations

### Immediate (This Week)
1. **Fix scoring weights** — Keywords 50%, Procurement Phase 30%, Set-Aside 20%, Budget 0%
2. **Prioritize Sources Sought** — These are $0 budget but highest value
3. **Add negative keywords** — Exclude "Construction," "Janitorial," "Hardware Maintenance"
4. **Extend lookback to 60-90 days** — Catch earlier phases

### Short-Term (This Month)
5. **Add NAICS codes** — 541513, 541990, 541330, 541613
6. **Implement LLM scoring** — Replace regex with semantic fit analysis
7. **Add SBIR.gov monitoring** — Critical for MVP/AI R&D
8. **Create "Phase Zero" alerts** — Flag "Industry Day," "Draft RFP," "Market Research"

### Medium-Term (Q2)
9. **Integrate Tradewinds** — Required for DoD AI positioning
10. **Build teaming intelligence** — Track primes winning big contracts for sub-contracting
11. **Agency forecast monitoring** — Pre-market intelligence
12. **GSA Schedule pursuit** — Unlock eBuy visibility

---

## Key Metrics to Track

| Metric | Current State | Target |
|--------|--------------|--------|
| Relevant opportunities surfaced/week | Unknown | 10-20 |
| Sources Sought captured | Likely filtered out | 100% |
| Time-to-discovery (vs SAM posting) | 0 days | -30 days (forecasts) |
| Proposal-to-win rate | Baseline needed | 2x improvement |

---

## Files Generated

```
~/projects/lfg-opps/eval/
├── samgov-eval_codex.md
├── samgov-eval_deepseek.md
├── samgov-eval_gemini-flash.md
├── samgov-eval_gemini-pro.md
├── samgov-eval_sonnet.md
└── samgov-eval_council-summary.md  ← this file
```

---

*Council orchestrated by Pulpito 🐙*
