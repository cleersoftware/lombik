from dataclasses import dataclass, field
from typing import Any


@dataclass
class Field:
    name: str
    label: str
    required: bool = False
    value: Any = ""
    error: str | None = None
    help_text: str | None = None
    id: str | None = None

    def __post_init__(self):
        if self.id is None:
            self.id = self.name

    @property
    def type(self) -> str:
        return "field"


@dataclass
class InputField(Field):
    field_type: str = "text"
    min_length: int | None = None
    max_length: int | None = None
    placeholder: str | None = None
    autocomplete: str | None = None

    @property
    def type(self) -> str:
        return "input"


@dataclass
class SelectField(Field):
    options: list[tuple[str, str]] = field(default_factory=list)

    @property
    def type(self) -> str:
        return "select"


@dataclass
class CheckboxField(Field):
    value: bool = False

    @property
    def type(self) -> str:
        return "checkbox"


@dataclass
class TextareaField(Field):
    rows: int = 4
    placeholder: str | None = None
    min_length: int | None = None
    max_length: int | None = None

    @property
    def type(self) -> str:
        return "textarea"


class Form:
    def __init__(self, fields: list[Field] | None = None):
        self.fields = fields or []

    def get_field(self, name: str) -> Field | None:
        return next(
            (field for field in self.fields if field.name == name),
            None,
        )

    def set_value(self, name: str, value: Any) -> None:
        field = self.get_field(name)

        if field:
            field.value = value

    def set_error(self, name: str, error: str) -> None:
        field = self.get_field(name)

        if field:
            field.error = error

    @property
    def has_errors(self) -> bool:
        return any(field.error for field in self.fields)

    @property
    def data(self) -> dict[str, Any]:
        return {field.name: field.value for field in self.fields}

    def validate(self) -> bool:
        for field in self.fields:
            value = field.value

            if field.required:
                if value is None or value == "" or value is False:
                    field.error = "This field is required."
                    continue

            if value in (None, "", False):
                continue

            if isinstance(field, InputField):
                if field.min_length and len(str(value)) < field.min_length:
                    field.error = f"Minimum length is {field.min_length}."
                elif field.max_length and len(str(value)) > field.max_length:
                    field.error = f"Maximum length is {field.max_length}."

            if isinstance(field, TextareaField):
                if field.min_length and len(str(value)) < field.min_length:
                    field.error = f"Minimum length is {field.min_length}."
                elif field.max_length and len(str(value)) > field.max_length:
                    field.error = f"Maximum length is {field.max_length}."

        return not self.has_errors