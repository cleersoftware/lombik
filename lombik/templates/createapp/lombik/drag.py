from db import db 
from lombik.responses import Result

def apply_drag_change(instance, field, value):
    """Generic in‑place update for a drag‑and‑drop field change."""
    if hasattr(instance, field):
        setattr(instance, field, value)
        try:
            db.session.commit()
            return Result(success=True)
        except:    
            return Result(success=False)