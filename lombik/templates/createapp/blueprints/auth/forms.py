from lombik.forms import (
    Form,
    InputField,
    SelectField,
    CheckboxField,
)

from lombik.utils import get_countries

class LoginForm(Form):
    def __init__(self):
        super().__init__([
            InputField(
                name="email",
                label="Email",
                field_type="email",
                required=True,
                min_length=5,
                max_length=120,
                autocomplete="email",
                placeholder="you@example.com",
            ),
            InputField(
                name="password",
                label="Password",
                field_type="password",
                required=True,
                min_length=8,
                max_length=120,
                autocomplete="current-password",
                placeholder="••••••••",
            ),
        ])


class RegisterForm(Form):
    def __init__(self):
        super().__init__([
             InputField(
                name="username",
                label="Username",
                id="reg-username",
                field_type="text",
                required=True,
                min_length=3,
                max_length=120,
                autocomplete="username",
                placeholder="johndoe",
            ),
            InputField(
                name="email",
                label="Email",
                id="reg-email",
                field_type="email",
                required=True,
                min_length=5,
                max_length=120,
                autocomplete="email",
                placeholder="you@example.com",
            ),
            InputField(
                name="password",
                label="Password",
                id="reg-password",
                field_type="password",
                required=True,
                min_length=8,
                max_length=120,
                autocomplete="new-password",
                placeholder="••••••••",
            ),
            InputField(
                name="confirm_password",
                label="Confirm password",
                id="reg-confirm-password",
                field_type="password",
                required=True,
                min_length=8,
                max_length=120,
                autocomplete="new-password",
                placeholder="••••••••",
            ),
            SelectField(
                name="country",
                label="Country",
                id="reg-country",
                required=True,
                options=[
                    (country, country) for country in get_countries()
                ],
            ),
            CheckboxField(
                name="terms",
                label="I agree to the terms and conditions",
                id="agree-terms",
                required=True,
            ),
        ])