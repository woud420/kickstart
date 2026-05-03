"""Application service layer."""

from ..model import CreateUserRequest, InMemoryUserRepository, UserResponse


class UserService:
    """Small example service backed by an in-memory repository."""

    def __init__(self, repository: InMemoryUserRepository | None = None) -> None:
        self._repository = repository or InMemoryUserRepository()

    def create_user(self, request: CreateUserRequest) -> UserResponse:
        """Create a user and return its public representation."""
        user = self._repository.create(email=request.email)
        return UserResponse(id=user.id, email=user.email)

    def get_user(self, user_id: str) -> UserResponse | None:
        """Return a user by id."""
        user = self._repository.get(user_id)
        if user is None:
            return None
        return UserResponse(id=user.id, email=user.email)
