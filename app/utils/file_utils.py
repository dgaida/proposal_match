import os
from datetime import datetime


def get_file_age_days(filepath: str) -> int:
    """Calculates the age of a file in days.

    Args:
        filepath (str): The path to the file.

    Returns:
        int: The age of the file in days. Returns 0 if the file does not exist.
    """
    if not os.path.exists(filepath):
        return 0

    mtime = os.path.getmtime(filepath)
    last_modified = datetime.fromtimestamp(mtime)
    now = datetime.now()
    delta = now - last_modified
    return delta.days
