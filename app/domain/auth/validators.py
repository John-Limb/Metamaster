"""Password and username validation functions for authentication.

This module provides validation functions for password strength
and username format requirements.
"""

import re
from typing import List, Tuple

# Password requirements
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# Password pattern requirements
PASSWORD_PATTERNS: List[Tuple[str, str]] = [
    (r"[A-Z]", "uppercase letter"),
    (r"[a-z]", "lowercase letter"),
    (r"\d", "digit"),
    (r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', "special character"),
]


def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """Validate password meets strength requirements.

    Checks that the password:
    - Is between MIN_PASSWORD_LENGTH and MAX_PASSWORD_LENGTH characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character

    Args:
        password: The password string to validate.

    Returns:
        A tuple of (is_valid, list_of_missing_requirements).
        If is_valid is True, the list will be empty.
    """
    missing: List[str] = []

    if len(password) < MIN_PASSWORD_LENGTH:
        missing.append(f"at least {MIN_PASSWORD_LENGTH} characters")
    if len(password) > MAX_PASSWORD_LENGTH:
        missing.append(f"at most {MAX_PASSWORD_LENGTH} characters")

    for pattern, requirement in PASSWORD_PATTERNS:
        if not re.search(pattern, password):
            missing.append(requirement)

    return len(missing) == 0, missing


def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username format.

    Checks that the username:
    - Is between 3 and 50 characters
    - Contains only alphanumeric characters and underscores

    Args:
        username: The username string to validate.

    Returns:
        A tuple of (is_valid, error_message).
        If is_valid is True, error_message will be empty.
    """
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 50:
        return False, "Username must be at most 50 characters"
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""


def validate_email_format(email: str) -> Tuple[bool, str]:
    """Validate email format.

    Performs a basic format check on the email address.

    Args:
        email: The email string to validate.

    Returns:
        A tuple of (is_valid, error_message).
        If is_valid is True, error_message will be empty.
    """
    # Basic email pattern - not exhaustive but catches common issues
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    return True, ""
