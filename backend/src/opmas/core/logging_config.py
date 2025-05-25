# Sets up logging configuration for OPMAS components.

import json
import logging
import logging.config
import os
from typing import Any, Dict

# Import config loading function
from .config import get_config


# --- JSON Formatter --- (Requires python-json-logger, add to requirements.txt if used)
# Using a simple custom one for now to avoid adding dependency yet.
class SimpleJsonFormatter(logging.Formatter):
    """A simple formatter to output log records as JSON."""

    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        # Add exception info if available
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        # Add stack info if available
        if record.stack_info:
            log_record["stack_info"] = self.formatStack(record.stack_info)
        # Add any extra fields passed to the logger
        # Standard ones often added by libraries
        skip_list = (
            "args",
            "asctime",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "thread",
            "threadName",
        )
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in skip_list and not key.startswith("_"):
                    log_record[key] = value

        return json.dumps(log_record)


# --- Logging Setup Function ---

_logging_configured = False


def setup_logging():
    """Configures logging based on settings from the config module."""
    global _logging_configured
    if _logging_configured:
        return

    config = get_config()  # Load the main configuration
    log_config = config.get("logging", {})

    log_level_str = log_config.get("level", "INFO").upper()
    # Use the new keys from config.py
    log_format_type = log_config.get("format_type", "standard").lower()
    default_fmt_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_format_string = log_config.get("format_string", default_fmt_string)
    log_datefmt = log_config.get("datefmt", "%Y-%m-%dT%H:%M:%S%z")  # ISO 8601 preferred

    log_level = getattr(logging, log_level_str, logging.INFO)

    # Define basic config (can be extended for file logging, etc.)
    logging_dict: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                # Use the actual format string loaded from config
                "format": log_format_string,
                "datefmt": log_datefmt,
            },
            "json": {
                # If using python-json-logger:
                # '()' : 'pythonjsonlogger.jsonlogger.JsonFormatter',
                # 'format': '%(asctime)s %(name)s %(levelname)s %(message)s', # Example format
                # 'datefmt': log_datefmt
                # Using Simple custom one:
                "()": __name__ + ".SimpleJsonFormatter",  # Reference our custom class
                "datefmt": log_datefmt,
            },
        },
        "handlers": {
            "console": {
                "level": log_level,
                "class": "logging.StreamHandler",
                "formatter": "standard",  # Default formatter name
            }
        },
        "root": {
            "handlers": ["console"],
            "level": log_level,
        },
        # Example: Quieter logging for noisy libraries
        "loggers": {
            "nats": {
                "handlers": ["console"],
                "level": "WARNING",  # NATS client can be verbose
                "propagate": False,
            },
            "paramiko": {
                "handlers": ["console"],
                "level": "WARNING",  # Paramiko can also be verbose
                "propagate": False,
            }
            # Add other library-specific levels if needed
        },
    }

    # Set the handler's formatter name based on the configured format type
    if log_format_type == "json":
        logging_dict["handlers"]["console"]["formatter"] = "json"
    else:
        logging_dict["handlers"]["console"]["formatter"] = "standard"

    # Update library log levels based on config (example)
    # You might want separate config keys for these if needed
    library_log_level = log_config.get("library_level", "WARNING").upper()
    logging_dict["loggers"]["nats"]["level"] = library_log_level
    logging_dict["loggers"]["paramiko"]["level"] = library_log_level

    try:
        logging.config.dictConfig(logging_dict)
        _logging_configured = True
        # Log the actual formatter *name* being used by the handler
        actual_formatter = logging_dict["handlers"]["console"]["formatter"]
        logging.info(f"Logging configured. Level: {log_level_str}, Format: {actual_formatter}")
    except Exception as e:
        # Fallback to basic config if dictConfig fails
        # Use the actual format string for fallback
        logging.basicConfig(level=log_level, format=log_format_string, datefmt=log_datefmt)
        logging.error(
            f"Failed to configure logging using dictConfig: {e}. Falling back to basicConfig.",
            exc_info=True,
        )


# Example Usage (for illustration)
if __name__ == "__main__":
    # Test standard logging
    print("--- Testing Standard Logging ---")
    # Ensure config defaults are loaded if no file exists
    # from config import _create_default_core_config, get_config
    # _create_default_core_config(get_config())
    setup_logging()
    logger = logging.getLogger("LoggingTest")
    logger.debug("This is a debug message (should not appear with INFO level).")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("This is an exception message.")

    # Test JSON logging (requires modifying config or setting env var)
    print("\n--- Testing JSON Logging (set OPMAS_LOGGING_FORMAT=json) ---")
    # To test this, run: OPMAS_LOGGING_FORMAT=json python src/opmas/logging_config.py
    # Or modify/create config/opmas_config.yaml:
    # logging:
    #   format: json
    #   level: DEBUG
    #
    # Need to clear config cache and logging flag to reconfigure
    # import config
    # config._config_cache = None
    # _logging_configured = False
    # print("(Re)configuring logging...")
    # setup_logging()
    # logger = logging.getLogger("LoggingTestJson")
    # logger.debug("This is a JSON debug message.")
    # logger.info("This is a JSON info message.", extra={'custom_field': 'value'})
    # logger.warning("This is a JSON warning.")

    print("\nLogging setup demo finished.")
