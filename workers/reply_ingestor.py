import email
import json
import os
import time
from datetime import datetime

from imapclient import IMAPClient
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Contact, Reply, Suppression, Workflow
from app.services.guardrails import detect_unsubscribe


def classify_reply(body: str):
    lowered = body.lower()
    if detect_unsubscribe(lowered):
        return {"intent": "unsubscribe", "next_action": "suppress_and_stop"}
    if any(k in lowered for k in ["interested", "learn more", "can we chat"]):
        return {
            "intent": "interested",
            "next_action": "qualify",
            "qualification_questions": [
                "What are the top 1-2 roadmap outcomes this quarter?",
                "Would a 5-25 engineer pod model for 12+ months fit your plan?",
            ],
        }
    if any(k in lowered for k in ["not now", "later", "q4"]):
        return {"intent": "nurture", "next_action": "set_followup"}
    return {"intent": "unknown", "next_action": "manual_review"}


def poll_once():
    host = os.getenv("IMAP_HOST")
    user = os.getenv("IMAP_USER")
    password = os.getenv("IMAP_PASSWORD")
    mailbox = os.getenv("IMAP_MAILBOX", "INBOX")
    if not host or not user or not password:
        return

    db: Session = SessionLocal()
    with IMAPClient(host, ssl=True) as client:
        client.login(user, password)
        client.select_folder(mailbox)
        messages = client.search(["UNSEEN"])
        fetched = client.fetch(messages, [b"RFC822"])

        for uid, data in fetched.items():
            raw = data[b"RFC822"]
            parsed = email.message_from_bytes(raw)
            from_address = parsed.get("From", "")
            body = ""
            if parsed.is_multipart():
                for part in parsed.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = parsed.get_payload(decode=True).decode(errors="ignore")

            contact = db.query(Contact).filter(Contact.email.ilike(f"%{from_address.split('<')[0].strip()}%")).first()
            if not contact:
                continue
            classification = classify_reply(body)
            db.add(Reply(
                contact_id=contact.id,
                account_id=contact.account_id,
                received_at=datetime.utcnow(),
                raw_body=body,
                classification_json=classification,
            ))
            wf = db.query(Workflow).filter(Workflow.contact_id == contact.id).first()
            if wf:
                wf.state = "REPLIED"
                if classification["intent"] == "unsubscribe":
                    db.merge(Suppression(email_or_domain=contact.email, reason="unsubscribe via imap"))
                    wf.state = "DISQUALIFIED"
                elif classification["intent"] == "interested":
                    wf.state = "QUALIFYING"
                elif classification["intent"] == "nurture":
                    wf.state = "NURTURE"
        db.commit()
    db.close()


if __name__ == "__main__":
    while True:
        poll_once()
        time.sleep(60)
