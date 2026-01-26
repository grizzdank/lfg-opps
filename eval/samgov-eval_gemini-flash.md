# Evaluation of `lfg-opps` SAM.gov Scraper Effectiveness

**Date:** 2024-05-22
**Evaluator:** Gemini Flash (Subagent)
**Subject:** Federal Contract Discovery Strategy for LFG Consultants

---

## Executive Summary
The current implementation of `lfg-opps` provides a solid foundation for programmatic discovery of federal opportunities. However, it is heavily reliant on "bottom-of-the-funnel" data (formal solicitations) and faces significant "signal-of-missing-data" issues (budget defaults). To move from a reactive scraper to a proactive discovery engine, LFG should expand its capture of pre-solicitation signals and refine its scoring to account for the unique data hygiene of SAM.gov.

---

## 1. Coverage: NAICS Analysis
The selected 11 NAICS codes are highly relevant but slightly skewed toward traditional IT and management consulting.

**Current Strengths:**
- Covers the "Big Three" for AI/IT: **541511** (Programming), **541512** (Systems Design), and **541519** (Other Computer Related).
- Solid OCM representation: **541611** (Admin & General Management) and **541612** (HR Consulting).

**Missing/Recommended Codes:**
- **541513 (Computer Facilities Management Services):** Often used for long-term AI infrastructure/ops support.
- **541613 (Marketing Consulting Services):** Increasingly used for "Internal AI Evangelism" and large-scale OCM/communications projects.
- **541330 (Engineering Services):** Used by DoD/NASA for technical R&D and MVP development that looks like "AI Engineering."
- **541990 (All Other Professional, Scientific, and Technical Services):** A "catch-all" where innovative AI pilots are sometimes classified.

---

## 2. Signal-to-Noise: Scoring Algorithm
The 40/40/20 split has a structural flaw due to SAM.gov data entry habits.

- **The Budget Problem (40% Weighting):** Since budget is missing from a vast majority of SAM listings (especially at the RFI/Combined Synopsis stage), 40% of the score is effectively neutralized or biased toward the few entities that provide estimates. 
    - *Correction:* The algorithm should penalize "Missing Budget" less or use historical agency spending (FPDS data) as a proxy for "Projected Value."
- **Client Quality (40% Weighting):** Defining "Quality" is subjective. If based on "Past Spend with SDVOSBs" or "Prompt Payment," this is high-value. If based on agency size, it might ignore lucrative niche opportunities in smaller agencies (e.g., Peace Corps, NRC).
- **Keyword Match (20% Weighting):** This is undervalued. In the consulting world, a specific keyword match (e.g., "Generative AI Governance") is a much stronger indicator of fit than a generic $1M budget.

---

## 3. Timing: The Procurement Cycle
SAM.gov is often "too late" for MVP-style work if you only look at "Solicitations."

- **Current Gap:** If the scraper only looks at `Notice Type: Solicitation`, LFG is competing on price/compliance against incumbents.
- **Critical Improvement:** The scraper must prioritize `Notice Type: Special Notice`, `Sources Sought`, and `Presolicitation`. For high-end consulting (AI/OCM), the win happens during the RFI (Request for Information) phase where LFG can help shape the SOW (Statement of Work).

---

## 4. Competition: SDVOSB Strategy
Leveraging the SDVOSB status is LFG's greatest "unfair advantage."

- **Set-Aside Filtering:** The scraper should explicitly flag "Total SDVOSB Set-Aside" but also "Small Business Set-Aside" where SDVOSB preference applies.
- **Full-and-Open Strategy:** LFG should use the scraper to identify large primes (e.g., Booz Allen, Deloitte) winning "Full and Open" contracts in these NAICS codes to target them for **subcontracting** roles specifically for the AI/OCM niche.

---

## 5. Gaps: Missing Sources
Beyond SAM.gov, the following are "dark" to the current tool:

1. **GSA eBuy:** Many AI/OCM tasks are run through MAS (Multiple Award Schedule) and are never posted on SAM.gov. (Requires a GSA Schedule).
2. **SBIR/STTR (Small Business Innovation Research):** Prime territory for "Rapid MVP Development." Agencies like AFWERX or DARPA fund AI prototypes here.
3. **Tradewinds Solutions Marketplace:** Specifically for AI; allows companies to upload 5-minute video pitches for DoD discovery.
4. **HHS BuySmarter / NASA SEWP:** Specialized portals often used for high-tech acquisitions.

---

## 6. Recommendations for Improvement

1. **Shift Weighting:** Change scoring to **Keyword (40%), Client/Agency Profile (40%), Budget (20%)**. Use keyword proximity (e.g., "AI" near "Change Management") to boost scores.
2. **Add "Phase" Scoring:** Weight "Sources Sought" higher than "Solicitations" to encourage early-stage engagement.
3. **Agency Heatmapping:** Incorporate data from USASpending.gov to identify which agencies are actually *buying* AI/OCM services right now (e.g., VA, DHS, and USDA are currently active in AI).
4. **NLP over Regex:** Move beyond simple keyword matching to NLP-based "Intent Analysis" to distinguish between "Buying an AI software license" and "Requiring AI Workflow Design."
5. **Teaming Discovery:** Add a feature to identify "Awarded" contracts. This allows LFG to find "Subcontracting" opportunities shortly after a Large Prime wins a major base contract.

---
**Status:** Evaluation Complete.
**File Path:** `/home/daveg/projects/lfg-opps/eval/samgov-eval_gemini-flash.md`