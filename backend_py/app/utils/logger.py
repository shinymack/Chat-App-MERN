import sys
from loguru import logger

# Remove default handler
logger.remove()

# Add standard stdout handler with clean, formatted output
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True,
    backtrace=True,
    diagnose=True,
)

# Optional: Add file logging
# logger.add("logs/app.log", rotation="10 MB", retention="10 days", level="DEBUG")

# Expose the logger object
log = logger
