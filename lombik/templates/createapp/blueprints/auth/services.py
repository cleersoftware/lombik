from werkzeug.security import generate_password_hash, check_password_hash
from blueprints.core.error_logging import log_error
from datetime import datetime, timezone, timedelta
from blueprints.auth.roles import roles
from dataclasses import dataclass
from typing import Optional, Any
from models import User
from flask import g
from db import db
import traceback
import uuid
import re


@dataclass
class Result:
    success: bool
    data: Optional[Any] = None
    message: str = ""


def utc_now():
    return datetime.now(timezone.utc)


def valid_email_pattern(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> Result:
    if len(password) < 8:
        return Result(False, message="Password must be at least 8 characters long.")

    if not re.search(r"[A-Z]", password):
        return Result(False, message="Password must contain at least one uppercase letter.")

    if not re.search(r"[a-z]", password):
        return Result(False, message="Password must contain at least one lowercase letter.")

    if not re.search(r"[^A-Za-z0-9]", password):
        return Result(False, message="Password must contain at least one special character.")

    return Result(True)

def username_exists(username: str) -> bool:
    return User.query.filter_by(username=username).first() is not None

def validate_role(role: str) -> bool:
    return role.strip().lower() in {r.lower() for r in roles()}


def email_exists(email: str) -> bool:
    return User.query.filter_by(email=email).first() is not None


def validate_user_creation(username: str, email: str, role: str, password: str) -> Result:

    if username_exists(username):
        return Result(False, message="Username already taken")
    
    if not validate_role(role=role):
        return Result(False, message="Invalid role")

    if not valid_email_pattern(email):
        return Result(False, message="Invalid credentials")

    if email_exists(email):
        return Result(False, message="Email already registered")

    password_check = validate_password_strength(password)
    if not password_check.success:
        return password_check

    return Result(True)


def create_user(username: str, email: str, role: str, password: str) -> Result:

    validation = validate_user_creation(username, email, role,  password)
    if not validation.success:
        return validation

    user = User(
        user_id=str(uuid.uuid4()),
        username=username,
        email=email,
        role=role,
        password_hash=generate_password_hash(password),
        created_at=utc_now()
    )
    try:
        db.session.add(user)
        db.session.commit()
        
        return Result(True, "User created successfully")
    
    except Exception as e:
        log_error(
            user_id=getattr(g, "user_id", None),
            function="create_user",
            action="Creating user",
            exception=e
        )

        return Result(False, "An error occured when creating the user")
    

def authenticate_user(email, password):
    user = User.query.filter_by(email=email).first()

    if not user:
        return {
            "success": False,
            "message": "Invalid credentials"
        }
    
    now = datetime.now(timezone.utc)

    if user.status == "deleted":
        delete_at = user.deactivated_at + timedelta(days=30)
        if delete_at < now:
            message = "This account and all its data was deleted permanently. Please create a new one"
        else:
            message = f"This account will be permanently deleted on {delete_at.strftime("%Y-%m-%d %H:%M UTC")}. To stop it please email us!"
        return {
            "success": False,
            "message": message
        }
    
    now = datetime.now(timezone.utc)

    if user.locked_until and user.locked_until > now:
        return {
            "success": False,
            "message": "Too many attempts. Try again later."
        }
    
    if not check_password_hash(user.password_hash, password):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        
        if user.failed_login_attempts >= 5:
            user.locked_until = now + timedelta(minutes=10)
        
        db.session.commit()

        return {
            "success": False,
            "message": "Incorrect password"
        }
    
    user.failed_login_attempts = 0
    user.locked_until = None
    db.session.commit()

    return {
        "success": True,
        "message": "user authenticated successfully",
        "user": user
    }

    
def load_user(user_id):
    user = db.session.query(
        User.user_id,
        User.username,
        User.email,
        User.role,
        User.status,
        User.created_at
    ).filter_by(user_id=user_id).first()
    if not user:
        return None

    return user