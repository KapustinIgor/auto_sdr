import json
import os
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Account, Contact, Message, ResearchBrief, Signal, Workflow
from app.services.guardrails import validate_copy
from app.services.scoring import passes_threshold, score_signals
from app.services.workflow_engine import transition

PROMPT_DIR = Path("prompts")


def process_scoring(db: Session, wf: Workflow):
    text = (wf.metadata_json or {}).get("text", "").lower()
    features = {
        "hiring_spike_engineering": "hiring" in text,
        "ai_initiative": "ai" in text,
        "cloud_migration": "cloud" in text,
        "acquisition_integration": "acquisition" in text or "integration" in text,
        "pe_margin_language": "margin" in text or "pe-backed" in text,
    }
    snippets = {k: text[:240] for k, v in features.items() if v}
    score, evidence = score_signals(features, (wf.metadata_json or {}).get("source_url", ""), snippets)
    account = db.query(Account).filter(Account.id == wf.account_id).first()
    account.score = score
    account.icp_fit = passes_threshold(score)
    for ev in evidence:
        db.add(Signal(
            account_id=wf.account_id,
            feature_key=ev.feature_key,
            feature_value=ev.feature_value,
            score_delta=ev.score_delta,
            evidence_url=ev.evidence_url,
            evidence_snippet=ev.evidence_snippet,
        ))
    wf.state = transition(wf.state, "SCORED")


def process_research(db: Session, wf: Workflow):
    account = db.query(Account).filter(Account.id == wf.account_id).first()
    brief = {
        "account": account.name,
        "why_now": ["AI feature pressure", "Cloud migration backlog"],
        "possible_pains": ["Hiring bottlenecks", "Roadmap slipping"],
        "recommended_angle": "Senior pod for 12+ months tied to delivery outcomes",
    }
    db.add(ResearchBrief(account_id=account.id, brief_json=brief))
    wf.state = transition(wf.state, "RESEARCHED")


def process_draft(db: Session, wf: Workflow):
    contact = db.query(Contact).filter(Contact.id == wf.contact_id).first()
    steps = ["Email1", "FU1", "FU2", "Breakup", "LI_Connect", "LI_Followup"]
    proof_points = json.loads(Path("data/proof_points.json").read_text())
    for step in steps:
        body = f"Hi {contact.name},\n\nNoticed pressure around AI roadmap and delivery capacity. Jaxel builds accountable product squads (5-25 engineers) for 12+ month programs.\n\nWould a 20-min fit check next week be useful? If not, reply unsubscribe.\n\nBest,\nJaxel"
        guard = validate_copy(body, approved_proofs=proof_points["approved"]) 
        status = "DRAFT" if guard["ok"] else "BLOCKED"
        db.add(Message(
            contact_id=contact.id,
            account_id=contact.account_id,
            channel="email" if step.startswith("E") or step.startswith("F") or step == "Breakup" else "linkedin_assisted",
            step=step,
            subject=f"{contact.name} - {step}",
            body=body,
            status=status,
        ))
    wf.state = transition(wf.state, "DRAFTED")
    wf.state = transition(wf.state, "APPROVAL_REQUIRED")


def run_once():
    db: Session = SessionLocal()
    for wf in db.query(Workflow).all():
        if wf.state == "CRAWLED":
            process_scoring(db, wf)
        if wf.state == "SCORED":
            if not db.query(Account).filter(Account.id == wf.account_id).first().icp_fit:
                wf.state = transition(wf.state, "DISQUALIFIED")
            else:
                process_research(db, wf)
        if wf.state == "RESEARCHED":
            process_draft(db, wf)
    db.commit()
    db.close()


if __name__ == "__main__":
    while True:
        run_once()
        time.sleep(20)
