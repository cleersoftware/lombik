from application.security import hash_password, validate_password_hash


def test_hash_and_verify():
    hashed = hash_password("SuperSecret123!")
    assert hashed != "SuperSecret123!"
    assert validate_password_hash(hashed, "SuperSecret123!") is True


def test_verify_wrong_password():
    hashed = hash_password("SuperSecret123!")
    assert validate_password_hash(hashed, "wrong-password") is False
