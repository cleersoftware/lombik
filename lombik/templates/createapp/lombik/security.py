from werkzeug.security import generate_password_hash, check_password_hash

# It's kinda weird to jsut havea security file and maek no changes to the original functions
# But this adapter just ensures that if you prefer a differernt hashing alog, or soemthign changes lombik will remaing consistent
def hash_password(password):
    return generate_password_hash(password)

def validate_password_hash(password_hash, password) -> bool:
    return bool(check_password_hash(password_hash, password))
