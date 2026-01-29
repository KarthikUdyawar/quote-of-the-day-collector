from typing import Any


def get_text(value: Any) -> str:
    """
    Normalize a value into a stripped string suitable for RSS entry fields.
    
    Parameters:
        value (Any): The value to normalize; if it's a list, the first element is used.
    
    Returns:
        str: The input converted to a string with leading/trailing whitespace removed; returns an empty string for None or an empty list.
    """
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value or "").strip()
