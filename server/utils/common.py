from curses import wrapper
from utils.databus_client import DatabusClient, get_client
from unidecode import unidecode


# Helper functions
def format_timestamp(ts: int | None) -> str:
    """Convert a UNIX timestamp to a human-readable string.

    arguments:
        - ts: The UNIX timestamp to format. If None, "N/A" is returned.

    returns:
        - A human-readable string representation of the timestamp.
    """
    if ts is None:
        return "N/A"
    from datetime import datetime

    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def normalize_text(text: str) -> str:
    """Normalize text by removing accents and converting to lowercase.

    arguments:
        - text: The input text to normalize.

    returns:
        - The normalized text.
    """
    return unidecode(text.strip().lower())
