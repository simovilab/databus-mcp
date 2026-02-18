
from utils.databus_client import DatabusClient, get_client
from unidecode import unidecode

# Helpers
def filter_by_field(items: list[dict], field: str, value: str) -> list[dict]:
    """ Filter a list of dictionaries by a specific field and value. """
    return [item for item in items if item.get(field) == value]

def format_timestamp(ts: int | None) -> str:
    """ Convert a UNIX timestamp to a human-readable string. """
    if ts is None:
        return "N/A"
    from datetime import datetime
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def normalize_text(text: str) -> str:
    """ Normalize text by removing accents and converting to lowercase. """
    return unidecode(text.strip().lower())