import re

FORBIDDEN_PATTERNS = [
    r"guarantee",
    r"cheapest",
    r"lowest rate",
    r"we helped your competitor",
]

REQUIRED_UNSUBSCRIBE = "unsubscribe"


def validate_copy(text: str, approved_proofs: list[str] | None = None):
    violations = []
    lowered = text.lower()
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, lowered):
            violations.append(f"forbidden_claim:{pattern}")

    if "competitor" in lowered and approved_proofs:
        if not any(proof.lower() in lowered for proof in approved_proofs):
            violations.append("unapproved_competitor_reference")

    if REQUIRED_UNSUBSCRIBE not in lowered:
        violations.append("missing_unsubscribe_instruction")

    return {"ok": len(violations) == 0, "violations": violations}


def detect_unsubscribe(reply_body: str) -> bool:
    body = reply_body.lower()
    return any(keyword in body for keyword in ["unsubscribe", "stop", "remove me", "do not contact"])
