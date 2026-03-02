"""Pydantic schemas for Auth operations.

This module provides request and response schemas for authentication
endpoints including registration, login, and token management.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.auth.validators import (
    validate_email_format,
    validate_password_strength,
    validate_username,
)


class UserRegisterRequest(BaseModel):
    """Schema for user registration request."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username (3-50 chars, alphanumeric and underscore only)",
    )
    email: str = Field(..., description="Valid email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (8-128 chars with complexity requirements)",
    )

    @field_validator("username")
    @classmethod
    def validate_username_format(cls, v: str) -> str:
        """Validate username format."""
        is_valid, error_msg = validate_username(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        is_valid, error_msg = validate_email_format(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        is_valid, missing = validate_password_strength(v)
        if not is_valid:
            raise ValueError(f"Password must contain: {', '.join(missing)}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "SecureP@ss123",
            }
        }
    )


class UserLoginRequest(BaseModel):
    """Schema for user login request."""

    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")

    model_config = ConfigDict(
        json_schema_extra={"example": {"username": "johndoe", "password": "SecureP@ss123"}}
    )


class ChangePasswordRequest(BaseModel):
    """Schema for password change request."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (8-128 chars with complexity requirements)",
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password_complexity(cls, v: str) -> str:
        """Validate new password meets complexity requirements."""
        is_valid, missing = validate_password_strength(v)
        if not is_valid:
            raise ValueError(f"Password must contain: {', '.join(missing)}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "OldP@ss123",
                "new_password": "NewSecureP@ss456",
            }
        }
    )


class UpdateProfileRequest(BaseModel):
    """Schema for profile update request."""

    email: Optional[str] = Field(None, description="New email address")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format when provided."""
        if v is None:
            return v
        is_valid, error_msg = validate_email_format(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.lower()

    model_config = ConfigDict(json_schema_extra={"example": {"email": "newemail@example.com"}})


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh request (cookie-based)."""

    # This schema is primarily for documentation purposes
    # The actual refresh token will come from an HTTP-only cookie
    pass


class UserResponse(BaseModel):
    """Schema for user data in responses."""

    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    created_at: datetime = Field(..., description="Account creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    """Schema for login response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: UserResponse = Field(..., description="User data")
    requires_password_change: Optional[bool] = Field(
        None, description="Whether user must change password"
    )

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema for token-only response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Schema for simple message response."""

    message: str = Field(..., description="Response message")

    model_config = ConfigDict(
        json_schema_extra={"example": {"message": "Operation completed successfully"}}
    )


class ErrorResponse(BaseModel):
    """Schema for error response."""

    detail: str = Field(..., description="Error detail message")
    error_code: Optional[str] = Field(None, description="Error code for client handling")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"detail": "Invalid credentials", "error_code": "AUTH_INVALID"}
        }
    )


class PasswordValidationResponse(BaseModel):
    """Schema for password validation result."""

    is_valid: bool = Field(..., description="Whether password is valid")
    missing_requirements: list[str] = Field(
        default_factory=list, description="List of missing requirements"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_valid": False,
                "missing_requirements": ["uppercase letter", "special character"],
            }
        }
    )
