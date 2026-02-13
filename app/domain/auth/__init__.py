"""Auth domain module.

This module provides authentication and authorization functionality
including user management, token handling, and password validation.
"""

from app.domain.auth.models import RefreshToken as RefreshTokenModel
from app.domain.auth.models import User as UserModel
from app.domain.auth.schemas import (
    ChangePasswordRequest,
    ErrorResponse,
    LoginResponse,
    MessageResponse,
    PasswordValidationResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.domain.auth.service import (
    AuthService,
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
    verify_token,
)
from app.domain.auth.validators import (
    validate_email_format,
    validate_password_strength,
    validate_username,
)

__all__ = [
    # Models
    "UserModel",
    "RefreshTokenModel",
    # Schemas
    "UserRegisterRequest",
    "UserLoginRequest",
    "ChangePasswordRequest",
    "TokenRefreshRequest",
    "UserResponse",
    "LoginResponse",
    "TokenResponse",
    "MessageResponse",
    "ErrorResponse",
    "PasswordValidationResponse",
    # Service
    "AuthService",
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "hash_token",
    # Validators
    "validate_password_strength",
    "validate_username",
    "validate_email_format",
]
