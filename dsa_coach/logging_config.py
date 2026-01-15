"""Logging configuration for DSA Coach.

Provides structured logging for:
- Tool executions (success/failure, duration)
- Hook executions
- Agent decisions
- Errors and exceptions

Logs are written to:
- Console (INFO level by default)
- File: logs/coach.log (DEBUG level, rotated daily)
- File: logs/errors.log (ERROR level only)
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Log directory
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log format
CONSOLE_FORMAT = "%(levelname)s | %(name)s | %(message)s"
FILE_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
)


def setup_logging(
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
) -> logging.Logger:
    """Configure logging for DSA Coach.

    Args:
        level: Minimum log level for console output
        log_to_file: Whether to write logs to files
        log_to_console: Whether to output to console

    Returns:
        Root logger for dsa_coach
    """
    # Create logger
    logger = logging.getLogger("dsa_coach")
    logger.setLevel(logging.DEBUG)  # Capture all, filter at handler level

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(logging.Formatter(CONSOLE_FORMAT))
        logger.addHandler(console_handler)

    # File handlers
    if log_to_file:
        # Main log file (rotated, 5MB max, keep 5 backups)
        main_handler = RotatingFileHandler(
            LOG_DIR / "coach.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        main_handler.setLevel(logging.DEBUG)
        main_handler.setFormatter(logging.Formatter(FILE_FORMAT))
        logger.addHandler(main_handler)

        # Error-only log file
        error_handler = RotatingFileHandler(
            LOG_DIR / "errors.log",
            maxBytes=2 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(FILE_FORMAT))
        logger.addHandler(error_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module.

    Args:
        name: Module name (e.g., "tools.consolidated", "agent.sdk_agent")

    Returns:
        Logger instance
    """
    return logging.getLogger(f"dsa_coach.{name}")


# Tool execution logging helpers
class ToolLogger:
    """Helper for logging tool executions with timing and context."""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.logger = get_logger(f"tools.{tool_name}")
        self.start_time: datetime | None = None

    def start(self, **params: object) -> None:
        """Log tool execution start."""
        self.start_time = datetime.now()
        # Filter out db parameter for cleaner logs
        clean_params = {k: v for k, v in params.items() if k != "db"}
        self.logger.debug(f"START | params={clean_params}")

    def success(self, result_summary: str = "") -> None:
        """Log successful tool execution."""
        duration = self._get_duration()
        self.logger.info(f"OK | {duration}ms | {result_summary}")

    def error(self, error_msg: str, exc: Exception | None = None) -> None:
        """Log tool execution error."""
        duration = self._get_duration()
        self.logger.error(f"FAIL | {duration}ms | {error_msg}", exc_info=exc)

    def hook_executed(self, hook_name: str, result: str = "") -> None:
        """Log hook execution within a tool."""
        self.logger.debug(f"HOOK | {hook_name} | {result}")

    def _get_duration(self) -> int:
        """Get execution duration in milliseconds."""
        if self.start_time:
            return int((datetime.now() - self.start_time).total_seconds() * 1000)
        return 0


# Initialize logging on module import
_root_logger = setup_logging(log_to_console=False)  # File only by default
