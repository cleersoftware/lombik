from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import extract
from lombik.responses import Result
from lombik.constants import USER_ROLES, USER_STATUSES, ADMIN_ROLES, TIMEZONES
from datetime import datetime, timezone, timedelta
from lombik.extensions import cache, limiter
from lombik.utils import utc_now, utc_next_month
from typing import Optional
from models import User
from db import db


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


def get_all_users() -> list[User]:
    return User.query.all()


def get_active_users() -> list[User]:
    return User.query.filter_by(status='active').all()


def get_inactive_users() -> list[User]:
    return User.query.filter_by(status='inactive').all()


def get_deleted_users() -> list[User]:
    return User.query.filter_by(status='deleted').all()


def get_locked_out_users() -> list[User]:
    return User.query.filter(User.locked_until > utc_now()).all()


def get_birthday_users() -> list[User]:
    return User.query.filter(
        extract('month', User.birthday) == datetime.today().month,
        extract('day', User.birthday) == datetime.today().day
    ).all()


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
    
    new_role = new_role.lower().strip() 
    if new_role not in USER_ROLES:
        return Result(success=False, data=None, message="Invalid role.")
    
    if new_role == user.role:
        return Result(success=True, data=user, message="User already has this role.")

    user.role = new_role
    db.session.commit()
    return Result(success=True, data=user, message=f"User role change to {new_role}")


def change_user_timezone(user_id: str, new_timezone: str) -> Result:
    user = get_user_by_id(id=user_id)
    if not user:
        return Result(success=False, data=None, message="User not found.")

    if new_timezone not in TIMEZONES:
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


def mark_user_as_deleted(user_id_to_delete: str, user_id_deleting: str):
    """
    Marks user as status = 'deleted' and sets delete_at field to 1 month from now.
    There shall be a cron job that deletes all users where delete_at < today
    """
    deleter = get_user_by_id(user_id_deleting)

    if not deleter:
        return Result(success=False, data=None, message="Deleter not found.")

    if deleter.role not in ADMIN_ROLES:
        return Result(success=False, data=None, message="You are not allowed to delete users.")

    user_to_delete = get_user_by_id(user_id_to_delete)

    if not user_to_delete:
        return Result(success=False, data=None, message="User not found.")

    user_to_delete.status = "deleted"
    user_to_delete.deactivated_at = utc_now()
    user_to_delete.delete_at = utc_next_month()
    try:
        db.session.add(user_to_delete)
        db.session.commit()
        return Result(success=True, data=None, message="User deleted successfully.")
    except Exception as e:
        db.session.rollback()
        return Result(success=False, data=None, message=f"User could not be deleted. Error: {e}")