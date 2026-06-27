from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import extract
from zoneinfo import available_timezones
from lombik.responses import Result
from lombik.constants import USER_ROLES, USER_STATUSES, ADMIN_ROLES
from datetime import datetime, timezone, timedelta
from lombik.extensions import cache, limit
from typing import Optional
from models import User
from db import db


def utc_now():
    return datetime.now(timezone.utc)


@cache.memoize(timeout=30)
def get_user_by_email(email: str) -> Optional[User]:
    if not email:
        return None
    return User.query.filter_by(email=email.strip().lower()).first()


@cache.memoize(timeout=30)
def get_user_by_id(id: str) -> Optional[User]:
    if not id:
        return None
    return User.query.filter_by(id=id.strip()).first()


@cache.memoize(timeout=30)
def get_user_by_username(username: str) -> Optional[User]:
    if not username:
        return None
    return User.query.filter_by(username=username.strip()).first()


@cache.memoize(timeout=30)
def get_all_users() -> list[User]:
    return User.query.all()


@cache.memoize(timeout=30)
def get_active_users() -> list[User]:
    return User.query.filter_by(status='active').all()


@cache.memoize(timeout=30)
def get_inactive_users() -> list[User]:
    return User.query.filter_by(status='inactive').all()


@cache.memoize(timeout=30)
def get_deleted_users() -> list[User]:
    return User.query.filter_by(status='deleted').all()


@cache.memoize(timeout=30)
def get_locked_out_users() -> list[User]:
    return User.query.filter(User.locked_until > utc_now()).all()


@cache.memoize(timeout=600)
def get_birthday_users() -> list[User]:
    return User.query.filter(
        extract('month', User.birthday) == datetime.today().month,
        extract('day', User.birthday) == datetime.today().day
    ).all()


@cache.memoize(timeout=600)
def get_users_active_since(days: int) -> list[User]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return User.query.filter(User.last_seen >= cutoff).all()


def is_admin(user: User) -> bool:
    return bool(user and user.role in ADMIN_ROLES)


def change_user_status(user_id: str, new_status: str) -> Result:
    user = get_user_by_id(id=user_id)
    if not user:
        return Result(success=False, data=None, message="User not found.")
    
    new_status = new_status.lower().strip() 
    if new_status not in USER_STATUSES:
        return Result(success=False, data=None, message="Invalid status.")
    
    if new_status == user.status:
        return Result(success=True, data=user, message="User already has this status.")

    user.status = new_status
    db.session.commit()
    return Result(success=True, data=user, message=f"User status change to {new_status}")


def change_user_role(user_id: str, new_role: str) -> Result:
    user = get_user_by_id(id=user_id)
    if not user:
        return Result(success=False, data=None, message="User not found.")
    
    if not is_admin(user):
        return Result(success=False, data=None, message="No permission to change user role.")
    
    new_role = new_role.lower().strip() 
    if new_role not in USER_ROLES:
        return Result(success=False, data=None, message="Invalid role.")
    
    if new_role == user.status:
        return Result(success=True, data=user, message="User already has this role.")

    user.status = new_role
    db.session.commit()
    return Result(success=True, data=user, message=f"User role change to {new_role}")


@limit.limiter("60 per minute")
def change_user_timezone(user_id: str, new_timezone: str) -> Result:
    user = get_user_by_id(id=user_id)
    if not user:
        return Result(success=False, data=None, message="User not found.")

    if new_timezone not in available_timezones():
        return Result(success=False, data=None, message="Invalid timezone.")
    if user.timezone == new_timezone:
        return Result(success=True, data=new_timezone, message="Timezone already set.")

    user.timezone = new_timezone
    
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return Result(success=False, data=None, message="Timezone could not be changed.")
    return Result(success=True, data={"new_timezone": new_timezone}, message="Timezone changed successfully.")