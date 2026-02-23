import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Account, Approval, AuditLog, Contact, Message, Reply, Signal, Suppression, Workflow
from app.schemas import AccountCreate, ApprovalAction, ContactCreate
from app.services.guardrails import detect_unsubscribe
from app.services.scoring import passes_threshold
from app.services.workflow_engine import compute_next_action, transition

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Jaxel AI SDR Agent")
templates = Jinja2Templates(directory="app/templates")


def log_audit(db: Session, actor: str, action: str, entity_type: str, entity_id: str, payload: dict):
    db.add(AuditLog(actor=actor, action=action, entity_type=entity_type, entity_id=str(entity_id), payload_json=payload))
    db.commit()


@app.get("/health")
def health():
    return {"status": "ok", "service": "api_gateway"}


@app.post("/accounts")
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    account = Account(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    log_audit(db, "system", "create_account", "account", account.id, payload.model_dump())
    return account


@app.post("/contacts")
def create_contact(payload: ContactCreate, db: Session = Depends(get_db)):
    contact = Contact(**payload.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    wf = Workflow(account_id=contact.account_id, contact_id=contact.id, state="DISCOVERED")
    db.add(wf)
    db.commit()
    return contact


@app.get("/accounts")
def list_accounts(db: Session = Depends(get_db)):
    rows = db.query(Account).all()
    result = []
    for account in rows:
        top_evidence = db.query(Signal).filter(Signal.account_id == account.id).order_by(Signal.score_delta.desc()).limit(3).all()
        result.append({
            "id": account.id,
            "name": account.name,
            "score": account.score,
            "top_evidence": [{"feature": s.feature_key, "snippet": s.evidence_snippet} for s in top_evidence],
        })
    return result


@app.get("/research/{account_id}")
def get_research(account_id: int, db: Session = Depends(get_db)):
    from app.models import ResearchBrief

    brief = db.query(ResearchBrief).filter(ResearchBrief.account_id == account_id).order_by(ResearchBrief.created_at.desc()).first()
    if not brief:
        raise HTTPException(404, "research not found")
    return brief


@app.get("/messages")
def list_messages(db: Session = Depends(get_db)):
    return db.query(Message).order_by(Message.created_at.desc()).all()


@app.post("/approvals/{message_id}")
def approve_message(message_id: int, payload: ApprovalAction, db: Session = Depends(get_db)):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(404, "message not found")
    approval = Approval(message_id=msg.id, reviewer=payload.reviewer, status=payload.status, notes=payload.notes)
    db.add(approval)
    if payload.status == "APPROVED":
        msg.status = "APPROVED"
        wf = db.query(Workflow).filter(Workflow.contact_id == msg.contact_id).first()
        if wf:
            wf.state = transition(wf.state, "APPROVED") if wf.state != "APPROVED" else "APPROVED"
            wf.next_action_at = compute_next_action(wf.state)
    db.commit()
    return {"ok": True}


@app.post("/send/{message_id}")
def mark_sent(message_id: int, db: Session = Depends(get_db)):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(404, "message not found")
    if msg.status != "APPROVED":
        raise HTTPException(400, "message must be approved")
    msg.status = "SENT"
    wf = db.query(Workflow).filter(Workflow.contact_id == msg.contact_id).first()
    if wf:
        wf.state = "SENT"
        wf.next_action_at = compute_next_action("SENT")
    db.commit()
    return {"ok": True}


@app.get("/replies")
def list_replies(db: Session = Depends(get_db)):
    return db.query(Reply).order_by(Reply.received_at.desc()).all()


@app.post("/suppression")
def add_suppression(email_or_domain: str = Form(...), reason: str = Form(...), db: Session = Depends(get_db)):
    db.merge(Suppression(email_or_domain=email_or_domain, reason=reason))
    db.commit()
    return {"ok": True}


@app.post("/webhook/reply")
def ingest_reply(contact_id: int = Form(...), account_id: int = Form(...), body: str = Form(...), db: Session = Depends(get_db)):
    classification = {
        "intent": "unsubscribe" if detect_unsubscribe(body) else "unknown",
        "next_action": "suppress" if detect_unsubscribe(body) else "qualify",
    }
    reply = Reply(contact_id=contact_id, account_id=account_id, raw_body=body, classification_json=classification)
    db.add(reply)
    if classification["intent"] == "unsubscribe":
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if contact and contact.email:
            db.merge(Suppression(email_or_domain=contact.email, reason="unsubscribe reply"))
        wf = db.query(Workflow).filter(Workflow.contact_id == contact_id).first()
        if wf:
            wf.state = "DISQUALIFIED"
    db.commit()
    return classification


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, db: Session = Depends(get_db)):
    accounts = db.query(Account).all()
    messages = db.query(Message).order_by(Message.created_at.desc()).limit(30).all()
    replies = db.query(Reply).order_by(Reply.received_at.desc()).limit(30).all()
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "accounts": accounts,
            "messages": messages,
            "replies": replies,
        },
    )


@app.get("/analytics/summary")
def analytics_summary(db: Session = Depends(get_db)):
    total_accounts = db.query(Account).count()
    qualified_accounts = db.query(Account).filter(Account.score >= 5).count()
    replies = db.query(Reply).count()
    meetings = db.query(Workflow).filter(Workflow.state == "MEETING_BOOKED").count()
    return {
        "total_accounts": total_accounts,
        "qualified_accounts": qualified_accounts,
        "reply_rate_proxy": replies,
        "meetings_booked": meetings,
    }
