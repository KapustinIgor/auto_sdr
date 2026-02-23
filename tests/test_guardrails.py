from app.services.guardrails import detect_unsubscribe, validate_copy


def test_guardrails_blocks_bad_claims_and_requires_unsubscribe():
    bad = "We guarantee results and are the cheapest provider."
    result = validate_copy(bad)
    assert not result["ok"]
    assert "missing_unsubscribe_instruction" in result["violations"]


def test_unsubscribe_detection():
    assert detect_unsubscribe("Please unsubscribe me")
