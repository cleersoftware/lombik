import secrets


def _generate_api_key():
    prefix = "sk-"
    key = secrets.token_urlsafe(32)
    return f"{prefix}{key}"


def get_api_key_from_request(req):
    """
    Extract Bearer token from the Authorization header.
    Returns the token string or None if missing/invalid.

    Expected format: "Bearer <token>
    """
    auth_header = req.headers.get('Authorization')
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]