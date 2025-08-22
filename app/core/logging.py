"""
Logging configuration for Memorial Website.
Provides structured logging with proper formatting and handlers.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

import structlog
from structlog.typing import FilteringBoundLogger


def setup_logging(
    log_level: str = "INFO", 
    log_format: Optional[str] = None,
    log_file: Optional[str] = None
) -> None:
    """
    Setup application logging with structured logging support.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom log format string
        log_file: Optional log file path
    """
    # Configure log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Default log format
    if not log_format:
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = ColoredFormatter(log_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Setup file handler if specified
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Configure third-party loggers
    configure_third_party_loggers(level)
    
    # Setup structured logging
    setup_structured_logging()
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured. Level: {log_level}, File: {log_file or 'Console only'}")


def configure_third_party_loggers(level: int) -> None:
    """Configure logging levels for third-party libraries."""
    
    # Database logging
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if level <= logging.DEBUG else logging.WARNING
    )
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)
    
    # FastAPI/Uvicorn logging
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.error").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(
        logging.INFO if level <= logging.INFO else logging.WARNING
    )
    logging.getLogger("fastapi").setLevel(level)
    
    # HTTP client logging
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # Rate limiting
    logging.getLogger("slowapi").setLevel(logging.WARNING)
    
    # Email logging
    logging.getLogger("fastapi_mail").setLevel(logging.INFO)


def setup_structured_logging() -> None:
    """Setup structlog for structured logging."""
    
    def add_logger_name(logger, method_name, event_dict):
        """Add logger name to event dict."""
        event_dict["logger"] = logger.name
        return event_dict
    
    def add_log_level(logger, method_name, event_dict):
        """Add log level to event dict."""
        event_dict["level"] = method_name.upper()
        return event_dict
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            add_logger_name,
            add_log_level,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.dev.ConsoleRenderer() if sys.stderr.isatty() else structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for console logging."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green  
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Add color to level name
        if record.levelname in self.COLORS and sys.stderr.isatty():
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname}"
                f"{self.RESET}"
            )
        
        return super().format(record)


def get_logger(name: str) -> FilteringBoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        FilteringBoundLogger: Structured logger instance
    """
    return structlog.get_logger(name)


class LoggingContext:
    """Context manager for adding context to all log messages."""
    
    def __init__(self, **context):
        self.context = context
    
    def __enter__(self):
        structlog.contextvars.bind_contextvars(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for key in self.context.keys():
            structlog.contextvars.unbind_contextvars(key)


def log_request_context(request_id: str, user_id: Optional[str] = None):
    """
    Create logging context for HTTP requests.
    
    Args:
        request_id: Unique request identifier
        user_id: Optional user identifier
        
    Returns:
        LoggingContext: Context manager for request logging
    """
    context = {"request_id": request_id}
    if user_id:
        context["user_id"] = user_id
    
    return LoggingContext(**context)


def log_database_context(operation: str, table: Optional[str] = None):
    """
    Create logging context for database operations.
    
    Args:
        operation: Database operation (SELECT, INSERT, UPDATE, DELETE)
        table: Optional table name
        
    Returns:
        LoggingContext: Context manager for database logging
    """
    context = {"db_operation": operation}
    if table:
        context["db_table"] = table
    
    return LoggingContext(**context)


# Performance logging utilities

class PerformanceTimer:
    """Context manager for measuring and logging execution time."""
    
    def __init__(self, logger: logging.Logger, operation: str, threshold_ms: int = 1000):
        """
        Initialize performance timer.
        
        Args:
            logger: Logger instance
            operation: Operation being measured
            threshold_ms: Log warning if execution exceeds this threshold
        """
        self.logger = logger
        self.operation = operation
        self.threshold_ms = threshold_ms
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        if self.start_time is None:
            return
        
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        
        if duration_ms > self.threshold_ms:
            self.logger.warning(
                f"Slow operation: {self.operation} took {duration_ms:.2f}ms "
                f"(threshold: {self.threshold_ms}ms)"
            )
        else:
            self.logger.debug(
                f"Operation completed: {self.operation} took {duration_ms:.2f}ms"
            )


def time_operation(operation: str, threshold_ms: int = 1000):
    """
    Decorator for timing function execution.
    
    Args:
        operation: Operation description
        threshold_ms: Log warning if execution exceeds this threshold
        
    Returns:
        Decorator function
    """
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            with PerformanceTimer(logger, operation, threshold_ms):
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            with PerformanceTimer(logger, operation, threshold_ms):
                return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Security logging utilities

def log_security_event(
    event_type: str,
    details: dict,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    severity: str = "WARNING"
):
    """
    Log security-related events.
    
    Args:
        event_type: Type of security event (login_failed, suspicious_activity, etc.)
        details: Additional event details
        user_id: Optional user identifier
        ip_address: Optional client IP address
        severity: Log severity level
    """
    logger = logging.getLogger("security")
    
    log_data = {
        "event_type": event_type,
        "details": details,
        "timestamp": structlog.processors.TimeStamper.default_time_stamp(),
    }
    
    if user_id:
        log_data["user_id"] = user_id
    if ip_address:
        log_data["ip_address"] = ip_address
    
    log_level = getattr(logging, severity.upper(), logging.WARNING)
    logger.log(log_level, f"Security event: {event_type}", extra=log_data)