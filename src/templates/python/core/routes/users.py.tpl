"""Example user routes."""

from fastapi import APIRouter, HTTPException, status

from ..api import UserService
from ..model import CreateUserRequest, UserResponse

router = APIRouter(prefix="/users", tags=["users"])
service = UserService()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(request: CreateUserRequest) -> UserResponse:
    """Create an example user."""
    return service.create_user(request)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str) -> UserResponse:
    """Return an example user by id."""
    user = service.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
