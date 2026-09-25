from dataclasses import dataclass, field
from typing import Any, Optional, Dict
from flask import make_response, render_template
import json


@dataclass
class Result:
    success: bool
    data: Optional[Dict[str, Any]] = field(default_factory=dict)
    message: str = ""


def htmx_response(html="", *, trigger=None, redirect=None, status=200):
    """
    HTMX response helper.

    html can be the filepath. This response wraps in flask's render_template().
    Pass an empty string (the default) to return an empty body, e.g. when the
    only thing you need is an HX-Redirect or HX-Trigger header.

    trigger can be:
    - str -> single event
    - list[str] -> multiple events
    - dict -> full HX-Trigger payload

    redirect:
    - str URL for HX-Redirect
    """

    response = make_response(render_template(html) if html else "", status)

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