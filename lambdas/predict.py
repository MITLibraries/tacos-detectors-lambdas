import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from http import HTTPStatus

from lambdas.config import Config, configure_sentry

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

CONFIG = Config()


@dataclass
class InputPayload:
    action: str


class RequestHandler(ABC):
    @abstractmethod
    def handle(self, payload: InputPayload) -> dict:
        """Process the request and return a response."""
        ...


class PingHandler(RequestHandler):
    """Handle ping requests."""

    def handle(self, _payload: InputPayload) -> dict:
        return {"response": "pong"}


class LambdaProcessor:
    def __init__(self) -> None:
        self.config = CONFIG

    def process_event(self, event: dict, _context: dict) -> dict:
        self.config.check_required_env_vars()
        configure_sentry()

        if not os.getenv("WORKSPACE"):
            unset_workspace_error_message = "Required env variable WORKSPACE is not set"
            raise RuntimeError(unset_workspace_error_message)

        logger.debug(json.dumps(event))

        # Need to handle config

        try:
            payload = self._parse_payload(event)
        except ValueError as exc:
            logger.error(exc)  # noqa: TRY400
            return self._generate_http_error_response(
                str(exc), http_status_code=HTTPStatus.BAD_REQUEST
            )

        # Need to validate secret

        try:
            handler = self.get_handler(payload.action)
            result = handler.handle(payload)
            return self._generate_http_success_response(result)
        except ValueError as exc:
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

    def get_handler(self, action: str) -> RequestHandler:
        if action == "ping":
            return PingHandler()
        raise ValueError(f"Action not recognized: `{action}`")  # noqa: TRY003 EM102

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
