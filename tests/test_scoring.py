from app.services.scoring import passes_threshold, score_signals


def test_scoring_rules_and_threshold():
    score, evidence = score_signals(
        {
            "hiring_spike_engineering": True,
            "ai_initiative": True,
            "cloud_migration": False,
            "acquisition_integration": False,
            "pe_margin_language": True,
        },
        "https://example.com",
        {"hiring_spike_engineering": "hiring aggressively"},
    )
    assert score == 6
    assert len(evidence) == 3
    assert passes_threshold(score)
