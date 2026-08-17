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