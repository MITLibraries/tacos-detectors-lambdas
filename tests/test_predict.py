import json
from http import HTTPStatus
from unittest.mock import patch

import pytest

from lambdas import predict


def test_lambda_handler_missing_workspace_env_raises_error(monkeypatch):
    monkeypatch.delenv("WORKSPACE", raising=False)
    with pytest.raises(
        OSError,
        match="Missing required environment variables: WORKSPACE",
    ):
        predict.lambda_handler({}, {})


# Validation problems of various types
def test_lambda_handler_with_wrong_secret(wrong_secret_event):
    """Test lambda_handler with an incorrect challenge secret."""
    response = predict.lambda_handler(wrong_secret_event, {})
    assert response["statusCode"] == HTTPStatus.UNAUTHORIZED
    body = json.loads(response["body"])
    assert body["error"] == "Challenge secret missing or mismatch"


def test_lambda_handler_with_no_secret(no_secret_event):
    """Test lambda_handler without including a challenge secret."""
    response = predict.lambda_handler(no_secret_event, {})
    assert response["statusCode"] == HTTPStatus.BAD_REQUEST
    body = json.loads(response["body"])
    assert body["error"][:23] == "Invalid input payload: "


def test_lambda_handler_ping_invalid(invalid_action_event):
    """Test lambda_handler with an invalid action."""
    response = predict.lambda_handler(invalid_action_event, {})
    assert response["statusCode"] == HTTPStatus.BAD_REQUEST
    body = json.loads(response["body"])
    assert body["error"] == "Action not recognized: `invalid`"


def test_lambda_handler_ping_nonsense(nonsense_event):
    """Test lambda_handler with nonsense parameters."""
    response = predict.lambda_handler(nonsense_event, {})
    assert response["statusCode"] == HTTPStatus.BAD_REQUEST
    body = json.loads(response["body"])
    assert body["error"][:23] == "Invalid input payload: "


def test_lambda_handler_unhandled_exception(valid_ping_event):
    """Test lambda_handler with an unhandled exception."""
    with patch("lambdas.predict.PingHandler.handle", side_effect=Exception("Test error")):
        response = predict.lambda_handler(valid_ping_event, {})
        assert response["statusCode"] == HTTPStatus.INTERNAL_SERVER_ERROR
        body = json.loads(response["body"])
        assert body["error"] == "Test error"


# Ping action
def test_lambda_handler_ping_valid(valid_ping_event):
    """Test lambda_handler with a valid HTTP event."""
    response = predict.lambda_handler(valid_ping_event, {})
    assert response["statusCode"] == HTTPStatus.OK
    body = json.loads(response["body"])
    assert body["response"] == "pong"


# Prediction action
def test_lambda_handler_predict_valid(valid_predict_event):
    """Test lambda_handler with a valid HTTP event."""
    response = predict.lambda_handler(valid_predict_event, {})
    assert response["statusCode"] == HTTPStatus.OK
    body = json.loads(response["body"])
    assert body["response"] == "true"


def test_lambda_handler_predict_invalid_missing(invalid_predict_event_missing):
    """Test lambda_handler with less than a full set of prediction features."""
    response = predict.lambda_handler(invalid_predict_event_missing, {})
    assert response["statusCode"] == HTTPStatus.BAD_REQUEST
    body = json.loads(response["body"])
    assert body["error"][:28] == "'apa' is a required property"


def test_lambda_handler_predict_invalid_extra(invalid_predict_event_extra):
    """Test lambda_handler with less than a full set of prediction features."""
    response = predict.lambda_handler(invalid_predict_event_extra, {})
    assert response["statusCode"] == HTTPStatus.BAD_REQUEST
    body = json.loads(response["body"])
    assert body["error"][:37] == "Additional properties are not allowed"
