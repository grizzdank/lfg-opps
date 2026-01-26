# Implementation Plan: Council Recommendations

**Created:** 2026-01-26
**Based on:** Council evaluation from 5 models (codex, deepseek, gemini-flash, gemini-pro, sonnet)

---

## Overview

Transform `lfg-opps` from a passive filter to an active federal opportunity intelligence engine.

**Key Metrics:**
- Sources Sought captured: 0% → 100%
- Relevant opportunities/week: ? → 15-25
- Time-to-discovery improvement: 30+ days earlier

---

## Phase 1: Critical Fixes (This Week)

### 1.1 Fix Scoring Weights
**File:** `src/config.py`

```python
# CURRENT (broken)
BUDGET_WEIGHT=0.4
CLIENT_WEIGHT=0.4  
KEYWORD_WEIGHT=0.2

# NEW
KEYWORD_WEIGHT=0.5
PHASE_WEIGHT=0.25      # NEW: Notice type scoring
SETASIDE_WEIGHT=0.25   # NEW: SDVOSB prioritization
BUDGET_WEIGHT=0.0      # Demote to metadata filter only
CLIENT_WEIGHT=0.0      # Not applicable to federal
```

**File:** `src/scoring/scorer.py`
- Add `score_phase()` method
- Add `score_setaside()` method
- Update composite score calculation

### 1.2 Add Phase/Notice Type Scoring
**New method in `scorer.py`:**

```python
def score_phase(self, opp: Opportunity) -> float:
    """Score based on procurement phase. Earlier = better.
    
    Sources Sought (r): 100 pts - can shape SOW, trigger set-aside
    Special Notice (s): 90 pts - Industry Days, RFIs
    Presolicitation (p): 80 pts - early warning
    Combined Synopsis (k): 60 pts - standard solicitation
    Solicitation (o): 50 pts - often too late
    """
    phase_scores = {
        "r": 100,  # Sources Sought - HIGHEST VALUE
        "s": 90,   # Special Notice (Industry Days)
        "p": 80,   # Presolicitation
        "k": 60,   # Combined Synopsis/Solicitation
        "o": 50,   # Solicitation
    }
    notice_type = getattr(opp, 'notice_type', '').lower()
    return phase_scores.get(notice_type, 50)
```

### 1.3 Add Set-Aside Scoring
**New method in `scorer.py`:**

```python
def score_setaside(self, opp: Opportunity) -> float:
    """Score based on set-aside type. SDVOSB preference.
    
    SDVOSB sole source: 100 pts
    SDVOSB competitive: 95 pts
    Total Small Business: 70 pts
    Partial Small Business: 50 pts
    Full & Open (Sources Sought): 60 pts - can CREATE set-aside
    Full & Open (Solicitation): 30 pts - low win probability
    """
    # Extract from opp.skills tags or description
    tags = " ".join(opp.skills).upper()
    desc = (opp.description or "").upper()
    
    if "SDVOSB" in tags or "SDVOSB" in desc:
        return 100
    if "VOSB" in tags or "VOSB" in desc:
        return 85
    if "SBA" in tags or "8(A)" in tags:
        return 75
    if "SMALL BUSINESS" in desc:
        return 70
    # Full & Open but Sources Sought = opportunity to CREATE set-aside
    if getattr(opp, 'notice_type', '') == 'r':
        return 60
    return 30
```

### 1.4 Add Negative Keywords
**File:** `src/config.py`

```python
NEGATIVE_KEYWORDS = [
    "construction",
    "janitorial", 
    "custodial",
    "paving",
    "roofing",
    "plumbing",
    "hvac",
    "landscaping",
    "food service",
    "laundry",
    "guard services",
    "hardware maintenance",
    "forklift",
    "truck driver",
]
```

**Update `scorer.py`:** If negative keyword found, score = 0 (filter out).

### 1.5 Extend Lookback Window
**File:** `src/config.py`

```python
# CURRENT
# posted_from = now - 30 days

# NEW
SAM_LOOKBACK_DAYS=90
```

### 1.6 Expand NAICS Codes
**File:** `src/config.py`

```python
sam_gov_naics_codes: List[str] = Field(
    default=[
        # EXISTING (keep)
        "541511",  # Custom Computer Programming
        "541512",  # Computer Systems Design
        "541519",  # Other Computer Related Services
        "541611",  # Administrative Management Consulting
        "541618",  # Other Management Consulting
        "541690",  # Other Scientific/Technical Consulting
        "518210",  # Computing Infrastructure (Cloud/AI)
        "541715",  # R&D in Physical/Engineering/Life Sciences
        "541614",  # Process/Logistics Consulting
        "611430",  # Professional Development Training
        "541612",  # Human Resources Consulting
        
        # NEW (from council)
        "541513",  # Computer Facilities Management (AI infra)
        "541990",  # All Other Professional Services (catch-all)
        "541330",  # Engineering Services (MVP/R&D)
        "541613",  # Marketing Consulting (CX, AI adoption)
    ],
    ...
)
```

---

## Phase 2: Enhanced Intelligence (This Month)

### 2.1 Store Notice Type in Opportunity Model
**File:** `src/models.py`

```python
@dataclass
class Opportunity:
    ...
    notice_type: str = ""  # NEW: o, p, k, r, s
    set_aside: str = ""    # NEW: SDVOSB, SBA, etc.
    response_deadline: datetime | None = None  # NEW
```

### 2.2 Update SAM.gov Normalizer
**File:** `src/sources/sam_gov.py`

Update `_normalize_opportunity()` to capture:
- `notice_type` from raw data
- `set_aside` from typeOfSetAside field
- `response_deadline` from responseDeadLine field

### 2.3 Add LLM Scoring (Optional Enhancement)
**New file:** `src/scoring/llm_scorer.py`

```python
"""LLM-based semantic scoring for opportunity relevance."""

import os
from openai import OpenAI

PROMPT = """Rate this federal contract opportunity 0-100 on fit for an SDVOSB 
consulting firm specializing in:
- AI Workflow Design & Integration
- Organizational Change Management (OCM)  
- Rapid MVP Development

Opportunity:
Title: {title}
Description: {description}

Return ONLY a JSON object: {{"score": <0-100>, "reasoning": "<brief explanation>"}}
"""

class LLMScorer:
    def __init__(self):
        self.client = OpenAI()  # Uses OPENAI_API_KEY env var
        
    def score(self, opp: Opportunity) -> tuple[float, str]:
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",  # Cheap, fast
            messages=[{
                "role": "user",
                "content": PROMPT.format(
                    title=opp.title,
                    description=opp.description[:2000]  # Truncate
                )
            }],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result["score"], result["reasoning"]
```

**Cost estimate:** ~$0.01 per 50 opportunities (gpt-4o-mini)

### 2.4 Phase Zero Alerts
**File:** `src/config.py`

```python
PHASE_ZERO_KEYWORDS = [
    "industry day",
    "draft rfp",
    "draft rfi", 
    "market research",
    "sources sought",
    "capability statement",
    "rfi response",
]
```

**New feature:** When Phase Zero keywords detected + high score → immediate Signal notification.

### 2.5 Add SBIR.gov Source
**New file:** `src/sources/sbir.py`

SBIR API: https://www.sbir.gov/api

```python
"""SBIR/STTR funding opportunity source."""

SBIR_API = "https://www.sbir.gov/api/solicitations.json"

class SBIRSource(BaseSource):
    """Fetch SBIR/STTR funding opportunities.
    
    Perfect for "Rapid MVP" and AI R&D work.
    Phase I: ~$275K proof of concept
    Phase II: ~$1.5M development
    """
    
    @property
    def source_type(self) -> Source:
        return Source.SBIR
        
    async def fetch_opportunities(self, ...):
        # Query SBIR API
        # Filter by topics containing AI/ML/automation keywords
        # Normalize to Opportunity model
```

---

## Phase 3: Strategic Expansion (Q2)

### 3.1 Tradewinds Integration
**Priority:** HIGH for DoD AI positioning

Tradewinds Solutions Marketplace: https://tradewindai.com/
- Requires registration
- Upload 5-min capability video
- DoD AI-specific procurement vehicle

**Action:** Register LFG, then build scraper for opportunity alerts.

### 3.2 Teaming Intelligence
**New file:** `src/intelligence/teaming.py`

Monitor SAM.gov Award notices to:
1. Identify primes winning large contracts in target NAICS
2. Track their small business subcontracting needs
3. Generate "Subcontracting Lead" alerts

### 3.3 Agency Forecast Monitoring
Many agencies publish Excel/PDF forecasts before SAM.gov:
- VA: https://www.va.gov/opal/fo/dbwva/forecasts.asp
- DHS: Procurement forecasts
- HHS: Acquisition forecasts

**Action:** Build scrapers for top 5 target agencies.

### 3.4 GSA Schedule Pursuit
**Blocker:** LFG needs GSA MAS Schedule to access eBuy.

**Action items:**
1. Determine which SIN (Special Item Number) fits AI/OCM
2. Prepare GSA Schedule application
3. Once approved, build eBuy integration

---

## File Changes Summary

| File | Changes |
|------|---------|
| `src/config.py` | New weights, NAICS codes, negative keywords, lookback |
| `src/models.py` | Add notice_type, set_aside, response_deadline |
| `src/scoring/scorer.py` | Add score_phase(), score_setaside(), update composite |
| `src/scoring/llm_scorer.py` | NEW: LLM semantic scoring |
| `src/sources/sam_gov.py` | Capture notice_type, set_aside in normalizer |
| `src/sources/sbir.py` | NEW: SBIR/STTR source |
| `TODO.md` | Update with this plan |

---

## Testing Plan

### Phase 1 Validation
1. Run current scraper, capture baseline metrics
2. Apply Phase 1 changes
3. Compare: Are Sources Sought now surfacing? Are high-budget generic contracts deprioritized?

### Expected Outcomes
- Sources Sought should appear in top 10 (currently filtered out)
- "IT Help Desk" contracts should drop in ranking
- AI/OCM-specific opportunities should rise

---

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1 | 3-5 days | Fixed scoring, expanded NAICS, negative keywords |
| Phase 2 | 2 weeks | LLM scoring, SBIR source, Phase Zero alerts |
| Phase 3 | Q2 2026 | Tradewinds, teaming intel, forecasts |

---

## Next Action

Start with Phase 1.1: Update scoring weights in `config.py` and `scorer.py`.

Want me to begin implementation?
