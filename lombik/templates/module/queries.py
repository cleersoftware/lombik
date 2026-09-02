from . import {{ module_name }}_bp
from models import *
from db import db
from flask import request
from lombik.extensions import cache, limiter
from lombik.responses import Result, htmx_response


@{{ module_name }}_bp.get("/resource")
def query():
    ...