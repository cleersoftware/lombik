import json

import pytest
from flask import Flask

from application.responses import Result, htmx_response


@pytest.fixture
def app_context():
    app = Flask(__name__)
    with app.test_request_context():
        yield app


def test_result_defaults():
    result = Result(success=True)
    assert result.data == {}
    assert result.message == ""


def test_htmx_response_trigger_string(app_context):
    response = htmx_response("", trigger="refresh")
    assert response.headers["HX-Trigger"] == "refresh"


def test_htmx_response_trigger_list(app_context):
    response = htmx_response("", trigger=["a", "b"])
    assert json.loads(response.headers["HX-Trigger"]) == {"a": True, "b": True}


def test_htmx_response_redirect(app_context):
    response = htmx_response("", redirect="/login")
    assert response.headers["HX-Redirect"] == "/login"
