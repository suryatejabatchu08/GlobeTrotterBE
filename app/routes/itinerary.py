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


@router.get("/activities")
def search_activities(
    city: str,
    category: str | None = None,
    max_cost: int | None = None
):
    headers = {
        "Authorization": f"Bearer {settings.FSQ_SERVICE_KEY}",
        "X-Places-Api-Version": settings.FSQ_API_VERSION
    }

    params = {
        "near": city,
        "categories": "16000",
        "limit": 15
    }

    res = requests.get(
        f"{settings.FSQ_BASE_URL}/places/search",
        headers=headers,
        params=params
    ).json()

    activities = []

    for place in res.get("results", []):
        cat = place["categories"][0]["name"]
        est_cost = estimate_cost(cat)

        if category and category.lower() not in cat.lower():
            continue
        if max_cost and est_cost > max_cost:
            continue

        activities.append({
            "fsq_place_id": place["fsq_place_id"],
            "name": place["name"],
            "category": cat,
            "estimated_cost": est_cost,
            "latitude": place["latitude"],
            "longitude": place["longitude"]
        })

    return activities


def estimate_cost(category: str) -> int:
    if "Museum" in category:
        return 300
    if "Outdoor" in category:
        return 0
    if "Food" in category:
        return 800
    return 500

from fastapi import APIRouter, Query
import requests
from app.core.config import settings

router = APIRouter(prefix="/search", tags=["Search Services"])

@router.get("/cities")
def search_cities(q: str, region: str | None = None):
    response = requests.get(
        "http://api.geonames.org/searchJSON",
        params={
            "q": q,
            "maxRows": 10,
            "username": "aadarshsenapati"
        },
        timeout=10
    )

    geo_data = response.json()

    results = []

    for city in geo_data.get("geonames", []):
        country_code = city.get("countryCode")
        if not country_code:
            continue

        country_resp = requests.get(
            f"https://restcountries.com/v3.1/alpha/{country_code}",
            timeout=10
        ).json()

        country = country_resp[0]
        city_region = country.get("region")

        if region and city_region and city_region.lower() != region.lower():
            continue

        results.append({
            "city": city["name"],
            "country": country["name"]["common"],
            "region": city_region,
            "latitude": city["lat"],
            "longitude": city["lng"],
            "population": city.get("population")
        })

    return results



@router.get("/activities")
def search_activities(
    city: str,
    category: str | None = None,
    max_cost: int | None = None
):
    headers = {
        "Authorization": f"Bearer YYJC2TYHXJTVSF5SPC3HOUGJMTLRHHDSEPHIGDTLVCFJREZZ",
        "X-Places-Api-Version": "2025-06-17"
    }

    params = {
        "near": city,
        "categories": "16000",
        "limit": 15
    }

    res = requests.get(
        f"https://places-api.foursquare.com/places/search",
        headers=headers,
        params=params
    ).json()

    activities = []

    for place in res.get("results", []):
        cat = place["categories"][0]["name"]
        est_cost = estimate_cost(cat)

        if category and category.lower() not in cat.lower():
            continue
        if max_cost and est_cost > max_cost:
            continue

        activities.append({
            "fsq_place_id": place["fsq_place_id"],
            "name": place["name"],
            "category": cat,
            "estimated_cost": est_cost,
            "latitude": place["latitude"],
            "longitude": place["longitude"]
        })

    return activities


def estimate_cost(category: str) -> int:
    if "Museum" in category:
        return 300
    if "Outdoor" in category:
        return 0
    if "Food" in category:
        return 800
    return 500
