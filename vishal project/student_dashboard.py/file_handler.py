"""
file_handler.py
---------------
Thin JSON persistence layer.
Handles missing files (first run) and malformed JSON (corruption)
without crashing the application.
"""

import json
import os
from constants import DATA_FILE


class FileHandler:
    """Static methods for loading and saving the students JSON file."""

    @staticmethod
    def load(filepath: str = DATA_FILE) -> list[dict]:
        """
        Read and return the student list from *filepath*.

        - Returns [] if the file does not exist (first run).
        - Returns [] if the file contains invalid JSON (corruption),
          printing a warning so the user is aware.
        """
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                # Guard: the file must contain a JSON array
                if not isinstance(data, list):
                    print(f"[FileHandler] WARNING: '{filepath}' does not contain a JSON array. Returning [].")
                    return []
                return data
        except json.JSONDecodeError as exc:
            print(f"[FileHandler] WARNING: Could not parse '{filepath}': {exc}. Returning [].")
            return []

    @staticmethod
    def save(data: list[dict], filepath: str = DATA_FILE) -> None:
        """
        Write *data* (a list of student dicts) to *filepath* as pretty-printed JSON.

        Creates parent directories automatically if they do not exist.
        Raises IOError on genuine write failures (disk full, permission denied).
        """
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
