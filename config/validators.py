import re

def validate_email(value: str):
    """
    Validates that the value is a valid email address.
    Raises ValueError if invalid.
    """
    if not value:
        return

    # Simple regex for email validation
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(pattern, value):
        raise ValueError("Invalid email address format.")


def validate_port(value: int):
    """
    Validates that the value is a valid TCP/UDP port number.
    Raises ValueError if invalid.
    """
    if value is None:
        return

    try:
        port = int(value)
    except (TypeError, ValueError):
        raise ValueError("Port must be a number.")

    if port < 1 or port > 65535:
        raise ValueError("Port must be between 1 and 65535.")
