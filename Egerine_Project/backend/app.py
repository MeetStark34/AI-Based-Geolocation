"""Flask API to accept GPS data points (latitude/longitude) for missions in real-time."""
from flask import Flask, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# Path to the CSV file where we store incoming GPS points
GPS_DATA_FILE = os.path.join("data", "gps_data.csv")

# Ensure the data directory exists
os.makedirs("data", exist_ok=True)

# If GPS data file does not exist, create it and write header
if not os.path.exists(GPS_DATA_FILE):
    with open(GPS_DATA_FILE, "w") as f:
        f.write("mission_id,timestamp,latitude,longitude\n")

@app.route('/api/track', methods=['POST'])
def track():
    """API endpoint to receive a GPS data point. Expects JSON with 'mission_id', 'latitude', 'longitude', and optional 'timestamp'."""
    data = request.get_json(force=True)
    mission_id = data.get("mission_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    timestamp = data.get("timestamp")

    # Validate required fields
    if mission_id is None or latitude is None or longitude is None:
        return jsonify({"status": "error", "message": "mission_id, latitude, and longitude are required"}), 400

    # Use current time if timestamp is not provided
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    # Append the data point to the CSV file
    try:
        with open(GPS_DATA_FILE, "a") as f:
            f.write(f"{mission_id},{timestamp},{latitude},{longitude}\n")
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to write data: {e}"}), 500

    return jsonify({"status": "success", "message": "Data point recorded"}), 200

if __name__ == "__main__":
    # Run the Flask app (for demonstration, use default settings)
    app.run(host="0.0.0.0", port=5000, debug=False)

