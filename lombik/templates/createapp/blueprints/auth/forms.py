from lombik.forms import Field

class LoginForm:
    def __init__(self):
        self.fields = [
            Field("email", "Email", "email", required=True, min_length=5, max_length=120),
            Field("password", "Password", "password", required=True, min_length=8)
        ]