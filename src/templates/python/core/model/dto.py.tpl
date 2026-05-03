"""Request and response DTOs."""

from pydantic import BaseModel, EmailStr


class CreateUserRequest(BaseModel):
    """Request body for creating a user."""

    email: EmailStr


class UserResponse(BaseModel):
    """Public user response."""

    id: str
    email: EmailStr
