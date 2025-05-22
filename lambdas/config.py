import logging
import os
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Config:
    REQUIRED_ENV_VARS = (
        "CHALLENGE_SECRET",
        "WORKSPACE",
    )
    OPTIONAL_ENV_VARS = ("SENTRY_DSN",)

    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        """Provide dot notation access to configurations and env vars on this class."""
        if name in self.REQUIRED_ENV_VARS or name in self.OPTIONAL_ENV_VARS:
            return os.getenv(name)
        message = f"'{name}' not a valid configuration variable"
        raise AttributeError(message)

    def check_required_env_vars(self) -> None:
        """Method to raise exception if required env vars not set."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            message = f"Missing required environment variables: {', '.join(missing_vars)}"
            raise OSError(message)

    @property
    def sentry_dsn(self) -> str | None:
        dsn = os.getenv("SENTRY_DSN")
        if dsn and dsn.strip().lower() != "none":
            return dsn
        return None


def configure_sentry() -> None:
    CONFIG = Config()  # noqa: N806
    env = CONFIG.WORKSPACE
    if CONFIG.sentry_dsn:
        sentry_sdk.init(
            dsn=CONFIG.sentry_dsn,
            environment=env,
            integrations=[
                AwsLambdaIntegration(),
            ],
            traces_sample_rate=1.0,
        )
        logger.info(
            "Sentry DSN found, exceptions will be sent to Sentry with env=%s", env
        )
    else:
        logger.info("No Sentry DSN found, exceptions will not be sent to Sentry")
