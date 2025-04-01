import pandas as pd
import os
import math
import joblib
import folium
import openrouteservice
from shapely.geometry import Point, MultiPoint, LineString
import csv

# === CONFIG ===
ORS_API_KEY = "5b3ce3597851110001cf6248cf5db78f03e641c3b7f4871bdfdd1bb3"
GPS_PATH = "data/gps_data.csv"
RESULTS_PATH = "data/validation_results.csv"
MAP_OUTPUT_PATH = "visuals/offroad_map_{}.html"
THRESHOLD_METERS = 30

# === UTILITY FUNCTIONS ===
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def convex_hull_area_km2(lats, lons):
    if len(lats) < 3:
        return 0.0
    points = [Point(lon, lat) for lat, lon in zip(lats, lons)]
    hull = MultiPoint(points).convex_hull
    if hull.is_empty:
        return 0.0
    coords = list(hull.exterior.coords)
    lat0, lon0 = coords[0][1], coords[0][0]
    area = 0
    for i in range(len(coords) - 1):
        x1 = (coords[i][0] - lon0) * 111320
        y1 = (coords[i][1] - lat0) * 111320
        x2 = (coords[i + 1][0] - lon0) * 111320
        y2 = (coords[i + 1][1] - lat0) * 111320
        area += x1 * y2 - x2 * y1
    return abs(area / 2) / 1e6  # m² to km²

# === MAIN FUNCTION ===
def detect_anomalies(mission_id=None):
    df = pd.read_csv(GPS_PATH)
    if "mission_id" not in df.columns:
        print("❌ 'mission_id' column not found in GPS data.")
        return

    if mission_id is None:
        mission_id = df["mission_id"].iloc[-1]

    df = df[df["mission_id"] == mission_id]
    if df.empty:
        print(f"❌ No data for mission {mission_id}")
        return

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    lats = df["latitude"].tolist()
    lons = df["longitude"].tolist()
    times = df["timestamp"].tolist()

    distance_km = sum(haversine(lats[i-1], lons[i-1], lats[i], lons[i]) for i in range(1, len(lats))) / 1000
    duration_min = (times[-1] - times[0]).total_seconds() / 60
    area_km2 = convex_hull_area_km2(lats, lons)
    avg_speed_kmh = distance_km / (duration_min / 60) if duration_min > 0 else 0
    num_points = len(df)

    # === AI Verification ===
    try:
        model = joblib.load("models/anomaly_model.pkl")
        X = pd.DataFrame([[distance_km, duration_min, avg_speed_kmh, area_km2, num_points]],
                         columns=["distance_km", "duration_min", "avg_speed_kmh", "area_km2", "num_points"])
        ml_pred = int(model.predict(X)[0])
    except Exception as e:
        print(f"[WARN] Model prediction failed: {e}")
        ml_pred = 0

    # === Rule-Based Checks ===
    anomalies = []
    if distance_km < 1:
        anomalies.append("Distance too short")
    if duration_min < 5:
        anomalies.append("Duration too short")
    if area_km2 < 0.01:
        anomalies.append("Area too small")

    # === Road Compliance Check ===
    offroad_count = 0
    try:
        client = openrouteservice.Client(key=ORS_API_KEY)
        route = client.directions([(lons[0], lats[0]), (lons[-1], lats[-1])], profile='cycling-regular', format='geojson')
        route_coords = route["features"][0]["geometry"]["coordinates"]
        route_line = LineString(route_coords)

        for lat, lon in zip(lats, lons):
            point = Point(lon, lat)
            if route_line.distance(point) * 100000 > THRESHOLD_METERS:
                offroad_count += 1

        if offroad_count > 0:
            anomalies.append("Off-road movement detected")

    except Exception as e:
        print(f"[WARN] ORS error: {e}")

    # === Generate Map ===
    os.makedirs("visuals", exist_ok=True)
    m = folium.Map(location=[lats[0], lons[0]], zoom_start=15)

    folium.PolyLine(list(zip(lats, lons)), color='green', weight=4, tooltip="Mission Path").add_to(m)

    # Add ORS route if available
    if 'route_coords' in locals():
        folium.PolyLine([(lat, lon) for lon, lat in route_coords], color='blue', weight=3, tooltip="ORS Route").add_to(m)

    # Add Start and End Markers
    folium.Marker(
        location=(lats[0], lons[0]),
        popup="Start",
        tooltip="Start",
        icon=folium.Icon(color="green", icon="play")
    ).add_to(m)

    folium.Marker(
        location=(lats[-1], lons[-1]),
        popup="End",
        tooltip="End",
        icon=folium.Icon(color="red", icon="stop")
    ).add_to(m)

    m.save(MAP_OUTPUT_PATH.format(mission_id))

    # === Save Results to CSV ===
    os.makedirs("data", exist_ok=True)
    write_header = not os.path.exists(RESULTS_PATH)
    with open(RESULTS_PATH, "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        if write_header:
            writer.writerow([
                "mission_id", "distance_km", "duration_min", "area_km2", "avg_speed_kmh",
                "num_points", "offroad_points", "ml_pred", "anomalies", "status"
            ])
        anomaly_str = "; ".join(anomalies) if anomalies else "None"
        status = "Anomalies Detected" if ml_pred == 1 or anomalies else "Valid"
        writer.writerow([
            mission_id,
            round(distance_km, 2),
            round(duration_min, 2),
            round(area_km2, 4),
            round(avg_speed_kmh, 2),
            num_points,
            offroad_count,
            ml_pred,
            anomaly_str,
            status
        ])

    # === Console Summary ===
    print("\n📊 Summary:")
    print(f"  Mission ID        : {mission_id}")
    print(f"  Distance (km)     : {distance_km:.2f}")
    print(f"  Duration (min)    : {duration_min:.2f}")
    print(f"  Area (km²)        : {area_km2:.4f}")
    print(f"  Avg speed (km/h)  : {avg_speed_kmh:.2f}")
    print(f"  Points recorded   : {num_points}")
    print(f"  Off-road points   : {offroad_count}")
    print(f"  ML Prediction     : {'Anomaly' if ml_pred == 1 else 'Valid'}")
    print(f"  Rule-based issues : {anomalies if anomalies else 'None'}")
    print(f"🚩 Final Status     : {status}")
    print(f"🗺  Map saved to     : visuals/offroad_map_{mission_id}.html")

# === Entry Point ===
if __name__ == "__main__":
    detect_anomalies()
