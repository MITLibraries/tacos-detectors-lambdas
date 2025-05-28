import json

import pytest


@pytest.fixture(autouse=True)
def _test_env(monkeypatch):
    monkeypatch.setenv("CHALLENGE_SECRET", "secret_phrase")
    monkeypatch.setenv("WORKSPACE", "test")


@pytest.fixture
def valid_ping_event():
    """Valid event payload for an HTTP invocation."""
    return {
        "body": json.dumps({"action": "ping", "challenge_secret": "secret_phrase"}),
        "requestContext": {"http": {"method": "POST"}},
    }


@pytest.fixture
def valid_predict_event():
    """Valid event payload for an HTTP invocation."""
    return {
        "body": json.dumps(
            {
                "action": "predict",
                "challenge_secret": "secret_phrase",
                "features": {
                    "apa": 0,
                    "brackets": 0,
                    "colons": 0,
                    "commas": 0,
                    "lastnames": 0,
                    "no": 0,
                    "pages": 0,
                    "periods": 0,
                    "pp": 0,
                    "quotes": 0,
                    "semicolons": 0,
                    "vol": 0,
                    "words": 0,
                    "year": 0,
                },
            }
        ),
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
def invalid_action_event():
    """Invalid event payload for an HTTP invocation."""
    return {
        "body": json.dumps({"action": "invalid", "challenge_secret": "secret_phrase"}),
        "requestContext": {"http": {"method": "POST"}},
    }


@pytest.fixture
def invalid_predict_event_missing():
    """Invalid event payload (required apa parameter is missing)."""
    return {
        "body": json.dumps(
            {
                "action": "predict",
                "challenge_secret": "secret_phrase",
                "features": {
                    "brackets": 0,
                    "colons": 0,
                    "commas": 0,
                    "lastnames": 0,
                    "no": 0,
                    "pages": 0,
                    "periods": 0,
                    "pp": 0,
                    "quotes": 0,
                    "semicolons": 0,
                    "vol": 0,
                    "words": 0,
                    "year": 0,
                },
            }
        ),
        "requestContext": {"http": {"method": "POST"}},
    }


@pytest.fixture
def invalid_predict_event_extra():
    """Invalid event payload ("extra" parameter is not supported)."""
    return {
        "body": json.dumps(
            {
                "action": "predict",
                "challenge_secret": "secret_phrase",
                "features": {
                    "apa": 0,
                    "brackets": 0,
                    "colons": 0,
                    "commas": 0,
                    "extra": 0,
                    "lastnames": 0,
                    "no": 0,
                    "pages": 0,
                    "periods": 0,
                    "pp": 0,
                    "quotes": 0,
                    "semicolons": 0,
                    "vol": 0,
                    "words": 0,
                    "year": 0,
                },
            }
        ),
        "requestContext": {"http": {"method": "POST"}},
    }
