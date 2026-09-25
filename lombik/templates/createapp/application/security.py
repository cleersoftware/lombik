from werkzeug.security import generate_password_hash, check_password_hash

# This adapter exists so password hashing stays consistent app-wide. If you
# ever switch algorithms (e.g. Argon2), change it here and nothing else breaks.
def hash_password(password):
    return generate_password_hash(password)

def validate_password_hash(password_hash, password) -> bool:
    return bool(check_password_hash(password_hash, password))
