import logging
from pathlib import Path
from typing import Optional

from ragtrace_lite.config.config_loader import get_config

def setup_logging(debug: bool = False):
    """Setup logging based on configuration."""
    config = get_config()
    log_config = config.logging

    level = logging.DEBUG if debug else getattr(logging, log_config.level.upper(), logging.INFO)

    # Remove all existing handlers to prevent duplicate logs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    handlers = []

    if log_config.console:
        console_handler = logging.StreamHandler()
        handlers.append(console_handler)

    if log_config.file:
        log_file_path = Path(log_config.file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

    # Set log level for specific noisy loggers if needed
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info("Logging configured.")
