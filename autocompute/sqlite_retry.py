
from __future__ import annotations

import logging
import time
from typing import Callable, Optional, Sequence, TypeVar

from django.db import OperationalError
from django.utils import timezone

from autocompute.models import ComputeTask


logger = logging.getLogger("django")

SQLITE_LOCK_ERROR_MARKER = "database is locked"
DEFAULT_SQLITE_RETRY_DELAYS_SECONDS: Sequence[int] = (1, 2, 3)

T = TypeVar("T")


def run_with_sqlite_retry(
    operation: Callable[[], T],
    *,
    retry_delays: Sequence[int] = DEFAULT_SQLITE_RETRY_DELAYS_SECONDS,
    logger_instance: Optional[logging.Logger] = None,
    operation_name: str = "sqlite_write",
) -> T:

    current_logger = logger_instance or logger
    delays = list(retry_delays)
    for attempt, backoff_seconds in enumerate(delays, start=1):
        try:
            return operation()
        except OperationalError as exc:
            error_text = str(exc).lower()
            if SQLITE_LOCK_ERROR_MARKER not in error_text:
                raise
            current_logger.warning(
                "SQLite lock detected during %s: attempt=%s backoff_seconds=%s error=%s",
                operation_name,
                attempt,
                backoff_seconds,
                str(exc),
            )
            time.sleep(backoff_seconds)
    return operation()


def save_task_with_sqlite_retry(
    task: ComputeTask,
    *,
    update_fields: Optional[Sequence[str]] = None,
    operation_name: str = "save_task",
) -> None:

    normalized_fields = list(update_fields) if update_fields else None
    run_with_sqlite_retry(
        lambda: task.save(update_fields=normalized_fields),
        operation_name=operation_name,
    )


def touch_task_heartbeat(
    task: ComputeTask,
    *,
    save: bool = True,
) -> None:

    task.last_heartbeat_at = timezone.now()
    if save:
        save_task_with_sqlite_retry(
            task,
            update_fields=["last_heartbeat_at"],
            operation_name="touch_task_heartbeat",
        )
