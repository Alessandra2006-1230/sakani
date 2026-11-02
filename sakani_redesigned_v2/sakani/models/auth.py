"""Password hashing, password checks and input validators for Sakani."""

import hashlib
import hmac
import os
import re

PBKDF2_ITERATIONS = 200_000
SALT_BYTES = 16
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def hash_password(password, salt=None):
    """Return (hash_hex, salt_hex) using PBKDF2-HMAC-SHA256.

    A random salt is created with os.urandom when none is supplied.
    """
    if salt is None:
        salt = os.urandom(SALT_BYTES).hex()
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PBKDF2_ITERATIONS,
    )
    return digest.hex(), salt


def verify_password(password, stored_hash, salt):
    """Return True when the password matches the stored hash and salt."""
    try:
        candidate, _ = hash_password(password, salt)
    except ValueError:
        return False
    return hmac.compare_digest(candidate, stored_hash)


def is_valid_email(email):
    """Return True when the email has a basic valid shape."""
    return bool(EMAIL_PATTERN.match(email.strip()))


def validate_signup(full_name, email, password, confirm):
    """Validate sign-up fields and return (ok, message)."""
    name = full_name.strip()
    email = email.strip()
    if not name:
        return False, "Please enter your full name."
    if len(name) < 2:
        return False, "Full name is too short."
    if len(name) > 100:
        return False, "Full name is too long (maximum 100 characters)."
    if not email:
        return False, "Please enter your email address."
    if len(email) > 120 or not is_valid_email(email):
        return False, "Please enter a valid email address."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if password != confirm:
        return False, "Passwords do not match."
    return True, ""


def validate_login(email, password):
    """Validate login fields and return (ok, message)."""
    if not email.strip():
        return False, "Please enter your email address."
    if not is_valid_email(email):
        return False, "Please enter a valid email address."
    if not password:
        return False, "Please enter your password."
    return True, ""
