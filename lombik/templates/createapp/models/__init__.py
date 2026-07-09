from .errors import Error
from .users import User 

def register_models():
    """
    Import all models in here to be supplied in app.py
    """
    return [User, Error]


__all__ = ["User", "Error"]