from loguru import logger
import sys


logger.add(
    "last.log",
    rotation="50 KB",
    compression="zip",
    level="INFO",
    backtrace=True,
    diagnose=True,
    catch=sys.stdout,
    format="{time} {level} {module} {message}",
)
