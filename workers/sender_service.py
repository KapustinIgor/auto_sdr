import os
import smtplib
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Contact, Message, Touch, Workflow
from app.services.workflow_engine import compute_next_action


def send_approved_messages():
    db: Session = SessionLocal()
    dry_run = os.getenv("SMTP_DRY_RUN", "true").lower() == "true"
    host = os.getenv("SMTP_HOST", "localhost")
    port = int(os.getenv("SMTP_PORT", "1025"))
    sender = os.getenv("SMTP_FROM", "sdr@example.com")

    for msg in db.query(Message).filter(Message.status == "APPROVED", Message.channel == "email").all():
        contact = db.query(Contact).filter(Contact.id == msg.contact_id).first()
        if not contact:
            continue
        provider_id = f"dry-{msg.id}"
        status = "SENT_DRY_RUN"
        if not dry_run:
            mail = EmailMessage()
            mail["From"] = sender
            mail["To"] = contact.email
            mail["Subject"] = msg.subject
            mail.set_content(msg.body)
            with smtplib.SMTP(host, port) as client:
                client.send_message(mail)
            provider_id = f"smtp-{msg.id}"
            status = "SENT"
        msg.status = "SENT"
        db.add(Touch(message_id=msg.id, provider_msg_id=provider_id, status=status))
        wf = db.query(Workflow).filter(Workflow.contact_id == msg.contact_id).first()
        if wf:
            wf.state = "AWAITING_REPLY"
            wf.next_action_at = compute_next_action("AWAITING_REPLY")
    db.commit()
    db.close()


if __name__ == "__main__":
    send_approved_messages()
