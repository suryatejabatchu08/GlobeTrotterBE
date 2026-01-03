import requests
from app.core.config import FSQ_SERVICE_KEY, FSQ_API_VERSION, FSQ_BASE_URL

def get_activities(city: str):
    headers = {
        "Authorization": f"Bearer {FSQ_SERVICE_KEY}",
        "X-Places-Api-Version": FSQ_API_VERSION,
        "Accept": "application/json"
    }
    params = {
        "near": city,
        "categories": "16000",
        "limit": 10
    }
    res = requests.get(
        f"{FSQ_BASE_URL}/places/search",
        headers=headers,
        params=params
    ).json()

    return res["results"]
