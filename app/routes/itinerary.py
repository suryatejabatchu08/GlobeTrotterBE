from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_supabase, get_supabase_admin
from app.core.security import get_current_user
from supabase import Client
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/itinerary", tags=["Itinerary Builder"])


@router.post("/trips/{trip_id}/stops", status_code=status.HTTP_201_CREATED)
async def add_stop(
    trip_id: str, 
    payload: dict, 
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    supabase_admin: Client = Depends(get_supabase_admin)
):
    """Add a new stop to a trip"""
    try:
        # Verify trip ownership
        trip = supabase.table("trips").select("id").eq("id", trip_id).eq("user_id", current_user.id).single().execute()
        if not trip.data:
            raise HTTPException(status_code=404, detail="Trip not found")

        # Get current max order
        res = supabase.table("stops") \
                .select("order") \
                .eq("trip_id", trip_id) \
                .order("order", desc=True) \
                .limit(1) \
                .execute()

        next_order = (res.data[0]["order"] + 1) if res.data else 0

        stop = {
            "trip_id": trip_id,
            "destination_id": payload.get("destination_id"),  # Optional link to destinations catalog
            "name": payload["name"],
            "location": payload.get("location", payload["name"]),
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude"),
            "arrival_date": payload.get("arrival_date"),
            "departure_date": payload.get("departure_date"),
            "order": payload.get("order", next_order),
            "notes": payload.get("notes"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Use admin client to bypass RLS (we already verified authorization above)
        result = supabase_admin.table("stops").insert(stop).execute()
        return {"message": "Stop added successfully", "stop": result.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stops/{stop_id}/activities", status_code=status.HTTP_201_CREATED)
async def add_activity(
    stop_id: str, 
    payload: dict, 
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    supabase_admin: Client = Depends(get_supabase_admin)
):
    """Add an activity to a stop"""
    try:
        # Verify stop exists and user owns the trip
        stop = supabase.table("stops") \
            .select("*, trips!inner(user_id)") \
            .eq("id", stop_id) \
            .single() \
            .execute()
        
        if not stop.data:
            raise HTTPException(status_code=404, detail="Stop not found")
        
        if stop.data["trips"]["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Get current max order for activities in this stop
        res = supabase.table("activities") \
                .select("order") \
                .eq("stop_id", stop_id) \
                .order("order", desc=True) \
                .limit(1) \
                .execute()

        next_order = (res.data[0]["order"] + 1) if res.data else 0

        activity = {
            "stop_id": stop_id,
            "catalog_activity_id": payload.get("catalog_activity_id"),  # Optional link to activity catalog
            "fsq_place_id": payload.get("fsq_place_id"),  # Foursquare place ID
            "name": payload["name"],
            "activity_type": payload.get("category", "other"),  # Map category to activity_type
            "description": payload.get("description"),
            "cost": payload.get("estimated_cost", 0),
            "duration_minutes": payload.get("duration_minutes"),  # Optional duration
            "currency": payload.get("currency", "USD"),
            "order": payload.get("order_index", next_order),  # Map order_index to order
            "scheduled_date": payload.get("scheduled_date"),
            "scheduled_time": payload.get("scheduled_time"),
            "location": payload.get("location"),
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Use admin client to bypass RLS (we already verified authorization above)
        result = supabase_admin.table("activities").insert(activity).execute()
        return {
            "message": "Activity added successfully",
            "activity": result.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trips/{trip_id}/stops")
async def get_trip_stops(
    trip_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Get all stops for a trip"""
    try:
        # Verify trip ownership
        trip = supabase.table("trips").select("id").eq("id", trip_id).eq("user_id", current_user.id).single().execute()
        if not trip.data:
            raise HTTPException(status_code=404, detail="Trip not found")

        stops = supabase.table("stops") \
            .select("*") \
            .eq("trip_id", trip_id) \
            .order("order") \
            .execute()

        return {"stops": stops.data}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stops/{stop_id}/activities")
async def get_stop_activities(
    stop_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Get all activities for a stop"""
    try:
        # Verify stop exists and user owns the trip
        stop = supabase.table("stops") \
            .select("*, trips!inner(user_id)") \
            .eq("id", stop_id) \
            .single() \
            .execute()
        
        if not stop.data:
            raise HTTPException(status_code=404, detail="Stop not found")
        
        if stop.data["trips"]["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        activities = supabase.table("activities") \
            .select("*") \
            .eq("stop_id", stop_id) \
            .order("order") \
            .execute()

        return {"activities": activities.data}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
