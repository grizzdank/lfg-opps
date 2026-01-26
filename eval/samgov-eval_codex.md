# Evaluation of `lfg-opps` SAM.gov Scraper Effectiveness
**Date:** 2024-05-22
**Evaluator:** Codex Subagent
**Subject:** Federal Contract Discovery Strategy for LFG Consultants (SDVOSB)

## Executive Summary
The `lfg-opps` tool provides a solid foundational layer for federal opportunity discovery by leveraging the official SAM.gov API and targeting industry-standard NAICS codes. However, as a Service-Disabled Veteran-Owned Small Business (SDVOSB) focused on high-end AI and OCM consulting, the current implementation faces significant hurdles in "Signal-to-Noise" ratio and "Timing." The reliance on late-stage SAM.gov postings often means LFG enters the competition too late.

---

## 1. Coverage: NAICS Code Analysis
The current list of 11 NAICS codes covers the basics of IT and Management Consulting, but misses critical niche areas where AI and OCM intersect.

*   **Current Strengths:** 541511 (Custom Programming), 541512 (Systems Design), 541611 (Admin & General Management).
*   **What's Missing:**
    *   **541513 (Computer Facilities Management):** Often used for long-term AI infrastructure maintenance or cloud operations.
    *   **541613 (Marketing Consulting):** Frequently used for "Customer Experience" (CX) and "Digital Strategy" projects which heavily involve OCM.
    *   **541990 (All Other Professional, Scientific, and Technical Services):** A "catch-all" frequently used for innovative R&D or pilot programs that don't fit standard IT boxes.
    *   **519190 (All Other Information Services):** Sometimes used for data science and AI-specific data curation.

**Recommendation:** Add a "Secondary NAICS" watch list to capture these outliers.

---

## 2. Signal-to-Noise: Scoring Algorithm Evaluation
The current scoring (Budget 40%, Client 40%, Keywords 20%) is logically sound but practically flawed due to SAM.gov data quality.

*   **The "Budget" Problem (40%):** Since budget is missing or "0" in the majority of pre-soliticiations and initial notices, 40% of the score is frequently rendered useless. This causes high-value opportunities to rank lower than mediocre ones that happen to have a dollar figure attached.
*   **Keyword Match (20%):** This is under-weighted. For a specialized firm like LFG, a 100% keyword match for "Change Management + AI" is a much better lead than a high-budget "Generic IT Support" contract.
*   **Client Quality (40%):** This is subjective. Is it based on past SDVOSB spend? Prompt payment? Ease of procurement?

**Recommendation:** Shift weights to **Keywords (50%)**, **Client/Agency History (30%)**, and **Budget (20%)**. Use a "Boolean Multiplier" for keywords—if "OCM" AND "AI" both appear, double the score.

---

## 3. Timing: The Procurement Cycle Gap
SAM.gov is where opportunities go to *die* or be *competed*. If LFG only sees it on SAM.gov, the incumbent likely already knows about it.

*   **The Problem:** Most SAM.gov postings are "Sources Sought" or "RFPs." By the time an RFP hits, the technical requirements have often been shaped by a competitor during the "Pre-RFP" phase.
*   **Missing Phases:** Look for **Special Notices** and **Pre-solicitations** specifically. If the scraper treats all notices equally, LFG is reacting, not positioning.

---

## 4. Competition: SDVOSB Strategy
Leveraging the **SDVOSB set-aside** is LFG's greatest "unfair advantage."

*   **Full-and-Open vs. Set-Aside:** The scraper should prioritize SDVOSB set-asides where the "Rule of Two" (two or more capable SDVOSBs) applies. Competing in Full-and-Open against Tier 1 integrators (Booz Allen, Deloitte) is a low-probability play for an MVP-focused boutique.
*   **Sole Source Potential:** The scraper should flag opportunities labeled "Notice of Intent to Sole Source" to see which competitors are winning and potentially approach them for sub-contracting OCM/AI components.

---

## 5. Gaps: Missing Data Sources
Beyond SAM.gov, LFG is blind to:
*   **GSA eBuy:** Many AI/Management consulting tasks are run through GSA Schedules (MAS). If LFG isn't on a schedule, they miss 50% of the relevant market.
*   **Tradewinds Solutions Marketplace:** Specifically for AI/ML, the DoD uses Tradewinds for rapid MVP procurement.
*   **SBIR/STTR (Small Business Innovation Research):** Prime territory for LFG's "Rapid MVP" and AI capabilities.

---

## 6. Concrete Recommendations for Improvement

1.  **Contextual Analysis (NLP):** Instead of simple keyword matching, use an LLM (via the tool) to summarize the *Statement of Work (SOW)* and score it against "LFG Capability Fit."
2.  **Agency-Specific Targeting:** Focus on agencies with high "AI Readiness" or "Digital Transformation" mandates (e.g., HHS, VA, DoD - JAIC/CDAO).
3.  **Teaming Discovery:** Add a feature to identify the *incumbent* on expiring contracts. LFG can then reach out to the incumbent to offer specialized AI/OCM sub-contracting.
4.  **"Sources Sought" Bot:** Create a specific filter for "Sources Sought." Responding to these is the only way to influence the RFP and ensure it becomes an SDVOSB set-aside.
5.  **Budget Proxy:** Since budget is often missing, use "Place of Performance" and "Type of Service" to estimate value based on historical agency spend for similar NAICS.

## Conclusion
`lfg-opps` is a great start, but it currently functions as a **passive filter** rather than an **active intelligence tool**. By shifting focus toward earlier-stage signals (Sources Sought) and emphasizing technical keyword relevancy over missing budget data, LFG can significantly increase its win probability.
