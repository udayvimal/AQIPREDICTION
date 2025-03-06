import requests
import json
API_KEY = "76c809311920792810bc99cbd8c796dd030c216175c5c2e961f8d7e467742433"
BASE_URL = "https://api.openaq.org/v3/sensors"


headers = {"X-API-Key": API_KEY, "accept": "application/json"}

params = {
    "country": "IN",  # Change to "US" or another country if needed
    "limit": 10
}

response = requests.get(BASE_URL, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=4))
else:
    print(f"❌ Error: {response.status_code}, Message: {response.text}")