from __future__ import annotations
import json, logging, os, sys
from datetime import datetime, timezone


class _JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {"ts": datetime.now(tz=timezone.utc).isoformat(), "level": record.levelname, "logger": record.name, "msg": record.getMessage()}
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


class _ColorFormatter(logging.Formatter):
    COLORS = {"DEBUG": "\033[37m", "INFO": "\033[36m", "WARNING": "\033[33m", "ERROR": "\033[31m", "CRITICAL": "\033[41m"}
    RESET = "\033[0m"
    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        ts = datetime.now(tz=timezone.utc).strftime("%H:%M:%S")
        line = f"{color}[{record.levelname[0]}]{self.RESET} {ts} {record.name.split('.')[-1]}: {record.getMessage()}"
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_JsonFormatter() if os.environ.get("LOG_FORMAT") == "json" else _ColorFormatter())
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO))
    logger.propagate = False
    return logger
