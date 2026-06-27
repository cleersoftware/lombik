from datetime import datetime, timezone
from lombik.responses import Result
from lombik.constants import USER_ROLES
from models import User
import re


def utc_now():
    return datetime.now(timezone.utc)


def valid_email_pattern(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def validate_role(role: str) -> bool:
    return role.strip().lower() in {r.lower() for r in USER_ROLES}


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


def email_exists(email: str) -> bool:
    return User.query.filter_by(email=email).first() is not None


def validate_user_creation(username: str, email: str, role: str, password: str) -> Result:

    if username_exists(username):
        return Result(False, message="Username already taken")
    
    if not validate_role(role=role):
        return Result(False, message="Invalid role")

    if not valid_email_pattern(email):
        return Result(False, message="Invalid email address")

    if email_exists(email):
        return Result(False, message="Email already registered")

    password_check = validate_password_strength(password)
    if not password_check.success:
        return password_check

    return Result(True)