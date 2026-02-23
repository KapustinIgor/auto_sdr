import pytest
from app.services.workflow_engine import WorkflowError, transition


def test_workflow_transition_valid_and_invalid():
    assert transition("DISCOVERED", "CRAWLED") == "CRAWLED"
    with pytest.raises(WorkflowError):
        transition("DISCOVERED", "SENT")
