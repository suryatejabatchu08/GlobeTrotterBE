import requests
from app.core.config import GEONAMES_USERNAME

def validate_city(city: str):
    url = "http://api.geonames.org/searchJSON"
    params = {
        "q": city,
        "maxRows": 1,
        "username": GEONAMES_USERNAME
    }
    res = requests.get(url, params=params).json()

    if not res["geonames"]:
        return None

    g = res["geonames"][0]
    return {
        "city": g["name"],
        "country_code": g["countryCode"]
    }
