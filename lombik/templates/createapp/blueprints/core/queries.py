from . import core_bp

@core_bp.get("/get_names")
def get_names():
    names = ["John", "Doe", "Jane"]
    html = ""
    for name in names:
        html += f"<li>{name}</li>"
    return html