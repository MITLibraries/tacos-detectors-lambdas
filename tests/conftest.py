import json

import pytest


@pytest.fixture(autouse=True)
def _test_env(monkeypatch):
    monkeypatch.setenv("CHALLENGE_SECRET", "secret_phrase")
    monkeypatch.setenv("WORKSPACE", "test")


@pytest.fixture
def valid_event():
    """Valid event payload for an HTTP invocation."""
    return {
        "body": json.dumps({"action": "ping", "challenge_secret": "secret_phrase"}),
        "requestContext": {"http": {"method": "POST"}},
    }


@pytest.fixture
def wrong_secret_event():
    """Event payload with incorrect challenge secret for an HTTP invocation."""
    return {
        "body": json.dumps({"action": "ping", "challenge_secret": "wrong_phrase"}),
        "requestContext": {"http": {"method": "POST"}},
    }


@pytest.fixture
def no_secret_event():
    """Event payload lacking the challenge secret for an HTTP invocation."""
    return {
        "body": json.dumps({"action": "ping"}),
        "requestContext": {"http": {"method": "POST"}},
    }


@pytest.fixture
def nonsense_event():
    """Nonsense event payload for an HTTP invocation."""
    return {
        "body": json.dumps({"foo": "bar", "challenge_secret": "secret_phrase"}),
        "requestContext": {"http": {"method": "POST"}},
    }


@pytest.fixture
def invalid_event():
    """Invalid event payload for an HTTP invocation."""
    return {
        "body": json.dumps({"action": "invalid", "challenge_secret": "secret_phrase"}),
        "requestContext": {"http": {"method": "POST"}},
    }
