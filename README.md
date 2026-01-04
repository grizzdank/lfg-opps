# LFG Opportunity Finder

Automated discovery and scoring of consulting opportunities for [LFG Consultants](https://lfgconsultants.com/).

## Features

- **Multi-source aggregation**: Freelancer.com (ready), Upwork (pending API approval)
- **Smart scoring**: Budget size (40%) + Client quality (40%) + Keyword match (20%)
- **Interactive CLI dashboard**: Browse, filter, and open opportunities
- **Email digests**: Scheduled notifications with top opportunities
- **Configurable thresholds**: Minimum budget, score filters

## Quick Start

```bash
# Clone and setup
cd ~/Projects/lfg-opps
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your Freelancer.com OAuth token

# Run
python -m src.main           # Interactive dashboard
python -m src.main --quick   # Quick list, top 10
python -m src.main --email   # Send email digest
```

## Configuration

### Freelancer.com Setup
1. Go to [developers.freelancer.com](https://developers.freelancer.com/)
2. Create an application
3. Get your OAuth token
4. Add to `.env`: `FLN_OAUTH_TOKEN=your_token`

### Upwork Setup (Pending)
1. Apply for API access: [support.upwork.com](https://support.upwork.com/hc/en-us/articles/115015857647)
2. Wait for approval (~2 weeks)
3. Add credentials to `.env`

### Scoring Configuration
Edit `.env` to adjust:
```bash
MIN_BUDGET=2500       # Minimum project budget
MIN_SCORE=60          # Minimum score to display
BUDGET_WEIGHT=0.4     # Budget importance (0-1)
CLIENT_WEIGHT=0.4     # Client quality importance (0-1)
KEYWORD_WEIGHT=0.2    # Keyword match importance (0-1)
```

## Keyword Matching

The scorer looks for keywords matching LFG's services:

| Category | Keywords |
|----------|----------|
| AI/Workflow | ai, automation, chatbot, gpt, workflow, process automation |
| MVP Development | mvp, prototype, rapid development, startup, agile |
| Change Management | change management, digital transformation, training, adoption |
| SMB Focus | small business, smb, startup, scale, efficiency |

## CLI Commands

```bash
# Interactive dashboard
python -m src.main

# Quick list (non-interactive)
python -m src.main --quick --limit 20

# Send email digest
python -m src.main --email

# Run on schedule (every 60 minutes by default)
python -m src.main --schedule --email

# Dry run (fetch and score only)
python -m src.main --dry-run
```

## Project Structure

```
lfg-opps/
├── src/
│   ├── config.py          # Settings and keywords
│   ├── models.py          # Data models
│   ├── main.py            # CLI entry point
│   ├── sources/
│   │   ├── base.py        # Abstract source
│   │   ├── freelancer.py  # Freelancer.com API
│   │   └── upwork.py      # Upwork API (stub)
│   ├── scoring/
│   │   └── scorer.py      # Scoring engine
│   └── output/
│       ├── cli.py         # Terminal dashboard
│       └── email.py       # Email digest
├── data/                  # SQLite DB (auto-created)
├── .env                   # Your credentials
└── requirements.txt
```

## Next Steps

1. **Apply for Upwork API today** - [Request here](https://support.upwork.com/hc/en-us/articles/115015857647)
2. Get Freelancer.com OAuth token
3. Configure email settings for digests
4. Run `python -m src.main --quick` to test

## License

Private - LFG Consultants
