from backend.core.security import (
    create_access_token,
    decode_token,
    get_password_hash,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    password = "admin123456"

    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed)


def test_token_roundtrip() -> None:
    token = create_access_token("1")

    payload = decode_token(token)

    assert payload is not None
    assert payload["sub"] == "1"
