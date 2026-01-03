from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_supabase, get_supabase_admin
from app.schemas.user import UserCreate, UserResponse, TokenResponse, UserUpdate
from supabase import Client
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    supabase: Client = Depends(get_supabase),
    supabase_admin: Client = Depends(get_supabase_admin)
):
    """
    Register a new user using Supabase Auth.
    """
    try:
        # Sign up user with Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
        
        # Create/update user profile using admin client (bypasses RLS)
        user_profile_data = {
            "id": auth_response.user.id,
            "email": user_data.email,
            "full_name": user_data.full_name,
        }
        
        # Use upsert to create or update the profile
        profile_result = supabase_admin.table("users").upsert(user_profile_data).execute()
        
        # Fetch the created/updated profile
        user_profile = supabase_admin.table("users").select("*").eq("id", auth_response.user.id).single().execute()
        
        return TokenResponse(
            access_token=auth_response.session.access_token,
            user=UserResponse(**user_profile.data)
        )
        
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    email: str,
    password: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Login user with email and password.
    """
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Fetch user profile
        user_profile = supabase.table("users").select("*").eq("id", auth_response.user.id).single().execute()
        
        return TokenResponse(
            access_token=auth_response.session.access_token,
            user=UserResponse(**user_profile.data)
        )
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@router.post("/logout")
async def logout(supabase: Client = Depends(get_supabase)):
    """
    Logout current user.
    """
    try:
        supabase.auth.sign_out()
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logout failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Refresh access token using refresh token.
    """
    try:
        auth_response = supabase.auth.refresh_session(refresh_token)
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_profile = supabase.table("users").select("*").eq("id", auth_response.user.id).single().execute()
        
        return TokenResponse(
            access_token=auth_response.session.access_token,
            user=UserResponse(**user_profile.data)
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
