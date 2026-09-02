import hashlib
import secrets
from datetime import timedelta

from flask import session

from lombik.constants import (
    TOKEN_BYTES,
    RESET_TOKEN_EXPIRY_MINUTES,
    PASSWORD_LOCKOUT_ATTEMPTS,
    PASSWORD_LOCKOUT_MINUTES
)
from lombik.errors import log_error
from lombik.responses import Result
from lombik.security import hash_password, validate_password_hash
from lombik.utils import utc_now, ensure_tz_aware
from lombik.validation import validate_password_strength, validate_user_creation

from db import db
from models import User


def authenticate_user(email: str, password: str) -> Result:
    email = (email or "").strip().lower()

    user = User.query.filter_by(email=email).first()

    if not user:
        return Result(success=False, message="Invalid credentials.")

    now = utc_now()

    if user.status == "deleted":
        delete_at = ensure_tz_aware(user.delete_at)
        if delete_at is None or delete_at <= now:
            message = "This account was deleted permanently."
        else:
            message = f"Account scheduled for removal: {delete_at.strftime('%Y-%m-%d %H:%M UTC')}."
        return Result(
            success=False,
            message=message
        )

    if user.locked_until and ensure_tz_aware(user.locked_until) > now:
        return Result(
            success=False,
            message="Too many attempts. Try again later.",
        )

    if not validate_password_hash(user.password_hash, password):
        user.failed_login_attempts = (
            user.failed_login_attempts or 0
        ) + 1

        if user.failed_login_attempts >= PASSWORD_LOCKOUT_ATTEMPTS:
            user.locked_until = (
                now + timedelta(minutes=PASSWORD_LOCKOUT_MINUTES)
            )
        try:
            db.session.commit()
        except Exception as e:
            log_error(exception=e)
            return Result(
                success=False,
                message="Could not verify user.",
            )

        return Result(
            success=False,
            message="Invalid credentials.",
        )
    
    user.last_seen = now
    user.failed_login_attempts = 0
    user.locked_until = None

    db.session.commit()

    return Result(
        success=True,
        data={"user_id": user.id},
        message="User authenticated successfully.",
    )


def logout_user() -> Result:
    session.clear()

    return Result(
        success=True,
        data={},
        message="User logged out.",
    )


def create_user(
    username: str,
    email: str,
    role: str,
    password: str,
    country: str,
) -> Result:

    username = username.strip().lower()

    validation = validate_user_creation(
        username=username,
        email=email,
        role=role,
        password=password,
    )

    if not validation.success:
        return validation

    user = User(
        username=username.strip(),
        email=email.strip().lower(),
        role=role,
        country=country,
        password_hash=hash_password(password),
        created_at=utc_now(),
    )

    try:
        db.session.add(user)
        db.session.commit()

        return Result(
            success=True,
            data={"user_id": user.id},
            message="User created successfully.",
        )

    except Exception as e:
        db.session.rollback()
        log_error(exception=e)

        return Result(
            success=False,
            message="User could not be created.",
        )


def change_password(
    user_id: str,
    old_password: str,
    new_password: str,
) -> Result:

    user = User.query.filter_by(id=user_id).first()

    if not user:
        return Result(
            success=False,
            message="User not found.",
        )

    if not validate_password_hash(
        user.password_hash,
        old_password,
    ):
        return Result(
            success=False,
            message="Old password is incorrect.",
        )

    validation = validate_password_strength(new_password)

    if not validation.success:
        return validation

    user.password_hash = hash_password(new_password)

    consume_reset_token(user)

    try:
        db.session.commit()

        return Result(
            success=True,
            data={},
            message="Password changed successfully.",
        )

    except Exception as e:
        db.session.rollback()
        log_error(exception=e)

        return Result(
            success=False,
            message="Password could not be changed.",
        )


def generate_token() -> tuple[str, str]:
    """
    Returns:
        raw_token, hashed_token

    The raw token is sent to the user.
    Only the hash is stored in the database.
    """

    raw_token = secrets.token_urlsafe(TOKEN_BYTES)
    hashed_token = hash_token(raw_token)

    return raw_token, hashed_token


def hash_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def verify_token(
    stored_hash: str | None,
    token: str | None,
) -> bool:

    if not stored_hash or not token:
        return False

    return secrets.compare_digest(
        stored_hash,
        hash_token(token),
    )


def create_reset_token(user: User) -> str:
    """
    Creates a new password-reset token.

    Only the hashed token is stored in the database.
    """

    raw_token, hashed_token = generate_token()

    user.reset_token_hash = hashed_token
    user.reset_token_expires_at = (
        utc_now()
        + timedelta(minutes=RESET_TOKEN_EXPIRY_MINUTES)
    )

    db.session.commit()

    return raw_token


def validate_reset_token(
    user: User | None,
    token: str | None,
) -> Result:

    if not user or not token:
        return Result(
            success=False,
            message="Invalid or expired reset link.",
        )

    if not verify_token(
        user.reset_token_hash,
        token,
    ):
        return Result(
            success=False,
            message="Invalid or expired reset link.",
        )

    if not user.reset_token_expires_at:
        return Result(
            success=False,
            message="Invalid or expired reset link.",
        )

    expires_at = ensure_tz_aware(user.reset_token_expires_at)

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(
            tzinfo=utc_now().tzinfo
        )

    if expires_at <= utc_now():
        return Result(
            success=False,
            message="Invalid or expired reset link.",
        )

    return Result(
        success=True,
        data={"user": user},
        message="Reset token is valid.",
    )


def consume_reset_token(user: User) -> None:
    """Invalidate the user's current password-reset token."""

    user.reset_token_hash = None
    user.reset_token_expires_at = None


def request_password_reset(email: str) -> Result:
    """
    Creates a password-reset token.

    Always returns a generic response to prevent
    account enumeration.

    The caller is responsible for constructing the URL
    and sending the email.
    """

    email = (email or "").strip().lower()

    generic_message = (
        "If an account exists, a password reset link will be sent."
    )

    if not email:
        return Result(
            success=True,
            message=generic_message,
        )

    user = User.query.filter_by(email=email).first()

    # optionally add more like: deactivated, suspended etc.
    if not user or user.status == "deleted":
        return Result(
            success=True,
            message=generic_message,
        )

    try:
        token = create_reset_token(user)

        return Result(
            success=True,
            data={
                "user_id": user.id,
                "email": user.email,
                "token": token,
            },
            message=generic_message,
        )

    except Exception as e:
        db.session.rollback()
        log_error(exception=e)

        return Result(
            success=True,
            message=generic_message,
        )


def reset_password(
    user_id: str,
    token: str,
    new_password: str,
) -> Result:

    user = User.query.filter_by(id=user_id).first()

    validation = validate_reset_token(
        user=user,
        token=token,
    )

    if not validation.success:
        return validation

    password_validation = validate_password_strength(
        password=new_password,
    )

    if not password_validation.success:
        return password_validation

    user.password_hash = hash_password(new_password)

    consume_reset_token(user)

    user.failed_login_attempts = 0
    user.locked_until = None

    try:
        db.session.commit()

        return Result(
            success=True,
            data={"user_id": user.id},
            message="Password reset successfully.",
        )

    except Exception as e:
        db.session.rollback()
        log_error(exception=e)

        return Result(
            success=False,
            message="Password could not be reset.",
        )