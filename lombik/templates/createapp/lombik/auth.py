from lombik.validation import validate_user_creation, validate_password_strength
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
from lombik.responses import Result
import secrets
import hashlib
from lombik.constants import ROLES, TOKEN_BYTES
from models.user import User
from db import db
import uuid


def utc_now():
    return datetime.now(timezone.utc)

def create_user(username: str, email: str, role: str, password: str) -> Result:
    validation = validate_user_creation(username, email, role, password)
    if not validation.success:
        return validation

    user = User(
        id=str(uuid.uuid4()),
        username=username,
        email=email,
        role=role,
        password_hash=generate_password_hash(password),
        created_at=utc_now()
    )
    try:
        db.session.add(user)
        db.session.commit()
        return Result(success=True, message="User created successfully.")
    
    except Exception as e:
        db.session.rollback()
        return Result(success=False, message=f"An error occurred when creating the user: {e}")
    

def authenticate_user(email, password):
    user = User.query.filter_by(email=email).first()

    if not user:
        return Result(success=False, message="invalid credentials")
    
    now = utc_now()

    if user.status == "deleted":
        delete_at = user.deactivated_at + timedelta(days=30)
        if delete_at < now:
            message = "This account and all its data was deleted permanently. Please create a new one."
        else:
            message = f"This account will be permanently deleted on {delete_at.strftime('%Y-%m-%d %H:%M UTC')}."
        return Result(success=False, message=message)
    

    if user.locked_until and user.locked_until > now:
        return Result(success=False, message="Too many attempts. Try again later.")
    
    if not check_password_hash(user.password_hash, password):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        
        if user.failed_login_attempts >= 5:
            user.locked_until = now + timedelta(minutes=10)
        
        db.session.commit()

        return Result(success=False, message="Invalid credentials.")
    
    user.failed_login_attempts = 0
    user.locked_until = None
    db.session.commit()

    return Result(
        success=True, 
        data={"user_id": user.id},
        message="User authenticated successfully."
    )


def logout_user():
    session.clear()
    return Result(success=True, data={}, message="User logged out.")


def change_password(user_id: str, old_password: str, new_password: str):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return Result(success=False, data={}, message="User not found.")

    if not check_password_hash(user.password_hash, old_password):
        return Result(success=False, data={}, message="Old password is incorrect.")

    if not validate_password_strength(new_password):
        return Result(success=False, data={}, message="Weak password.")

    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return Result(success=True, data={}, message="Password changed.")


def generate_token():
    """
    Returns:
        (raw_token, hashed_token)
    """
    token = secrets.token_urlsafe(TOKEN_BYTES)
    return token, _hash_token(token)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token(stored_hash: str, token: str) -> bool:
    if not stored_hash or not token:
        return False

    return stored_hash == _hash_token(token)


def consume_token(user_id, field_name: str = "reset_token"):
    """
    Generic token invalidation.
    Works for reset tokens, email verify tokens, etc.
    """
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return None
    
    setattr(user, field_name, None)


def create_reset_token_for_user(user_id):
    """
    Creates and stores hashed token on user.
    Returns raw token (for email sending).
    """
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return None
    token, token_hash = generate_token()

    user.reset_token = token_hash
    return token


def validate_reset_token(user, token: str) -> bool:
    return verify_token(user.reset_token, token)


"""
forgot_password()
verify_email()
"""