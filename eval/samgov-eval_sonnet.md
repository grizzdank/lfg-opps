# Evaluation of `lfg-opps` SAM.gov Scraper Effectiveness

## Overview
This evaluation assesses the current implementation of the `lfg-opps` tool for discovering federal consulting opportunities for LFG Consultants, an SDVOSB specializing in AI Workflows, OCM, and Rapid MVP development.

---

## 1. Coverage: NAICS Codes Analysis
The current set of 11 NAICS codes is a strong baseline, but contains gaps relative to LFG's core offerings.

**Current List:**
- 518210 (Data Processing, Hosting, and Related Services)
- 541511 (Custom Computer Programming Services)
- 541512 (Computer Systems Design Services)
- 541519 (Other Computer Related Services)
- 541611 (Administrative Management and General Management Consulting)
- 541612 (Human Resources Consulting)
- 541614 (Process, Physical Distribution, and Logistics Consulting)
- 541618 (Other Management Consulting Services)
- 541690 (Other Scientific and Technical Consulting Services)
- 541715 (Research and Development in the Physical, Engineering, and Life Sciences)
- 611430 (Professional and Management Development Training)

**Missing/Recommended Codes:**
- **541513 (Computer Facilities Management Services):** Often used for managed AI infrastructure or platform-as-a-service (PaaS) contracts.
- **541990 (All Other Professional, Scientific, and Technical Services):** A "catch-all" frequently used for high-end niche consulting like AI Ethics or specialized workflow design.
- **541330 (Engineering Services):** Specifically relevant if the "Rapid MVP" involves any hardware integration or systems engineering.
- **561110 (Office Administrative Services):** Occasionally used for OCM contracts focused on administrative efficiency.

---

## 2. Signal-to-Noise: Scoring Algorithm
The current scoring system (Budget 40%, Client Quality 40%, Keywords 20%) has a significant "missing data" vulnerability.

*   **The Budget Blind Spot (40% Weight):** Since SAM.gov listings rarely include a budget until the award stage, a 40% weight on a field that defaults to 0 will suppress potentially massive opportunities. High-relevance, high-value "Sources Sought" notices will score poorly.
*   **Keyword Under-weighting (20% Weight):** For a precision firm like LFG, the technical fit (AI, OCM) is more predictive of success than the "Client Quality" score. 
*   **Recommendation:** Inverse the weighting.
    *   **Keywords (50%):** Use a tiered keyword list (e.g., "AI + Workflow" = 10 pts, "IT Support" = 1 pt).
    *   **Procurement Type (30%):** Reward "Sources Sought" or "Presolicitation" to capture the timing advantage.
    *   **Client/Budget (20%):** Treat as secondary filters.

---

## 3. Timing: Capture in the Procurement Cycle
SAM.gov is often "too late" for full-and-open competition if you aren't already talking to the agency.

*   **Standard Path:** SAM.gov typically lists **Active Notices**.
*   **The Gap:** By the time a "Combined Synopsis/Solicitation" hits SAM.gov, the requirements are often baked.
*   **Opportunity:** The tool must specifically flag **Sources Sought (SS)** and **Requests for Information (RFI)**. These are the "Early Warning" signals where LFG can influence the SOW or push for an SDVOSB set-aside.

---

## 4. Competition: SDVOSB Strategy
Leveraging the SDVOSB status is LFG's greatest competitive advantage.

*   **The Strategy:** The scraper should prioritize opportunities where the "Setaside" field is NOT yet determined but the agency has a history of SDVOSB awards. 
*   **Direct Awards:** For MVPs under the Simplified Acquisition Threshold (SAT), the scraper should look for opportunities where LFG can pitch a direct/sole-source award based on their unique AI capability.

---

## 5. Gaps: Missing Sources
Beyond SAM.gov, the following sources are critical for a firm focused on "Rapid MVPs" and "AI":

1.  **SBIR.gov:** Direct funding for AI R&D and MVP development. Small Business Innovation Research (SBIR) Phase I/II are perfect for "Rapid MVP" teams.
2.  **Tradewinds Solutions Marketplace:** An AI-specific vehicle for the DoD (CDAO). This is a "must-have" for any AI-focused federal vendor.
3.  **Agency-Specific Portals:** 
    *   **GSA eBuy:** (Requires a GSA Schedule, but critical for OCM/IT).
    *   **NASA SEWP:** High volume for IT services.
4.  **Forecasts:** Acquisition forecasts (e.g., DHS, HHS) provide 6–18 months' lead time before a SAM.gov posting.

---

## 6. Concrete Improvements

1.  **Implement Boolean Logic in Keyword Scoring:** Instead of a flat match, score higher for combinations (e.g., `AI` AND `Change Management`).
2.  **Add "Place of Performance" Filtering:** If OCM requires onsite presence, filter for locations LFG can realistically support to avoid wasted effort.
3.  **Automate "Competitor Tracking":** Scrape the "Award" notices for the same NAICS codes to see which firms are winning AI/OCM work. This identifies potential subcontracting partners.
4.  **Phase Zero Detection:** Create a specific alert for notices containing "Industry Day" or "Draft RFP." These are the highest-value signals for an OCM/AI firm.
5.  **Budget Proxy:** Since "Budget" is often empty, use the **Contract Class** (e.g., "J") or historical agency spending for that NAICS code as a proxy for potential value.

---
**Evaluator:** Sonnet (via Clawdbot)
**Status:** Complete
**Date:** 2025-03-24
