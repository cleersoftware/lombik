"""Business logic for the {{ module_name }} module.

Keep page handlers in ``pages.py`` thin — do real work here so it can be
reused and tested independently of Flask.
"""

from application.responses import Result


def example_service() -> Result:
    """Replace with your own read/write functions."""
    return Result(success=True, data={}, message="{{ module_name }} service works.")
