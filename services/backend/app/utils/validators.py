import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


def is_valid_password(password: str) -> bool:
    """Minimum 8 chars, at least one letter and one digit."""
    if len(password) < 8:
        return False
    return bool(re.search(r"[A-Za-z]", password)) and bool(re.search(r"\d", password))
