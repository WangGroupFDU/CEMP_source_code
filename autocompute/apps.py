import logging

from django.apps import AppConfig
from django.db.backends.signals import connection_created


logger = logging.getLogger("django")


def _configure_sqlite_runtime_pragmas(sender, connection, **kwargs):

    if getattr(connection, "vendor", "") != "sqlite":
        return

    try:
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA busy_timeout = 30000;")
            cursor.execute("PRAGMA journal_mode = WAL;")
    except Exception:
        logger.warning(
            "Failed to apply SQLite runtime pragmas for connection alias=%s.",
            getattr(connection, "alias", ""),
            exc_info=True,
        )


class AutocomputeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'autocompute'

    def ready(self):

        connection_created.connect(
            _configure_sqlite_runtime_pragmas,
            dispatch_uid="autocompute.sqlite_runtime_pragmas",
        )
