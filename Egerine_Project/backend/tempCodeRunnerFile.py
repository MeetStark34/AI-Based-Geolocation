import openrouteservice
import time
from datetime import datetime, timedelta
import requests

# ========== CONFIG ==========
ORS_API_KEY = "5b3ce3597851110001cf6248cf5db78f03e641c3b7f4871bdfdd1bb3"
API_URL = "http://127.0.0.1:5000/api/track"  # Your Flask endpoint
MISSION_ID = "mission_road_101"
SEND_TO_API = True  # Set to False to just print

# Start and end coordinates (longitude, latitude) in Paris
start = (2.3518, 48.8566)  # near Hôtel de Ville
end = (2.3600, 48.8600)    # near Place de la République

# ========== INIT ==========
client = openrouteservice.Client(key=ORS_API_KEY)
routes = client.directions(
    coordinates=[start, end],
    profile='cycling-regular',
    format='geojson'
)

coords = routes['features'][0]['geometry']['coordinates']
print(f"📍 Route contains {len(coords)} points")

# ========== SIMULATE GPS TRACKING ==========
current_time = datetime.now()

for i, (lon, lat) in enumerate(coords):
    timestamp = current_time + timedelta(seconds=i * 10)

    gps_data = {
        "latitude": lat,
        "longitude": lon,
        "timestamp": timestamp.isoformat(),
        "mission_id": MISSION_ID
    }

    if SEND_TO_API:
        try:
            response = requests.post(API_URL, json=gps_data)
            print(f"[{i+1}] Sent: {gps_data} → Status: {response.status_code}")
        except Exception as e:
            print("Error sending:", e)
    else:
        print(f"[{i+1}] {gps_data}")

    time.sleep(0.5)

print("\n✅ Smart route simulation complete.")
