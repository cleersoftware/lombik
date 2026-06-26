from dataclasses import dataclass, field
from typing import Any, Optional, Dict
from flask import make_response
import json

@dataclass
class Result:
    success: bool
    data: Optional[Dict[str, Any]] = field(default_factory=dict)
    message: str = ""


def htmx_response(html, *, trigger=None, redirect=None):
    """
    HTMX response helper.

    trigger can be:
    - str -> single event
    - list[str] -> multiple events
    - dict -> full HX-Trigger payload

    redirect:
    - str URL for HX-Redirect
    """

    response = make_response(html)

    if trigger:
        if isinstance(trigger, str):
            response.headers["HX-Trigger"] = trigger

        elif isinstance(trigger, list):
            response.headers["HX-Trigger"] = json.dumps(
                {event: True for event in trigger}
            )

        elif isinstance(trigger, dict):
            response.headers["HX-Trigger"] = json.dumps(trigger)

        else:
            raise TypeError("trigger must be str, list, or dict")

    if redirect:
        response.headers["HX-Redirect"] = redirect

    return response