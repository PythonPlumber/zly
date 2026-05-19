import pytest
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


def test_hash_and_verify_password():
    hashed = hash_password("my_password")
    assert verify_password("my_password", hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_create_and_decode_token():
    token = create_access_token({"sub": "user123"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user123"


def test_decode_invalid_token():
    payload = decode_access_token("invalid_token_here")
    assert payload is None
