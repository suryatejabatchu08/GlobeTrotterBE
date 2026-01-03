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


@router.post("/api/v1/itinerary/stops/{stop_id}/activities")
def add_activity(stop_id: str, payload: dict, db=Depends(get_db)):
    """
    payload comes from Swagger / frontend
    """

    response = db.table("activities").insert({
        "stop_id": stop_id,
        "fsq_place_id": payload["fsq_place_id"],
        "name": payload["name"],
        "category": payload.get("category"),
        "estimated_cost": payload.get("estimated_cost", 0),
        "order_index": payload.get("order_index", 0)
    }).execute()

    return {
        "message": "Activity added successfully",
        "activity": response.data
    }
