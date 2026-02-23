from datetime import datetime, timedelta

ALLOWED_TRANSITIONS = {
    "DISCOVERED": ["CRAWLED"],
    "CRAWLED": ["SCORED"],
    "SCORED": ["RESEARCHED", "DISQUALIFIED"],
    "RESEARCHED": ["DRAFTED"],
    "DRAFTED": ["APPROVAL_REQUIRED", "APPROVED"],
    "APPROVAL_REQUIRED": ["APPROVED", "DRAFTED"],
    "APPROVED": ["SENT"],
    "SENT": ["AWAITING_REPLY"],
    "AWAITING_REPLY": ["REPLIED"],
    "REPLIED": ["QUALIFYING", "DISQUALIFIED", "NURTURE", "MEETING_BOOKED"],
    "QUALIFYING": ["MEETING_BOOKED", "NURTURE", "DISQUALIFIED"],
}


class WorkflowError(ValueError):
    pass


def transition(current_state: str, next_state: str) -> str:
    if next_state not in ALLOWED_TRANSITIONS.get(current_state, []):
        raise WorkflowError(f"Invalid transition {current_state} -> {next_state}")
    return next_state


def compute_next_action(state: str, now: datetime | None = None, cooldown_days: int = 3):
    now = now or datetime.utcnow()
    if state in {"SENT", "AWAITING_REPLY"}:
        return now + timedelta(days=cooldown_days)
    if state == "QUALIFYING":
        return now + timedelta(days=1)
    return None
