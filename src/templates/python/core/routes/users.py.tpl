"""User routes - HTTP endpoints for user operations.

This module contains route handlers for user-related HTTP endpoints.
Routes are thin wrappers that delegate to services for business logic.
"""

import json
from typing import Dict, Any
from urllib.parse import urlparse, parse_qs

from ..api.services import UserService, UserProfileService
from ..model.dto import (
    CreateUserRequest, UpdateUserRequest, PaginationRequest,
    CreateUserProfileRequest, UpdateUserProfileRequest,
    ApiResponse, ErrorResponse
)
from ..model.repository import (
    InMemoryUserRepository, InMemoryUserProfileRepository,
    UserNotFoundError, UserAlreadyExistsError,
    ProfileNotFoundError, ProfileAlreadyExistsError
)


class UserRoutes:
    """HTTP route handlers for user operations."""
    
    def __init__(self):
        """Initialize user routes with in-memory repositories."""
        self.user_repo = InMemoryUserRepository()
        self.profile_repo = InMemoryUserProfileRepository()
        self.user_service = UserService(self.user_repo, self.profile_repo)
        self.profile_service = UserProfileService(self.user_repo, self.profile_repo)
    
    async def handle_users_endpoint(self, method: str, path: str, body: str = None, query_params: Dict[str, str] = None) -> tuple[int, Dict[str, Any]]:
        """Handle /api/v1/users endpoint.
        
        Args:
            method: HTTP method (GET, POST)
            path: Request path
            body: Request body (for POST)
            query_params: Query parameters
            
        Returns:
            Tuple of (status_code, response_data)
        """
        try:
            if method == "GET":
                return await self._list_users(query_params or {})
            elif method == "POST":
                return await self._create_user(body)
            else:
                return 405, {"success": False, "message": "Method not allowed", "error_code": "METHOD_NOT_ALLOWED"}
        
        except Exception as e:
            return 500, {"success": False, "message": str(e), "error_code": "INTERNAL_ERROR"}
    
    async def handle_user_endpoint(self, method: str, user_id: str, body: str = None) -> tuple[int, Dict[str, Any]]:
        """Handle /api/v1/users/{id} endpoint.
        
        Args:
            method: HTTP method (GET, PUT, DELETE)
            user_id: User ID from path
            body: Request body (for PUT)
            
        Returns:
            Tuple of (status_code, response_data)
        """
        try:
            if method == "GET":
                return await self._get_user(user_id)
            elif method == "PUT":
                return await self._update_user(user_id, body)
            elif method == "DELETE":
                return await self._delete_user(user_id)
            else:
                return 405, {"success": False, "message": "Method not allowed", "error_code": "METHOD_NOT_ALLOWED"}
        
        except Exception as e:
            return 500, {"success": False, "message": str(e), "error_code": "INTERNAL_ERROR"}
    
    async def handle_user_profile_endpoint(self, method: str, user_id: str, body: str = None) -> tuple[int, Dict[str, Any]]:
        """Handle /api/v1/users/{id}/profile endpoint.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            user_id: User ID from path
            body: Request body (for POST, PUT)
            
        Returns:
            Tuple of (status_code, response_data)
        """
        try:
            if method == "GET":
                return await self._get_user_profile(user_id)
            elif method == "POST":
                return await self._create_user_profile(user_id, body)
            elif method == "PUT":
                return await self._update_user_profile(user_id, body)
            elif method == "DELETE":
                return await self._delete_user_profile(user_id)
            else:
                return 405, {"success": False, "message": "Method not allowed", "error_code": "METHOD_NOT_ALLOWED"}
        
        except Exception as e:
            return 500, {"success": False, "message": str(e), "error_code": "INTERNAL_ERROR"}
    
    async def _list_users(self, query_params: Dict[str, str]) -> tuple[int, Dict[str, Any]]:
        """List users with pagination."""
        try:
            # Parse pagination parameters
            page = int(query_params.get("page", "1"))
            page_size = int(query_params.get("page_size", "10"))
            sort_by = query_params.get("sort_by", "created_at")
            sort_order = query_params.get("sort_order", "desc")
            
            pagination = PaginationRequest(
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            result = await self.user_service.list_users(pagination)
            
            return 200, {
                "success": True,
                "data": result.users,
                "pagination": {
                    "page": result.page,
                    "page_size": result.page_size,
                    "total": result.total,
                    "has_next": result.has_next,
                    "has_previous": result.has_previous
                }
            }
        
        except ValueError as e:
            return 400, {"success": False, "message": str(e), "error_code": "VALIDATION_ERROR"}
    
    async def _create_user(self, body: str) -> tuple[int, Dict[str, Any]]:
        """Create a new user."""
        try:
            data = json.loads(body) if body else {}
            
            request = CreateUserRequest(
                username=data.get("username", ""),
                email=data.get("email", ""),
                full_name=data.get("full_name", ""),
                profile_data=data.get("profile_data", {})
            )
            
            user = await self.user_service.create_user(request)
            
            return 201, {
                "success": True,
                "message": "User created successfully",
                "data": user.__dict__
            }
        
        except json.JSONDecodeError:
            return 400, {"success": False, "message": "Invalid JSON data", "error_code": "INVALID_JSON"}
        except ValueError as e:
            return 400, {"success": False, "message": str(e), "error_code": "VALIDATION_ERROR"}
        except UserAlreadyExistsError as e:
            return 409, {"success": False, "message": str(e), "error_code": "USER_ALREADY_EXISTS"}
    
    async def _get_user(self, user_id: str) -> tuple[int, Dict[str, Any]]:
        """Get user by ID."""
        try:
            user = await self.user_service.get_user(user_id)
            
            return 200, {
                "success": True,
                "data": user.__dict__
            }
        
        except UserNotFoundError as e:
            return 404, {"success": False, "message": str(e), "error_code": "USER_NOT_FOUND"}
    
    async def _update_user(self, user_id: str, body: str) -> tuple[int, Dict[str, Any]]:
        """Update user."""
        try:
            data = json.loads(body) if body else {}
            
            request = UpdateUserRequest(
                full_name=data.get("full_name"),
                profile_data=data.get("profile_data")
            )
            
            if not request.has_updates():
                return 400, {"success": False, "message": "No updates provided", "error_code": "NO_UPDATES"}
            
            user = await self.user_service.update_user(user_id, request)
            
            return 200, {
                "success": True,
                "message": "User updated successfully",
                "data": user.__dict__
            }
        
        except json.JSONDecodeError:
            return 400, {"success": False, "message": "Invalid JSON data", "error_code": "INVALID_JSON"}
        except ValueError as e:
            return 400, {"success": False, "message": str(e), "error_code": "VALIDATION_ERROR"}
        except UserNotFoundError as e:
            return 404, {"success": False, "message": str(e), "error_code": "USER_NOT_FOUND"}
    
    async def _delete_user(self, user_id: str) -> tuple[int, Dict[str, Any]]:
        """Delete user."""
        try:
            success = await self.user_service.delete_user(user_id)
            
            if success:
                return 200, {
                    "success": True,
                    "message": "User deleted successfully"
                }
            else:
                return 500, {"success": False, "message": "Failed to delete user", "error_code": "DELETE_FAILED"}
        
        except UserNotFoundError as e:
            return 404, {"success": False, "message": str(e), "error_code": "USER_NOT_FOUND"}
    
    async def _get_user_profile(self, user_id: str) -> tuple[int, Dict[str, Any]]:
        """Get user profile."""
        try:
            profile = await self.profile_service.get_profile(user_id)
            
            return 200, {
                "success": True,
                "data": profile.__dict__
            }
        
        except ProfileNotFoundError as e:
            return 404, {"success": False, "message": str(e), "error_code": "PROFILE_NOT_FOUND"}
    
    async def _create_user_profile(self, user_id: str, body: str) -> tuple[int, Dict[str, Any]]:
        """Create user profile."""
        try:
            data = json.loads(body) if body else {}
            
            request = CreateUserProfileRequest(
                bio=data.get("bio", ""),
                avatar_url=data.get("avatar_url", ""),
                location=data.get("location", ""),
                website=data.get("website", ""),
                social_links=data.get("social_links", {}),
                preferences=data.get("preferences", {})
            )
            
            profile = await self.profile_service.create_profile(user_id, request)
            
            return 201, {
                "success": True,
                "message": "Profile created successfully",
                "data": profile.__dict__
            }
        
        except json.JSONDecodeError:
            return 400, {"success": False, "message": "Invalid JSON data", "error_code": "INVALID_JSON"}
        except ValueError as e:
            return 400, {"success": False, "message": str(e), "error_code": "VALIDATION_ERROR"}
        except UserNotFoundError as e:
            return 404, {"success": False, "message": str(e), "error_code": "USER_NOT_FOUND"}
        except ProfileAlreadyExistsError as e:
            return 409, {"success": False, "message": str(e), "error_code": "PROFILE_ALREADY_EXISTS"}
    
    async def _update_user_profile(self, user_id: str, body: str) -> tuple[int, Dict[str, Any]]:
        """Update user profile."""
        try:
            data = json.loads(body) if body else {}
            
            request = UpdateUserProfileRequest(
                bio=data.get("bio"),
                avatar_url=data.get("avatar_url"),
                location=data.get("location"),
                website=data.get("website"),
                social_links=data.get("social_links"),
                preferences=data.get("preferences")
            )
            
            if not request.has_updates():
                return 400, {"success": False, "message": "No updates provided", "error_code": "NO_UPDATES"}
            
            profile = await self.profile_service.update_profile(user_id, request)
            
            return 200, {
                "success": True,
                "message": "Profile updated successfully",
                "data": profile.__dict__
            }
        
        except json.JSONDecodeError:
            return 400, {"success": False, "message": "Invalid JSON data", "error_code": "INVALID_JSON"}
        except ValueError as e:
            return 400, {"success": False, "message": str(e), "error_code": "VALIDATION_ERROR"}
        except ProfileNotFoundError as e:
            return 404, {"success": False, "message": str(e), "error_code": "PROFILE_NOT_FOUND"}
    
    async def _delete_user_profile(self, user_id: str) -> tuple[int, Dict[str, Any]]:
        """Delete user profile."""
        try:
            success = await self.profile_service.delete_profile(user_id)
            
            if success:
                return 200, {
                    "success": True,
                    "message": "Profile deleted successfully"
                }
            else:
                return 500, {"success": False, "message": "Failed to delete profile", "error_code": "DELETE_FAILED"}
        
        except ProfileNotFoundError as e:
            return 404, {"success": False, "message": str(e), "error_code": "PROFILE_NOT_FOUND"}