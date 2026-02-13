"""Password hashing utilities using Argon2id.

This module provides secure password hashing and verification using Argon2id,
which is the recommended algorithm by OWASP for password hashing.

Argon2id provides resistance against:
- GPU-based attacks (memory-hard)
- Side-channel attacks
- Time-memory trade-off attacks
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# OWASP recommended Argon2id parameters
# See: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
ph = PasswordHasher(
    time_cost=3,           # Number of iterations (passes over memory)
    memory_cost=65536,     # 64MB memory usage (in KiB)
    parallelism=4,         # Number of parallel threads
    hash_len=32,           # Hash length in bytes
    salt_len=16,           # Salt length in bytes
)


def hash_password(password: str) -> str:
    """Hash a password using Argon2id.

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed password string in Argon2id format.

    Example:
        >>> hashed = hash_password("my_secure_password")
        >>> hashed.startswith("$argon2id$")
        True
    """
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a hash.

    This function securely compares the password against the stored hash
    using constant-time comparison to prevent timing attacks.

    Args:
        password: The plain text password to verify.
        password_hash: The stored password hash.

    Returns:
        True if the password matches the hash, False otherwise.

    Example:
        >>> hashed = hash_password("my_secure_password")
        >>> verify_password("my_secure_password", hashed)
        True
        >>> verify_password("wrong_password", hashed)
        False
    """
    try:
        ph.verify(password_hash, password)
        return True
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """Check if a hash needs to be rehashed.

    This should be called after successful password verification to check
    if the hash parameters have changed and the password should be rehashed.

    Args:
        password_hash: The stored password hash to check.

    Returns:
        True if the hash should be rehashed, False otherwise.

    Example:
        >>> hashed = hash_password("my_secure_password")
        >>> needs_rehash(hashed)
        False
    """
    return ph.check_needs_rehash(password_hash)
