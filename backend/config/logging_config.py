"""
Logging configuration for StratoviqueAI
Streamlined logging with console + file output + performance tracking
"""

import logging
import logging.handlers
import os
from time import time

# Create logs directory if it doesn't exist
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Log file paths
APP_LOG_FILE = os.path.join(LOG_DIR, "app.log")
TOKEN_LOG_FILE = os.path.join(LOG_DIR, "token_usage.log")
AGENT_LOG_FILE = os.path.join(LOG_DIR, "agents.log")
PERF_LOG_FILE = os.path.join(LOG_DIR, "performance.log")

# Formatters - streamlined
DETAILED_FORMATTER = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

SIMPLE_FORMATTER = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

PERF_FORMATTER = logging.Formatter(
    '%(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def _add_file_handler(logger: logging.Logger, file_path: str, formatter: logging.Formatter, level: int = logging.DEBUG):
    """Helper to add file handler to logger"""
    try:
        handler = logging.handlers.RotatingFileHandler(
            file_path, maxBytes=10*1024*1024, backupCount=5
        )
        handler.setLevel(level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    except Exception as e:
        print(f"⚠️  Failed to set up file handler for {file_path}: {e}")


def _setup_logger(name: str, log_file: str = None, include_console: bool = True, level: int = logging.DEBUG) -> logging.Logger:
    """
    Streamlined logger setup
    
    Args:
        name: Logger name
        log_file: Optional file path
        include_console: Add console handler
        level: Logger level
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if logger.hasHandlers():
        return logger
    
    # Console output
    if include_console:
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(SIMPLE_FORMATTER)
        logger.addHandler(console)
    
    # File output
    if log_file:
        _add_file_handler(logger, log_file, DETAILED_FORMATTER, logging.DEBUG)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with the given name"""
    return logging.getLogger(name)


# ── Initialize All Loggers ────────────────────────────────────────────────────

# Main app logger (all general app events)
app_logger = _setup_logger("stratoviqueai", APP_LOG_FILE)

# Agent execution logger
agents_logger = _setup_logger("stratoviqueai.agents", AGENT_LOG_FILE)

# Token usage logger (for cost tracking)
token_logger = _setup_logger("stratoviqueai.tokens", TOKEN_LOG_FILE)

# Performance/timing logger
perf_logger = _setup_logger("stratoviqueai.performance", PERF_LOG_FILE)

# LangGraph workflow logger
langgraph_logger = _setup_logger("stratoviqueai.langgraph", None)

# Search API logger
search_logger = _setup_logger("stratoviqueai.search", None)


# ── Performance Tracking ──────────────────────────────────────────────────────

class TimingContext:
    """Context manager for tracking operation timing"""
    
    def __init__(self, operation_name: str, log_to_perf: bool = True):
        self.operation_name = operation_name
        self.log_to_perf = log_to_perf
        self.start_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = (time() - self.start_time) * 1000  # milliseconds
        
        if self.log_to_perf:
            status = "✓" if exc_type is None else "✗"
            perf_logger.info(f"{status} {self.operation_name} | {self.duration:.2f}ms")
        
        return False


def track_time(operation_name: str):
    """Decorator to track function execution time"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with TimingContext(operation_name) as timer:
                return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator
