from . import {{ module_name }}_bp
from models import *
from db import db
from lombik.extensions import cache, limiter


@{{ module_name }}_bp.get("/resource")
def function():
    ...