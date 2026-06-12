"""JWT helpers for {{ service_name }}."""

from datetime import UTC, datetime, timedelta
from typing import TypedDict

import bcrypt
from jose import JWTError, jwt

type JwtClaim = str | int | datetime
type JwtPayload = dict[str, JwtClaim]


class VerifiedToken(TypedDict):
    """Verified token payload returned to callers."""

    subject: str
    token_type: str


class JWTAuth:
    """Small JWT helper for generated services."""

    def __init__(
        self,
        secret_key: str,
        *,
        algorithm: str = "HS256",
        access_token_minutes: int = 30,
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_minutes = access_token_minutes

    def create_access_token(self, subject: str) -> str:
        """Create an access token for a subject."""
        now = datetime.now(UTC)
        payload: JwtPayload = {
            "sub": subject,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=self._access_token_minutes),
        }
        return str(jwt.encode(payload, self._secret_key, algorithm=self._algorithm))

    def verify_access_token(self, token: str) -> VerifiedToken | None:
        """Verify an access token."""
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except JWTError:
            return None

        subject = payload.get("sub")
        token_type = payload.get("type")
        if not isinstance(subject, str) or token_type != "access":
            return None
        return {"subject": subject, "token_type": "access"}

    def hash_password(self, password: str) -> str:
        """Hash a password with bcrypt."""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against a bcrypt hash."""
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
