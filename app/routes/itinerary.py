from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.services.geonames import validate_city
from app.services.countries import get_country_name

router = APIRouter(prefix="/itinerary", tags=["Itinerary Builder"])

@router.post("/trips/{trip_id}/stops")
def add_stop(trip_id: str, payload: dict, db=Depends(get_db)):
    geo = validate_city(payload["location"])
    if not geo:
        raise HTTPException(404, "City not found")

    country = get_country_name(geo["country_code"])

    # Get current max order
    res = db.table("stops") \
            .select("order") \
            .eq("trip_id", trip_id) \
            .order("order", desc=True) \
            .limit(1) \
            .execute()

    next_order = (res.data[0]["order"] + 1) if res.data else 1

    stop = {
        "trip_id": trip_id,
        "name": payload["name"],
        "location": geo["city"],
        "latitude": geo.get("lat"),
        "longitude": geo.get("lng"),
        "arrival_date": payload.get("arrival_date"),
        "departure_date": payload.get("departure_date"),
        "order": next_order,
        "notes": payload.get("notes")
    }

    db.table("stops").insert(stop).execute()

    return {"message": "Stop added successfully"}


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
