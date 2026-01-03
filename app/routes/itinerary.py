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


from datetime import datetime

def calculate_days(start_date, end_date):
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    return (end - start).days + 1


import requests

def fetch_attractions(city: str, limit: int = 20):
    headers = {
        'Authorization': 'Bearer YYJC2TYHXJTVSF5SPC3HOUGJMTLRHHDSEPHIGDTLVCFJREZZ',
        'X-Places-Api-Version': '2025-06-17',
        'Accept': 'application/json'
    }

    params = {
        "near": city,
        "categories": "16000",  # attractions
        "limit": limit
    }

    response = requests.get(
        f"https://places-api.foursquare.com/places/search",
        headers=headers,
        params=params,
        timeout=10
    )

    return response.json().get("results", [])



from datetime import timedelta

def generate_day_wise_itinerary(city, start_date, end_date):
    days = calculate_days(start_date, end_date)
    attractions = fetch_attractions(city, limit=days * 5)

    itinerary = []
    start = datetime.fromisoformat(start_date)

    per_day = max(len(attractions) // days, 1)

    for day in range(days):
        day_date = start + timedelta(days=day)

        day_activities = attractions[
            day * per_day : (day + 1) * per_day
        ]

        itinerary.append({
            "day": day + 1,
            "date": day_date.date().isoformat(),
            "city": city,
            "activities": [
                {
                    "fsq_place_id": a["fsq_place_id"],
                    "name": a["name"],
                    "category": a["categories"][0]["name"],
                    "latitude": a["latitude"],
                    "longitude": a["longitude"]
                }
                for a in day_activities
            ]
        })

    return itinerary


from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/itinerary", tags=["Auto Itinerary"])

class AutoPlanRequest(BaseModel):
    city: str
    start_date: str
    end_date: str

@router.post("/auto-plan")
def auto_plan_trip(payload: AutoPlanRequest):
    itinerary = generate_day_wise_itinerary(
        payload.city,
        payload.start_date,
        payload.end_date
    )

    return {
        "city": payload.city,
        "total_days": len(itinerary),
        "itinerary": itinerary
    }

from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.schemas.activity import ScheduleActivityCreate

router = APIRouter(prefix="/schedule", tags=["Schedule"])

@router.post("/activities")
def save_activity(
    payload: ScheduleActivityCreate,
    db = Depends(get_db)
):
    res = db.table("scheduled_activities").insert(payload.dict()).execute()

    return {
        "message": "Activity scheduled successfully",
        "data": res.data
    }



@router.get("/trips/{trip_id}")
def get_scheduled_activities(trip_id: str, db=Depends(get_db)):
    res = (
        db.table("scheduled_activities")
        .select("*")
        .eq("trip_id", trip_id)
        .order("day")
        .execute()
    )

    return res.data


from app.schemas.activity import ScheduleActivityUpdate

@router.patch("/activities/{activity_id}")
def update_activity(
    activity_id: str,
    payload: ScheduleActivityUpdate,
    db=Depends(get_db)
):
    res = (
        db.table("scheduled_activities")
        .update(payload.dict(exclude_unset=True))
        .eq("id", activity_id)
        .execute()
    )

    return {
        "message": "Activity updated successfully",
        "data": res.data
    }



@router.delete("/activities/{activity_id}")
def delete_activity(activity_id: str, db=Depends(get_db)):
    db.table("scheduled_activities").delete().eq("id", activity_id).execute()
    return {"message": "Activity removed"}
