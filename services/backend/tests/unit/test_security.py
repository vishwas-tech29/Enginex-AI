import uuid

from app.utils.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.utils.validators import is_valid_email, is_valid_password


def test_password_hash_and_verify_roundtrip():
    hashed = hash_password("Sup3rSecret")
    assert hashed != "Sup3rSecret"
    assert verify_password("Sup3rSecret", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_roundtrip():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"


def test_email_validation():
    assert is_valid_email("user@example.com")
    assert not is_valid_email("not-an-email")


def test_password_validation():
    assert is_valid_password("abc12345")
    assert not is_valid_password("short1")
    assert not is_valid_password("nodigitshere")
