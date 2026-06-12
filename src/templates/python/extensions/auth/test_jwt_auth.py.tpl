"""Unit tests for the generated JWT helpers (no infrastructure required)."""

from src.handler.auth import JWTAuth

TEST_SECRET = "test-secret-not-for-production"


def test_access_token_roundtrip() -> None:
    auth = JWTAuth(TEST_SECRET)

    token = auth.create_access_token("user-123")
    verified = auth.verify_access_token(token)

    assert verified is not None
    assert verified["subject"] == "user-123"
    assert verified["token_type"] == "access"


def test_tampered_and_foreign_tokens_are_rejected() -> None:
    auth = JWTAuth(TEST_SECRET)
    token = auth.create_access_token("user-123")

    assert auth.verify_access_token(token + "tampered") is None
    assert JWTAuth("a-different-secret").verify_access_token(token) is None


def test_password_hash_roundtrip() -> None:
    auth = JWTAuth(TEST_SECRET)

    password_hash = auth.hash_password("correct horse battery staple")

    assert auth.verify_password("correct horse battery staple", password_hash)
    assert not auth.verify_password("wrong password", password_hash)
