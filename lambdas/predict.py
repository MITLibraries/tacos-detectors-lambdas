import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from http import HTTPStatus
from pickle import load

import pandas as pd
from jsonschema import ValidationError, validate
from sklearn.exceptions import NotFittedError
from sklearn.utils.validation import check_is_fitted

from lambdas.config import Config, configure_sentry

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

CONFIG = Config()


@dataclass
class InputPayload:
    action: str
    challenge_secret: str
    features: dict | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


class RequestHandler(ABC):
    @abstractmethod
    def handle(self, payload: InputPayload) -> dict:
        """Process the request and return a response."""
        ...


class PingHandler(RequestHandler):
    """Handle ping requests."""

    def handle(self, _payload: InputPayload) -> dict:
        return {"response": "pong"}


class PredictHandler(RequestHandler):
    """Handle prediction requests."""

    def load_model(self) -> None:
        """Load the machine learning model, and confirm it is fitted.

        Please note that this method does not have a return value. It populates
        the `self.model` attribute with the loaded model.
        """
        path = "lambdas/models/neural.pkl"
        with open(path, "rb") as f:
            self.model = load(f)  # noqa: S301

        try:
            check_is_fitted(self.model)
        except NotFittedError as exc:
            message = f"Model not fitted: {exc}"
            logger.exception(message)
            raise RuntimeError(message) from exc

    def handle(self, payload: InputPayload) -> dict:
        """Validate received payload, load model, and generate prediction."""
        with open("lambdas/schemas/features_schema.json") as f:
            schema = json.load(f)
        validate(instance=payload.to_dict(), schema=schema)

        self.load_model()

        data = pd.DataFrame(payload.features, index=[0])
        prediction = self.model.predict(data)

        return {"response": f"{prediction[0]}"}


class LambdaProcessor:
    def __init__(self) -> None:
        self.config = CONFIG

    def process_event(self, event: dict, _context: dict) -> dict:
        self.config.check_required_env_vars()
        configure_sentry()

        logger.debug(json.dumps(event))

        # Need to handle config

        try:
            payload = self._parse_payload(event)
        except (ValueError, ValidationError) as exc:
            logger.error(exc)  # noqa: TRY400
            return self._generate_http_error_response(
                str(exc), http_status_code=HTTPStatus.BAD_REQUEST
            )

        try:
            self._validate_secret(payload.challenge_secret)
        except RuntimeError as exc:
            logger.error(exc)  # noqa: TRY400
            return self._generate_http_error_response(
                str(exc), http_status_code=HTTPStatus.UNAUTHORIZED
            )

        try:
            handler = self.get_handler(payload.action)
            result = handler.handle(payload)
            return self._generate_http_success_response(result)
        except (ValueError, ValidationError) as exc:
            return self._generate_http_error_response(
                str(exc),
                http_status_code=HTTPStatus.BAD_REQUEST,
            )
        except Exception as exc:
            logger.exception("Unhandled exception")
            return self._generate_http_error_response(
                str(exc),
                http_status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def _parse_payload(self, event: dict) -> InputPayload:
        """Parse input payload, raising an exception if invalid."""
        body = json.loads(event["body"]) if "requestContext" in event else event

        try:
            input_payload = InputPayload(**body)
        except Exception as exc:
            message = f"Invalid input payload: {exc}"
            logger.error(message)  # noqa: TRY400
            raise ValueError(message) from exc

        return input_payload

    def _validate_secret(self, challenge_secret: str | None) -> None:
        """Check that secret passed with lambda invocation matches secret env var."""
        if (
            not challenge_secret
            or challenge_secret.strip() != self.config.CHALLENGE_SECRET
        ):
            message = "Challenge secret missing or mismatch"
            raise RuntimeError(message)

    def get_handler(self, action: str) -> RequestHandler:
        match action:
            case "ping":
                return PingHandler()
            case "predict":
                return PredictHandler()
            case _:
                message = f"Action not recognized: `{action}`"
                raise ValueError(message)

    @staticmethod
    def _generate_http_error_response(
        error: str,
        error_details: dict | None = None,
        http_status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
    ) -> dict:
        """Produce an error HTTP response object.

        See more: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html
        """
        return {
            "statusCode": http_status_code,
            "headers": {"Content-Type": "application/json"},
            "isBase64Encoded": False,
            "body": json.dumps(
                {
                    "error": error,
                    "error_details": error_details,
                }
            ),
        }

    @staticmethod
    def _generate_http_success_response(response: dict) -> dict:
        """Produce a success HTTP response object.

        See more: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html
        """
        return {
            "statusCode": HTTPStatus.OK,
            "statusDescription": "200 OK",
            "headers": {"Content-Type": "application/json"},
            "isBase64Encoded": False,
            "body": json.dumps(response),
        }


def lambda_handler(event: dict, context: dict) -> dict:
    """AWS lambda entrypoint."""
    return LambdaProcessor().process_event(event, context)
