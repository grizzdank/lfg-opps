# LFG Opportunity Finder - Implementation Plan

## Overview

Automated system to discover, score, and surface consulting opportunities from freelance platforms for [LFG Consultants](https://lfgconsultants.com/).

### Target Services
- Organizational Change Management (OCM)
- AI Workflow Design & Integration
- Rapid MVP Development

### Constraints
- **API Approach**: Official APIs only (no scraping)
- **Budget**: $0 - custom build with free tiers
- **Minimum Project Budget**: $2,500+
- **Notifications**: Email digest + Local CLI/dashboard
- **Tech Stack**: Python

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LFG Opportunity Finder                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Data Sources │    │   Scoring    │    │   Output     │       │
│  │              │───▶│   Engine     │───▶│   Layer      │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  • Freelancer.com    • Budget Score      • CLI Dashboard        │
│  • Upwork API        • Client Score      • Email Digest         │
│  • (Future sources)  • Keyword Match     • JSON Export          │
│                      • Freshness                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Sources

### 1. Freelancer.com API (Primary)
- **SDK**: `pip install freelancersdk` ([GitHub](https://github.com/freelancer/freelancer-sdk-python))
- **Auth**: OAuth2 token required
- **Features**: Project search, budget info, employer details
- **Sandbox**: Available at `freelancer-sandbox.com`
- **Status**: SDK last updated Dec 2022, functional

### 2. Upwork API (Secondary)
- **Docs**: [Upwork Developer](https://www.upwork.com/developer)
- **Auth**: OAuth 2.0, requires API key application
- **Approval**: 2-week review process
- **Limits**: 40K requests/day
- **Requirements**:
  - Complete profile with valid address
  - Clear use case description
  - Agree to reasonable request volume

**Note**: Apply for Upwork API access early - it's the highest-volume platform.

---

## Scoring Algorithm

### Composite Score Formula
```
total_score = (budget_score * 0.4) + (client_score * 0.4) + (keyword_score * 0.2)
```

### Budget Score (40% weight)
| Budget Range | Score |
|--------------|-------|
| $2,500 - $5,000 | 60 |
| $5,000 - $10,000 | 80 |
| $10,000 - $25,000 | 95 |
| $25,000+ | 100 |
| Hourly ($50+/hr) | 85 |

### Client Quality Score (40% weight)
| Factor | Max Points |
|--------|------------|
| Client rating (4.5+) | 30 |
| Payment verified | 20 |
| Previous hires (5+) | 20 |
| Money spent ($10K+) | 15 |
| Repeat client potential | 15 |

### Keyword Match Score (20% weight)
**High-value keywords** (20 pts each, max 100):
- "AI", "artificial intelligence", "machine learning"
- "MVP", "prototype", "rapid development"
- "change management", "digital transformation"
- "workflow automation", "process improvement"
- "SMB", "small business", "startup"

---

## Project Structure

```
lfg-opportunity-finder/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration & environment
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── base.py            # Abstract source class
│   │   ├── freelancer.py      # Freelancer.com integration
│   │   └── upwork.py          # Upwork integration
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── scorer.py          # Main scoring engine
│   │   ├── budget.py          # Budget scoring logic
│   │   ├── client.py          # Client quality scoring
│   │   └── keywords.py        # Keyword matching
│   ├── output/
│   │   ├── __init__.py
│   │   ├── cli.py             # Terminal dashboard
│   │   ├── email.py           # Email digest sender
│   │   └── export.py          # JSON/CSV export
│   └── main.py                # Entry point & scheduler
├── tests/
│   └── ...
├── data/
│   ├── opportunities.db       # SQLite for persistence
│   └── seen_ids.json          # Deduplication cache
├── .env.example
├── requirements.txt
└── README.md
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Set up project structure and dependencies
- [ ] Implement Freelancer.com API integration
- [ ] Create base data models for opportunities
- [ ] Build basic CLI output

### Phase 2: Scoring Engine (Week 2)
- [ ] Implement budget scoring module
- [ ] Implement client quality scoring
- [ ] Implement keyword matching
- [ ] Create composite score calculator

### Phase 3: Output & Notifications (Week 3)
- [ ] Build CLI dashboard with Rich library
- [ ] Implement email digest (using `smtplib` or free tier services)
- [ ] Add SQLite persistence for history
- [ ] Implement deduplication

### Phase 4: Upwork Integration (Week 4+)
- [ ] Apply for Upwork API access (do this in Phase 1!)
- [ ] Implement Upwork data source
- [ ] Unify scoring across platforms
- [ ] Add comparison views

---

## Key Dependencies

```txt
# requirements.txt
freelancersdk>=0.1.20       # Freelancer.com API
httpx>=0.25.0               # Modern HTTP client
pydantic>=2.0               # Data validation
rich>=13.0                  # CLI dashboard
python-dotenv>=1.0          # Environment management
schedule>=1.2               # Job scheduling
sqlite-utils>=3.35          # Easy SQLite
jinja2>=3.1                 # Email templates
```

---

## Configuration

```python
# .env.example
# Freelancer.com
FLN_OAUTH_TOKEN=your_token_here
FLN_URL=https://www.freelancer.com  # or freelancer-sandbox.com

# Upwork (after approval)
UPWORK_CLIENT_ID=your_client_id
UPWORK_CLIENT_SECRET=your_secret
UPWORK_ACCESS_TOKEN=your_token

# Email (optional - for digest)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_TO=dave@lfgconsultants.com

# Scoring thresholds
MIN_BUDGET=2500
MIN_SCORE=60
MAX_RESULTS_PER_RUN=50
```

---

## CLI Dashboard Example

```
╭─────────────────────────────────────────────────────────────────╮
│             LFG Opportunity Finder - Jan 4, 2026                │
├─────────────────────────────────────────────────────────────────┤
│  Found: 23 opportunities │ Scored 85+: 7 │ New today: 12        │
╰─────────────────────────────────────────────────────────────────╯

┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┓
┃ Score  ┃ Title                                 ┃ Budget  ┃ Source┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━┩
│ 🟢 94  │ AI Workflow Automation for HR Dept    │ $15,000 │ UW    │
│ 🟢 91  │ MVP Development - Fintech Startup     │ $12,000 │ FL    │
│ 🟢 88  │ Digital Transformation Consultant     │ $8,500  │ UW    │
│ 🟡 76  │ Process Automation - Manufacturing    │ $5,000  │ FL    │
│ 🟡 72  │ Change Management for ERP Migration   │ $4,500  │ UW    │
└────────┴───────────────────────────────────────┴─────────┴───────┘

[d] Details  [o] Open in browser  [n] Next page  [q] Quit
```

---

## Immediate Action Items

1. **Apply for Upwork API access today** - [Request API Key](https://support.upwork.com/hc/en-us/articles/115015857647-How-to-request-an-API-key-from-Upwork)
   - Use LFG Consultants company profile
   - Describe use case: "Internal tool to monitor relevant consulting opportunities"
   - 2-week approval timeline

2. **Create Freelancer.com developer account**
   - Sign up at [developers.freelancer.com](https://developers.freelancer.com/)
   - Generate OAuth token
   - Test with sandbox environment first

3. **Set up project repository**
   - Initialize Python project
   - Configure virtual environment
   - Set up `.env` with sandbox credentials

---

## Future Enhancements (Post-MVP)

- **Additional Sources**: Toptal (if accepted as talent), LinkedIn job alerts, AngelList
- **AI-Powered Proposal Drafts**: Use Claude API to generate proposal templates
- **Client Research**: Auto-lookup company info for high-scored opportunities
- **Response Tracking**: Track which scored opportunities you applied to and outcomes
- **Slack/Discord Integration**: Real-time notifications beyond email

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Upwork API rejection | Primary focus on Freelancer.com; reapply with revised use case |
| API rate limits | Implement backoff, cache results, run during off-peak hours |
| Stale SDK | Freelancer SDK works but may need patches; fork if needed |
| Low match volume | Expand keyword list, lower minimum budget threshold temporarily |

---

## Success Metrics

- **Target**: Surface 5-10 high-quality opportunities (score 80+) per week
- **Efficiency**: Reduce manual job board browsing by 80%
- **Conversion**: Track proposal → interview → contract rate

---

*Plan created: January 4, 2026*
*For: LFG Consultants Opportunity Discovery Automation*
