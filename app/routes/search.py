from fastapi import APIRouter, Query
import requests
from app.core.config import settings

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/cities")
def search_cities(q: str, region: str | None = None):
    """Search for cities using GeoNames API with optional region filtering"""
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
