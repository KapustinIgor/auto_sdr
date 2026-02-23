# Jaxel AI SDR Agent (Open Source, Self-Hosted)

Production-minded AI SDR system optimized for **qualified enterprise conversations per 100 high-fit accounts**.

## What this repo includes

- FastAPI API Gateway + basic HTML Admin UI
- Python workflow engine/state machine
- Crawler worker (Playwright-ready pattern + BeautifulSoup parsing + MinIO HTML snapshots)
- Rule-based signal scoring with evidence and thresholding
- RAG-ready research agent (FAISS + Ollama)
- Copy agent (JSON schema prompts, email sequence + LinkedIn assisted copy)
- Guardrails engine with deterministic policy checks
- SMTP sender service with dry-run mode
- IMAP reply ingestion + classification + unsubscribe suppression
- Analytics endpoint + audit logging
- Docker Compose local stack (Postgres, Redis, MinIO, Ollama, MailHog)

## ICP hard-coded assumptions (Jaxel)

- Account fit logic, scoring triggers, and sequence content are tuned for:
  - 100–2,000 employees, $20M–$500M, US primary
  - Enterprise/mid-market technical buyers (CTO, VP Eng, CIO, Head of Product, COO)
  - Engagement profile: $500K–$3M ACV, 5–25 engineers, 12+ months

## Architecture

### Services
1. `api_gateway` (`app/main.py`)
2. `workflow_engine` (`app/services/workflow_engine.py`, `workers/workflow_worker.py`)
3. `crawler_worker` (`workers/crawler_worker.py`)
4. `signal_engine` (`app/services/scoring.py`, `workers/signal_engine.py`)
5. `research_agent` (`workers/research_agent.py`)
6. `copy_agent` (`workers/copy_agent.py`)
7. `guardrails_engine` (`app/services/guardrails.py`)
8. `sender_service` (`workers/sender_service.py`)
9. `reply_ingestor` (`workers/reply_ingestor.py`)
10. `reply_classifier` (`workers/reply_classifier.py`)
11. `qualifier_agent` (`workers/qualifier_agent.py`)
12. `analytics` (`/analytics/summary` endpoint)

### Lead state machine

`DISCOVERED → CRAWLED → SCORED → RESEARCHED → DRAFTED → APPROVAL_REQUIRED → APPROVED → SENT → AWAITING_REPLY`

Replies transition to:
`REPLIED → (QUALIFYING | DISQUALIFIED | NURTURE | MEETING_BOOKED)`

## Guardrails

Hard checks:
- no guarantees
- no invented logos/case studies/competitor claims
- no cheap/rate language
- include unsubscribe instruction
- unsubscribe replies are auto-suppressed and workflows stopped

## Setup

```bash
cp .env.example .env
docker compose up --build -d
```

Open:
- API docs: http://localhost:8000/docs
- Admin UI: http://localhost:8000/admin
- MailHog UI: http://localhost:8025
- MinIO UI: http://localhost:9001

## Demo end-to-end commands

### 1) Seed accounts/contacts
```bash
python scripts/seed_demo.py
```

### 2) Crawl + score
```bash
python -c "from workers.crawler_worker import run_once; run_once()"
python -c "from workers.workflow_worker import run_once; run_once()"
```

### 3) Generate research + drafts
```bash
python -c "from workers.workflow_worker import run_once; run_once()"
```

### 4) Approve drafts
```bash
python - <<'PY'
from app.database import SessionLocal
from app.models import Message

db = SessionLocal()
for m in db.query(Message).filter(Message.status=='DRAFT').all():
    m.status='APPROVED'
db.commit()
print('approved')
PY
```

### 5) Send (dry run)
```bash
python workers/sender_service.py
```

### 6) Ingest sample reply + classify
```bash
python - <<'PY'
from workers.reply_ingestor import classify_reply
print(classify_reply('Interested. Can we chat next week?'))
print(classify_reply('Please unsubscribe me.'))
PY
```

## Admin features implemented

- List accounts with score + top evidence (`GET /accounts`, `/admin`)
- View research brief (`GET /research/{account_id}`)
- View/edit message drafts (`GET /messages`, update via DB/API extension)
- Approve/reject drafts (`POST /approvals/{message_id}`)
- Send approved messages (`POST /send/{message_id}` + `workers/sender_service.py`)
- View replies with classification (`GET /replies`, `/admin`)
- Add suppression entries (`POST /suppression`)

## Testing

```bash
pytest -q
```

Includes tests for:
- scoring model
- guardrails
- workflow transitions

## Notes

- LinkedIn is intentionally assisted-mode only (copy generation, no automation).
- Wappalyzer CLI integration can be added in crawler worker as optional enrichment hook.
- Prompts are versioned under `/prompts`.
- Approved proof points live in `/data/proof_points.json`.
