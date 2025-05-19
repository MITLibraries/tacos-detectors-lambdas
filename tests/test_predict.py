import json
from http import HTTPStatus
from importlib import reload

import pytest

from lambdas import predict


def test_predict_configures_sentry_if_dsn_present(caplog, monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "https://1234567890@00000.ingest.sentry.io/123456")
    reload(predict)
    assert (
        "Sentry DSN found, exceptions will be sent to Sentry with env=test" in caplog.text
    )


def test_predict_doesnt_configure_sentry_if_dsn_not_present(caplog, monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    reload(predict)
    assert "No Sentry DSN found, exceptions will not be sent to Sentry" in caplog.text


def test_lambda_handler_missing_workspace_env_raises_error(monkeypatch):
    monkeypatch.delenv("WORKSPACE", raising=False)
    with pytest.raises(RuntimeError) as error:
        predict.lambda_handler({}, {})
    assert "Required env variable WORKSPACE is not set" in str(error)


def test_lambda_handler_ping_valid(valid_event):
    """Test lambda_handler with a valid HTTP event."""
    response = predict.lambda_handler(valid_event, {})
    assert response["statusCode"] == HTTPStatus.OK
    body = json.loads(response["body"])
    assert body["response"] == "pong"


def test_lambda_handler_ping_invalid(invalid_event):
    """Test lambda_handler with a invalid HTTP event."""
    response = predict.lambda_handler(invalid_event, {})
    assert response["statusCode"] == HTTPStatus.BAD_REQUEST
    body = json.loads(response["body"])
    assert body["error"] == "Action not recognized: `invalid`"


def test_lambda_handler_ping_nonsense(nonsense_event):
    """Test lambda_handler with a nonsense HTTP event."""
    response = predict.lambda_handler(nonsense_event, {})
    assert response["statusCode"] == HTTPStatus.BAD_REQUEST
    body = json.loads(response["body"])
    assert body["error"][:23] == "Invalid input payload: "
