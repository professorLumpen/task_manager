import functools
import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


def setup_logger():
    project_logger = logging.getLogger("task_manager_logger")
    project_logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)

    project_logger.addHandler(ch)

    return project_logger


logger = setup_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        logger.info("Request: %s %s", request.method, request.url)

        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error("Exception: %s %s - %s", request.method, request.url, exc, exc_info=True)
            raise

        process_time = (time.perf_counter() - start_time) * 1000
        logger.info(
            "Response: %s %s -> %s. Process time: %s ms",
            request.method,
            request.url,
            response.status_code,
            process_time,
        )

        return response


def logging_decorator(level=logging.INFO):
    def inner_decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger.log(level, "Call %s with args=%s, kwargs=%s", func.__name__, args, kwargs)

            try:
                result = await func(*args, **kwargs)
                logger.log(level, "Result %s: %s", func.__name__, result)
                return result
            except Exception as exc:
                logger.error("Exception %s: %s", func.__name__, exc, exc_info=True)
                raise

        return wrapper

    return inner_decorator
