from . import {{ module_name }}_bp
from lombik.responses import Result, htmx_response


@{{ module_name }}_bp.post("/endpoint")
def action():
    ...