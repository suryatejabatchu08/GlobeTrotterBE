from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_supabase
from app.core.security import get_current_user, get_current_user_optional
from app.schemas.trip import TripCreate, TripUpdate, TripResponse, TripListResponse, ShareTripResponse
from supabase import Client
from typing import List, Optional
import logging
import secrets
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trips", tags=["Trips"])


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    trip_data: TripCreate,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Create a new trip for the authenticated user.
    """
    try:
        trip_dict = trip_data.model_dump()
        trip_dict["user_id"] = current_user.id
        trip_dict["created_at"] = datetime.utcnow().isoformat()
        trip_dict["updated_at"] = datetime.utcnow().isoformat()
        
        result = supabase.table("trips").insert(trip_dict).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create trip"
            )
        
        return TripResponse(**result.data[0])
        
    except Exception as e:
        logger.error(f"Create trip error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=TripListResponse)
async def get_my_trips(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all trips for the authenticated user.
    """
    try:
        # Get trips with pagination
        result = supabase.table("trips")\
            .select("*")\
            .eq("user_id", current_user.id)\
            .order("created_at", desc=True)\
            .range(skip, skip + limit - 1)\
            .execute()
        
        # Get total count
        count_result = supabase.table("trips")\
            .select("id", count="exact")\
            .eq("user_id", current_user.id)\
            .execute()
        
        trips = [TripResponse(**trip) for trip in result.data]
        total = count_result.count if hasattr(count_result, 'count') else len(trips)
        
        return TripListResponse(trips=trips, total=total)
        
    except Exception as e:
        logger.error(f"Get trips error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get a specific trip by ID. User must own the trip.
    """
    try:
        result = supabase.table("trips")\
            .select("*")\
            .eq("id", trip_id)\
            .eq("user_id", current_user.id)\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        return TripResponse(**result.data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get trip error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: str,
    trip_data: TripUpdate,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Update a trip. User must own the trip.
    """
    try:
        # Verify ownership
        existing = supabase.table("trips")\
            .select("id")\
            .eq("id", trip_id)\
            .eq("user_id", current_user.id)\
            .single()\
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        # Update trip
        update_dict = trip_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.utcnow().isoformat()
        
        result = supabase.table("trips")\
            .update(update_dict)\
            .eq("id", trip_id)\
            .execute()
        
        return TripResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update trip error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(
    trip_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Delete a trip. User must own the trip.
    """
    try:
        # Verify ownership and delete
        result = supabase.table("trips")\
            .delete()\
            .eq("id", trip_id)\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete trip error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{trip_id}/share", response_model=ShareTripResponse)
async def share_trip(
    trip_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Generate a public share link for a trip.
    """
    try:
        # Verify ownership
        trip = supabase.table("trips")\
            .select("*")\
            .eq("id", trip_id)\
            .eq("user_id", current_user.id)\
            .single()\
            .execute()
        
        if not trip.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        # Generate share token if not exists
        share_token = trip.data.get("share_token")
        if not share_token:
            share_token = secrets.token_urlsafe(32)
            supabase.table("trips").update({
                "share_token": share_token,
                "is_public": True,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", trip_id).execute()
        
        # In production, use your actual domain
        share_url = f"http://localhost:3000/shared/{share_token}"
        
        return ShareTripResponse(
            share_url=share_url,
            share_token=share_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Share trip error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/shared/{share_token}", response_model=TripResponse)
async def get_shared_trip(
    share_token: str,
    supabase: Client = Depends(get_supabase),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Get a trip by its public share token. No authentication required.
    """
    try:
        result = supabase.table("trips")\
            .select("*")\
            .eq("share_token", share_token)\
            .eq("is_public", True)\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared trip not found"
            )
        
        return TripResponse(**result.data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get shared trip error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{trip_id}/share", status_code=status.HTTP_204_NO_CONTENT)
async def unshare_trip(
    trip_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Remove public sharing from a trip.
    """
    try:
        result = supabase.table("trips").update({
            "is_public": False,
            "share_token": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", trip_id).eq("user_id", current_user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unshare trip error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
