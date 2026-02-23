from dataclasses import dataclass
from datetime import datetime


@dataclass
class SignalEvidence:
    feature_key: str
    feature_value: str
    score_delta: float
    evidence_url: str
    evidence_snippet: str
    timestamp: datetime


RULES = {
    "hiring_spike_engineering": 3,
    "ai_initiative": 2,
    "cloud_migration": 2,
    "acquisition_integration": 2,
    "pe_margin_language": 1,
}


def score_signals(features: dict[str, bool], source_url: str, snippets: dict[str, str]):
    evidence: list[SignalEvidence] = []
    score = 0.0
    now = datetime.utcnow()
    for key, delta in RULES.items():
        if features.get(key):
            score += delta
            evidence.append(
                SignalEvidence(
                    feature_key=key,
                    feature_value="true",
                    score_delta=delta,
                    evidence_url=source_url,
                    evidence_snippet=snippets.get(key, ""),
                    timestamp=now,
                )
            )
    return min(score, 10), evidence


def passes_threshold(score: float, threshold: float = 5) -> bool:
    return score >= threshold
