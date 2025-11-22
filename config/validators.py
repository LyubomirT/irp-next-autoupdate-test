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
