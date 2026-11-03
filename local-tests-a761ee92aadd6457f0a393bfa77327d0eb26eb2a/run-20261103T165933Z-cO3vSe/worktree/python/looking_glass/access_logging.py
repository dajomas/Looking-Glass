"""Suppress successful HTTP access records without hiding server diagnostics."""
import logging


class AccessStatusFilter(logging.Filter):
    def __init__(self, log_success=False):
        super().__init__()
        self.log_success = log_success

    def filter(self, record):
        if self.log_success or record.levelno >= logging.WARNING:
            return True
        # Uvicorn's HTTP access tuple: client, method, path, HTTP version, status.
        # Unknown formats are kept rather than risking silent diagnostic loss.
        if not isinstance(record.args, tuple) or len(record.args) != 5:
            return True
        try:
            status = int(record.args[4])
        except (TypeError, ValueError, OverflowError):
            return True
        return not 100 <= status < 400


def configure_access_logging(log_success=False):
    if not isinstance(log_success, bool):
        raise ValueError("server.access_log_success must be a YAML boolean")
    logger = logging.getLogger("uvicorn.access")
    for item in list(logger.filters):
        if isinstance(item, AccessStatusFilter):
            logger.removeFilter(item)
    logger.addFilter(AccessStatusFilter(log_success))
