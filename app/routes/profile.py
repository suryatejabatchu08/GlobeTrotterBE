from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_supabase, get_supabase_admin
from app.core.security import get_current_user
from app.schemas.user import UserResponse, UserUpdate
from supabase import Client
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["User Profile"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get current user's profile.
    """
    try:
        result = supabase.table("users")\
            .select("*")\
            .eq("id", current_user.id)\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return UserResponse(**result.data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    profile_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Update current user's profile.
    """
    try:
        update_dict = profile_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.utcnow().isoformat()
        
        result = supabase.table("users")\
            .update(update_dict)\
            .eq("id", current_user.id)\
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return UserResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    current_user: dict = Depends(get_current_user),
    supabase_admin: Client = Depends(get_supabase_admin)
):
    """
    Delete current user's account and all associated data.
    This will cascade delete all trips, stops, and activities.
    """
    try:
        # Delete user from auth (requires admin client)
        supabase_admin.auth.admin.delete_user(current_user.id)
        
        # The database triggers will handle cascading deletes
        # of user profile and all related data
        
        return None
        
    except Exception as e:
        logger.error(f"Delete account error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete account"
        )
