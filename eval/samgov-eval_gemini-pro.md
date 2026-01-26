# SAM.gov Scraper Evaluation: LFG Consultants

**Agent:** Gemini Pro
**Date:** October 26, 2023
**Subject:** Evaluation of `lfg-opps` SAM.gov scraping strategy

## Executive Summary
The current `lfg-opps` implementation provides a solid baseline for automated lead generation but suffers from "data blindness" caused by reliance on structured fields (Budget) that are frequently empty in federal postings. For a niche boutique firm specializing in AI and OCM, the current scoring algorithm likely prioritizes generic, high-budget IT contracts over highly relevant but unpriced sources sought notices. The strategy is reactive rather than proactive.

---

## 1. Coverage: NAICS Code Analysis

The selected NAICS codes are generally strong for the service offerings, but there are minor optimization opportunities.

### Current Portfolio Analysis
*   **Strong Alignment:**
    *   **541511, 541512, 541519:** Core for AI/MVP development.
    *   **541611:** The "catch-all" for OCM and general consulting. Critical for LFG.
    *   **611430:** Excellent for OCM-related training/workshops.
*   **Marginal/Questionable:**
    *   **541715 (R&D):** Often dominates basic research contracts (labs/universities). Unless LFG is doing heavy R&D (SBIR/STTR), this may introduce noise.
    *   **541614 (Logistics):** Unless the AI workflow is specifically supply-chain focused, this often returns pure logistics support (trucking, warehousing) which is irrelevant.

### Missing / Recommended Additions
*   **541990 (All Other Professional, Scientific, and Technical Services):** Often used for novel technologies or unique consulting requirements that don't fit neatly elsewhere.
*   **611710 (Educational Support Services):** If OCM work involves curriculum design or ed-tech.
*   **519290 (Web Search Portals and All Other Information Services):** Sometimes used for cloud/data services (replacing older 519190).

## 2. Signal-to-Noise: Scoring Algorithm Critique

**Current Model:** Budget (40%) | Client (40%) | Keywords (20%)

**Verdict:** **Ineffective for Discovery.**

### Issues
1.  **The Budget Fallacy:** Federal solicitations (especially Sources Sought/RFI) rarely publish a budget in the structured data fields. By weighting this 40%, you are effectively **penalizing the most valuable early-stage opportunities**. You are optimizing for "late-stage" Solicitations where pricing is often effectively decided.
2.  **Keyword Undervaluation:** For a boutique firm, *relevance is everything*. A $100M contract for generic "Help Desk Support" (Client Quality: High, Budget: High) will outscore a $500k "AI Strategy Pilot" (No Budget listed) despite the latter being a perfect fit.
3.  **Semantic Blindness:** Simple keyword matching fails to distinguish between "We need AI" and "We do not accept AI generated proposals."

### Refined Scoring Recommendation
*   **Keyword/Semantic Match:** 50% (Must prioritize relevance).
*   **Notice Type:** 20% (Prioritize Sources Sought/Presolicitation).
*   **Set-Aside Fit:** 20% (SDVOSB > Total Small Business > Unrestricted).
*   **Client Affinity:** 10% (Past performance agencies).
*   **Budget:** 0% (Treat as metadata, not ranking criteria, unless explicitly filtering).

## 3. Timing: The Procurement Cycle

SAM.gov API data includes Notice Types. The current description suggests a "batch and scan" approach.

*   **Risk:** If the scraper focuses on `Solicitation` and `Combined Synopsis/Solicitation`, LFG is too late. By the time an RFP hits SAM, the incumbent or a pre-positioned competitor often has it wired.
*   **Opportunity:** The tool must prioritize `Sources Sought` and `Presolicitation` and `Special Notice`.
    *   **Sources Sought:** Agencies looking for capability statements. This is where an SDVOSB "rule of two" decision happens. **This is the sweet spot for LFG.**
    *   **RFI:** Opportunity to shape the requirements before the RFP.

## 4. Competition & Strategy

*   **SDVOSB Leverage:** Using the SDVOSB set-aside filter is correct, but limiting.
    *   **Strategy:** Don't just look for *existing* SDVOSB set-asides. Look for *Unrestricted* opportunities in the *Sources Sought* phase. If LFG (and one other SDVOSB) responds with a strong capability statement, the Contracting Officer is legally encouraged to set it aside for SDVOSB. The tool helps *create* the set-aside, not just find it.
*   **Teaming:** Large primes often scan SAM for subs to meet small business goals. Identifying large unrestricted IDIQ vehicles where OCM is a component could allow LFG to pitch themselves as a sub to the prime.

## 5. Gaps: Beyond SAM.gov

SAM.gov is the "Public Square," but niche deals happen elsewhere.

1.  **Agency Forecasts:** Many agencies (VA, DHS, HHS) publish Excel/PDF forecasts of upcoming procurements *before* they hit SAM. The scraper misses this pre-market data.
2.  **SBIR/STTR:** For "Rapid MVP" and "AI," the SBIR (Small Business Innovation Research) program is critical. These are often listed on distinct portals (Department of Defense SBIR submission site, etc.), though sometimes cross-posted.
3.  **GSA eBuy:** If LFG gets on a GSA Schedule (e.g., MAS), eBuy is where the actual task orders flow. These are **not** public on SAM.gov.
4.  **Other Transaction Authorities (OTAs):** For AI/Tech, OTAs are faster than FAR-based contracts. Consortia (like C5, SOSSEC) manage these. They are opaque to a standard SAM scraper.

## 6. Concrete Improvements

### Immediate Actions (Low Effort)
1.  **Invert Scoring:** Flip the weights. Make Keyword Match 60%, Client 20%, Set-Aside Status 20%. Ignore Budget for ranking.
2.  **Filter Logic check:** Ensure `Sources Sought` are not being filtered out due to $0 budget.
3.  **Negative Keywords:** Implement exclusion basic keywords to reduce noise (e.g., "Construction," "Janitorial," "Hardware Maintenance," "Paving").

### Strategic Upgrades (High Effort)
1.  **LLM Enrichment:**
    *   Instead of counting keywords, pass the `Description` text to a cheap LLM (e.g., gpt-4o-mini, gemini-flash) with a prompt: *"Rate this opportunity 0-100 on fit for an AI & Change Management consultancy. Explain why."*
    *   Use this score for ranking. It handles nuance far better than regex.
2.  **Notification Velocity:**
    *   If a high-probability *Sources Sought* drops, alert via Slack/Signal immediately. Response windows are short.
3.  **Teaming/Subcontracting Flag:**
    *   If a large Unrestricted opportunity matches keywords but is too big for LFG ($50M+), flag it as a "Subcontracting Lead" to contact the likely primes.

## Conclusion
`lfg-opps` is currently built like a definitive filter (like shopping on Amazon) rather than a discovery engine for a complex B2B market. Federal contracting requires finding the *signal* in the *Early* phase (Sources Sought) where data is unstructured and budgets are hidden. Shifting from "Budget-driven" to "Content-driven" (LLM analysis) logic is the single highest-value change LFG can make.
