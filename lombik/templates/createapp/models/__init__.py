from blueprints.auth.models import User
from blueprints.core.models import Error

def load_models():
    """
    Import all models in here to be supplied in app.py
    """
    return [User, Error]


__all__ = ["User", "Error"]