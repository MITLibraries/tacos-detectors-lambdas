import json
from http import HTTPStatus
from unittest.mock import patch

import pytest
from sklearn.exceptions import NotFittedError

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
def test_lambda_handler_predict_citation(valid_predict_event_citation):
    """Test lambda_handler with a valid HTTP event for a citation."""
    response = predict.lambda_handler(valid_predict_event_citation, {})
    assert response["statusCode"] == HTTPStatus.OK
    body = json.loads(response["body"])
    assert body["response"] == "True"


def test_lambda_handler_predict_noncitation(valid_predict_event_noncitation):
    """Test lambda_handler with a valid HTTP event for a non-citation."""
    response = predict.lambda_handler(valid_predict_event_noncitation, {})
    assert response["statusCode"] == HTTPStatus.OK
    body = json.loads(response["body"])
    assert body["response"] == "False"


def test_lambda_handler_predict_invalid_missing(invalid_predict_event_missing):
    """Test lambda_handler with less than a full set of prediction features."""
    response = predict.lambda_handler(invalid_predict_event_missing, {})
    assert response["statusCode"] == HTTPStatus.BAD_REQUEST
    body = json.loads(response["body"])
    assert body["error"][:28] == "'apa' is a required property"


def test_lambda_handler_predict_invalid_extra(invalid_predict_event_extra):
    """Test lambda_handler with extraneous prediction features."""
    response = predict.lambda_handler(invalid_predict_event_extra, {})
    assert response["statusCode"] == HTTPStatus.BAD_REQUEST
    body = json.loads(response["body"])
    assert body["error"][:37] == "Additional properties are not allowed"


def test_lambda_handler_predict_unfitted_model(valid_predict_event_citation):
    """Test lambda_handler with an unfitted model."""
    with patch(
        "lambdas.predict.check_is_fitted", side_effect=NotFittedError("not fitted")
    ):
        response = predict.lambda_handler(valid_predict_event_citation, {})
        assert response["statusCode"] == HTTPStatus.INTERNAL_SERVER_ERROR
        body = json.loads(response["body"])
        assert body["error"] == "Model not fitted: not fitted"


def test_predict_handler_loads_model():
    """Test that the model is loaded correctly."""
    predictor = predict.PredictHandler()
    assert not hasattr(predictor, "model")
    predictor.load_model()
    assert hasattr(predictor, "model")
    assert callable(predictor.model.predict)


def test_predict_handler_errors_with_unfitted_model():
    """Test that an error is raised if the model is not fitted."""
    with patch(
        "lambdas.predict.check_is_fitted", side_effect=NotFittedError("not fitted")
    ):
        predictor = predict.PredictHandler()
        # Calling the load_model method should now raise a predictable error
        with pytest.raises(RuntimeError, match="Model not fitted: not fitted"):
            predictor.load_model()
