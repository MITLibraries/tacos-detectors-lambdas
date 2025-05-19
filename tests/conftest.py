import json

import pytest


@pytest.fixture(autouse=True)
def _test_env(monkeypatch):
    monkeypatch.setenv("WORKSPACE", "test")


@pytest.fixture
def valid_event():
    """Valid event payload for an HTTP invocation."""
    return {
        "body": json.dumps({"action": "ping"}),
        "requestContext": {"http": {"method": "POST"}},
    }


@pytest.fixture
def nonsense_event():
    """Nonsense event payload for an HTTP invocation."""
    return {
        "body": json.dumps({"foo": "bar"}),
        "requestContext": {"http": {"method": "POST"}},
    }


@pytest.fixture
def invalid_event():
    """Invalid event payload for an HTTP invocation."""
    return {
        "body": json.dumps({"action": "invalid"}),
        "requestContext": {"http": {"method": "POST"}},
    }
