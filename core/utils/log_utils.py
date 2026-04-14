"""
Logging helpers for structured service logs.

This module centralizes repetitive log message formatting so services can
produce consistent message shapes with a small helper interface.
"""

import logging

def log_info(logger: logging.Logger, service: str, message: str, **kwargs) -> None:
    if kwargs:
        extra = " ".join(f"{k}='{v}'" for k, v in kwargs.items())
    logger.info(f"service='{service}' message='{message}' {extra}")


def log_error(
    logger: logging.Logger,
    service: str,
    message: str,
    error: object,
    **kwargs,
) -> None:
    if kwargs:
        extra = " ".join(f"{k}='{v}'" for k, v in kwargs.items())
    logger.error(
        f"service='{service}' message='{message}' "
        f"{extra} error='{str(error)}' exception='{type(error).__name__}'"
    )
