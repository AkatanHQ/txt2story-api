import logging
from datetime import datetime

def setup_logger():
    """
    Sets up a logger with a consistent format and file handler for production use.
    """
    logger = logging.getLogger("ComicAppLogger")
    logger.setLevel(logging.DEBUG)  # Set log level to DEBUG for detailed logs

    # Create a console handler for stdout
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Log format
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()
