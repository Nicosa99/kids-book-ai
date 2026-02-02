import logging
import sys

def setup_logging(name: str = "KidsBookGen") -> logging.Logger:
    """
    Konfiguriert einen robusten Logger, der Zeitstempel und Log-Level auf stdout ausgibt.
    Verhindert doppelte Logs durch Check auf vorhandene Handler.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Nur Handler hinzufügen, wenn noch keine existieren (verhindert Spam bei Reloads/Imports)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        # Format: 2023-10-27 10:00:00 - [INFO] - utils - Nachricht
        formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(module)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
