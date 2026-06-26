from sqlalchemy.exc import SQLAlchemyError
from zoneinfo import available_timezones
from ..responses import Result
from models import User
from db import db


def change_user_timezone(user_id: str, new_timezone: str):
    user = User.query.filter_by(id=user_id).first()
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