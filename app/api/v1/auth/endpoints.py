"""Auth API endpoints for authentication operations.

This module provides REST API endpoints for user authentication including
registration, login, token refresh, logout, and password management.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.domain.auth.models import User
from app.domain.auth.schemas import (
    ChangePasswordRequest,
    LoginResponse,
    MessageResponse,
    TokenResponse,
    UpdateProfileRequest,
    UserLoginRequest,
    UserResponse,
)
from app.domain.auth.service import AuthService, hash_token
from app.infrastructure.security.jwt import get_jwt_handler
from app.infrastructure.security.rate_limiter import RATE_LIMITS, rate_limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


def get_client_ip(request: Request) -> str:
    """Get client IP address for rate limiting.

    Checks X-Forwarded-For header first for reverse proxy scenarios,
    then falls back to direct client host.

    Args:
        request: The FastAPI request object.

    Returns:
        The client IP address as a string.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate user from JWT token.

    Dependency for protecting endpoints that require authentication.

    Args:
        credentials: The HTTP Bearer credentials from the request.
        db: The database session.

    Returns:
        The authenticated User object.

    Raises:
        HTTPException: 401 if token is invalid or user not found.
    """
    token = credentials.credentials
    jwt_handler = get_jwt_handler()

    user_id = jwt_handler.verify_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user



@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate user",
    description="Authenticate with username/email and password to receive tokens.",
)
async def login(
    request: Request,
    response: Response,
    data: UserLoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Authenticate user and return tokens.

    Validates credentials and issues access and refresh tokens. The refresh
    token is set as an HTTP-only cookie for security.

    Args:
        request: The FastAPI request object.
        response: The FastAPI response object for setting cookies.
        data: The login request data.
        db: The database session.

    Returns:
        LoginResponse with access token and user information.

    Raises:
        HTTPException: 429 if rate limited, 401 if credentials invalid.
    """
    # Rate limiting
    client_ip = get_client_ip(request)
    allowed, remaining, retry_after = rate_limiter.is_allowed(
        f"login:{client_ip}",
        RATE_LIMITS["login"]["max_requests"],
        RATE_LIMITS["login"]["window_seconds"],
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    auth_service = AuthService(db)
    jwt_handler = get_jwt_handler()

    # Authenticate user
    user = auth_service.authenticate_user(data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Generate tokens
    access_token = jwt_handler.create_access_token(user.id)
    refresh_token = jwt_handler.create_refresh_token(user.id)

    # Store refresh token in database
    expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    auth_service.store_refresh_token(user.id, refresh_token, expires_at)

    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )

    # Update last login
    auth_service.update_last_login(user)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        requires_password_change=user.requires_password_change,
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
        ),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get a new access token using the refresh token from cookie.",
)
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Refresh access token using refresh token from cookie.

    Validates the refresh token from the HTTP-only cookie and issues
    a new access token if valid.

    Args:
        request: The FastAPI request object.
        response: The FastAPI response object.
        db: The database session.

    Returns:
        TokenResponse with new access token.

    Raises:
        HTTPException: 429 if rate limited, 401 if token invalid/revoked.
    """
    # Rate limiting
    client_ip = get_client_ip(request)
    allowed, remaining, retry_after = rate_limiter.is_allowed(
        f"refresh:{client_ip}",
        RATE_LIMITS["refresh"]["max_requests"],
        RATE_LIMITS["refresh"]["window_seconds"],
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many refresh attempts. Retry after {retry_after} seconds.",
        )

    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    jwt_handler = get_jwt_handler()
    auth_service = AuthService(db)

    # Verify refresh token
    user_id = jwt_handler.verify_refresh_token(refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check if token is in database and not revoked
    token_hash = hash_token(refresh_token)
    stored_token = auth_service.get_valid_refresh_token(token_hash)
    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked or expired",
        )

    # Generate new access token
    access_token = jwt_handler.create_access_token(user_id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Invalidate refresh token and clear authentication cookie.",
)
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Logout user and invalidate refresh token.

    Revokes the refresh token in the database and clears the cookie.

    Args:
        request: The FastAPI request object.
        response: The FastAPI response object for clearing cookies.
        db: The database session.

    Returns:
        MessageResponse confirming logout.
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        auth_service = AuthService(db)
        # Revoke the refresh token
        token_hash = hash_token(refresh_token)
        auth_service.revoke_refresh_token(token_hash)

    # Clear the cookie (attributes must match set_cookie for browser to delete it)
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
    )

    return MessageResponse(message="Successfully logged out")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's information.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current authenticated user.

    Returns the profile information for the authenticated user.

    Args:
        current_user: The authenticated user from the JWT token.

    Returns:
        UserResponse with the user's information.
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        avatar_url=current_user.avatar_url,
        created_at=current_user.created_at,
    )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change the current user's password. Required for first-time admin login.",
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Change user password.

    Allows authenticated users to change their password. Required for
    first-time admin login when requires_password_change is True.

    Args:
        data: The password change request data.
        current_user: The authenticated user from the JWT token.
        db: The database session.

    Returns:
        MessageResponse confirming password change.

    Raises:
        HTTPException: 400 if current password is incorrect.
    """
    auth_service = AuthService(db)

    # Change password (verifies current password internally)
    success = auth_service.change_password(
        current_user, data.current_password, data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    return MessageResponse(message="Password changed successfully")


@router.put(
    "/profile",
    response_model=UserResponse,
    summary="Update user profile",
    description="Update the current user's profile information (e.g. email).",
)
async def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Update the authenticated user's profile.

    Args:
        data: The profile update data.
        current_user: The authenticated user from the JWT token.
        db: The database session.

    Returns:
        UserResponse with the updated user information.

    Raises:
        HTTPException: 409 if email is already taken.
    """
    auth_service = AuthService(db)

    if data.email is not None:
        try:
            current_user = auth_service.update_email(current_user, data.email)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )

    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        avatar_url=current_user.avatar_url,
        created_at=current_user.created_at,
    )
