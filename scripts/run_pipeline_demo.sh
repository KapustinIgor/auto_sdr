#!/usr/bin/env bash
set -euo pipefail
python scripts/seed_demo.py
python -c "from workers.crawler_worker import run_once; run_once(); print('crawl complete')"
python -c "from workers.workflow_worker import run_once; run_once(); print('score/research/draft complete')"
python - <<'PY'
from app.database import SessionLocal
from app.models import Message

db = SessionLocal()
for m in db.query(Message).filter(Message.status=='DRAFT').limit(3).all():
    m.status='APPROVED'
db.commit()
print('approved first 3 drafts')
PY
python workers/sender_service.py
python - <<'PY'
from app.database import SessionLocal
from app.models import Contact, Reply
from workers.reply_ingestor import classify_reply

db = SessionLocal()
contact = db.query(Contact).first()
classification = classify_reply('Interested. Can we chat next week?')
reply = Reply(contact_id=contact.id, account_id=contact.account_id, raw_body='Interested. Can we chat next week?', classification_json=classification)
db.add(reply)
db.commit()
print('reply classified', classification)
PY
