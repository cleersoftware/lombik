from lombik.validation import validate_user_creation
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
from lombik.responses import Result
from lombik.constants import ROLES
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
        return Result(True, message="User created successfully")
    
    except Exception as e:
        return Result(False, message="An error occurred when creating the user")
    

def authenticate_user(email, password):
    user = User.query.filter_by(email=email).first()

    if not user:
        return Result(False, message="invalid credentials")
    
    now = datetime.now(timezone.utc)

    if user.status == "deleted":
        delete_at = user.deactivated_at + timedelta(days=30)
        if delete_at < now:
            message = "This account and all its data was deleted permanently. Please create a new one"
        else:
            message = f"This account will be permanently deleted on {delete_at.strftime('%Y-%m-%d %H:%M UTC')}."
        return Result(False, message=message)
    
    now = datetime.now(timezone.utc)

    if user.locked_until and user.locked_until > now:
        return Result(False, message="Too many attempts. Try again later.")
    
    if not check_password_hash(user.password_hash, password):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        
        if user.failed_login_attempts >= 5:
            user.locked_until = now + timedelta(minutes=10)
        
        db.session.commit()

        return Result(False, message="Invalid credentials")
    
    user.failed_login_attempts = 0
    user.locked_until = None
    db.session.commit()

    return Result(
        True, 
        data={"user_id": user.user_id},
        message="User authenticated successfully"
    )
