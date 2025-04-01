import openrouteservice
import time
from datetime import datetime, timedelta
import requests

# ========== CONFIG ========== #
ORS_API_KEY = "5b3ce3597851110001cf6248cf5db78f03e641c3b7f4871bdfdd1bb3"
API_URL = "http://127.0.0.1:5000/api/track"  # Your Flask endpoint
SEND_TO_API = True  # Set to False to just print
SLEEP_BETWEEN_POINTS = 0.3  # Seconds between each GPS point

# Define multiple missions with (start, end) in Paris
MISSIONS = [
    {
        "id": "mission_road_3",
        "start": (2.3333, 48.8600),  # Louvre
        "end": (2.3490, 48.8700),    # Strasbourg Saint-Denis
    }
]

# ========== INIT ORS CLIENT ========== #
client = openrouteservice.Client(key=ORS_API_KEY)


# ========== FUNCTION TO SIMULATE ROUTE ========== #
def simulate_mission(mission_id, start, end):
    print(f"\n🛰️ Simulating route for: {mission_id}")
    try:
        routes = client.directions(
            coordinates=[start, end],
            profile='cycling-regular',
            format='geojson'
        )
        coords = routes['features'][0]['geometry']['coordinates']
        print(f"📍 Route contains {len(coords)} points")
    except Exception as e:
        print(f"❌ Error getting route for {mission_id}: {e}")
        return

    current_time = datetime.now()
    for i, (lon, lat) in enumerate(coords):
        timestamp = current_time + timedelta(seconds=i * 10)
        gps_data = {
            "latitude": lat,
            "longitude": lon,
            "timestamp": timestamp.isoformat(),
            "mission_id": mission_id
        }

        if SEND_TO_API:
            try:
                response = requests.post(API_URL, json=gps_data)
                print(f"[{i+1}] Sent: {gps_data} → Status: {response.status_code}")
            except Exception as e:
                print("Error sending:", e)
        else:
            print(f"[{i+1}] {gps_data}")

        time.sleep(SLEEP_BETWEEN_POINTS)

    print(f"✅ Completed simulation for: {mission_id}")


# ========== RUN ALL MISSIONS ========== #
for mission in MISSIONS:
    simulate_mission(mission["id"], mission["start"], mission["end"])

print("\n🎯 All missions simulated successfully.")
