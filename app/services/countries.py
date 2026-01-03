import requests

def get_country_name(code: str):
    url = f"https://restcountries.com/v3.1/alpha/{code}"
    res = requests.get(url).json()
    return res[0]["name"]["common"]
