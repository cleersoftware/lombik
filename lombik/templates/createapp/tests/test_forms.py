from application.forms import (
    CheckboxField,
    Form,
    InputField,
    SelectField,
    TextareaField,
)


def test_form_data_returns_values():
    form = Form([
        InputField(name="name", label="Name", value="Ada"),
        SelectField(name="role", label="Role", value="admin"),
    ])
    assert form.data == {"name": "Ada", "role": "admin"}


def test_required_validation():
    form = Form([
        InputField(name="name", label="Name", required=True),
    ])
    assert form.validate() is False
    assert form.get_field("name").error == "This field is required."


def test_length_validation():
    form = Form([
        InputField(name="name", label="Name", min_length=3, max_length=5, value="toolong"),
    ])
    assert form.validate() is False
    assert "Maximum length" in form.get_field("name").error


def test_checkbox_value_coercion():
    field = CheckboxField(name="active", label="Active")
    assert field.value is False
    field.value = True
    assert field.value is True


def test_select_options():
    field = SelectField(name="role", label="Role", options=[("admin", "Admin"), ("user", "User")])
    assert field.options[0] == ("admin", "Admin")
    assert field.type == "select"
