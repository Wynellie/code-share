from datetime import timedelta

from jose import jwt

from backend import security


def test_password_hash_and_verify():
    password = "strong_password_123"

    hashed = security.get_password_hash(password)

    assert hashed != password
    assert security.verify_password(password, hashed) is True
    assert security.verify_password("wrong_password", hashed) is False


def test_create_access_token_contains_sub():
    token = security.create_access_token({"sub": "42"}, expires_delta=timedelta(minutes=10))

    payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])

    assert payload["sub"] == "42"
    assert "exp" in payload
