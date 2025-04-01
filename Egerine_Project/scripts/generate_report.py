import os
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# === CONFIG ===
GPS_DATA_PATH = "data/gps_data.csv"
VALIDATION_PATH = "data/validation_results.csv"
REPORT_OUTPUT_FOLDER = "reports"
VISUALS_FOLDER = "visuals"

class CustomPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(100)
        generated_on = datetime.now().strftime("%Y-%m-%d")
        self.cell(0, 10, f"Generated on: {generated_on} by Egerine AI Engine", align="C")

def generate_report(mission_id):
    os.makedirs(REPORT_OUTPUT_FOLDER, exist_ok=True)
    df_val = pd.read_csv(VALIDATION_PATH)
    row = df_val[df_val["mission_id"] == mission_id].iloc[-1]
    df_gps = pd.read_csv(GPS_DATA_PATH)
    df_gps = df_gps[df_gps["mission_id"] == mission_id].copy()
    df_gps["timestamp"] = pd.to_datetime(df_gps["timestamp"])
    start_time = df_gps["timestamp"].min()
    end_time = df_gps["timestamp"].max()

    distance = row["distance_km"]
    duration = row["duration_min"]
    area = row["area_km2"]
    avg_speed = row["avg_speed_kmh"]
    num_points = row["num_points"]
    offroad = row["offroad_points"]
    status = row["status"]
    anomalies = row["anomalies"]
    ml_pred = row["ml_pred"]
    co2_saved = round(distance * 0.21, 2)

    pdf = CustomPDF()
    pdf.add_page()

    def section_title(title):
        pdf.set_font("Arial", 'B', 14)
        pdf.set_fill_color(230, 230, 255)
        pdf.cell(0, 10, title, ln=True, fill=True)
        pdf.set_font("Arial", '', 12)
        pdf.ln(2)

    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(0)
    pdf.cell(0, 10, f"Mission Report: {mission_id}", ln=True)
    pdf.ln(4)

    # Mission Summary
    section_title("Mission Summary")
    pdf.cell(0, 8, f"Start Time       : {start_time}", ln=True)
    pdf.cell(0, 8, f"End Time         : {end_time}", ln=True)
    pdf.cell(0, 8, f"Duration         : {duration:.2f} minutes", ln=True)
    pdf.cell(0, 8, f"Distance         : {distance:.2f} km", ln=True)
    pdf.cell(0, 8, f"Area Covered     : {area:.4f} km²", ln=True)
    pdf.cell(0, 8, f"Average Speed    : {avg_speed:.2f} km/h", ln=True)
    pdf.cell(0, 8, f"GPS Points       : {num_points}", ln=True)

    # Environmental Impact
    section_title("Environmental Impact")
    pdf.cell(0, 8, f"Estimated CO2 Saved: {co2_saved:.2f} kg", ln=True)

    # Anomaly Detection
    section_title("Anomaly Detection")
    if anomalies and anomalies != "None":
        for a in str(anomalies).split(";"):
            pdf.set_text_color(200, 0, 0)
            pdf.cell(0, 8, f"- {a.strip()}", ln=True)
        pdf.set_text_color(0)
    else:
        pdf.cell(0, 8, "No rule-based anomalies detected.", ln=True)

    ai_text = "Anomalous" if ml_pred == 1 else "Valid"
    ai_color = (200, 0, 0) if ml_pred == 1 else (0, 150, 0)
    pdf.set_text_color(*ai_color)
    pdf.cell(0, 8, f"AI Model Prediction: {ai_text}", ln=True)
    pdf.set_text_color(0)

    # Final Verdict
    section_title("Final Verdict")
    if status == "Valid":
        pdf.set_text_color(0, 180, 0)
        verdict_text = "STATUS: VALID"
    else:
        pdf.set_text_color(200, 0, 0)
        verdict_text = "STATUS: ANOMALOUS"

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, verdict_text, ln=True)
    pdf.set_text_color(0)
    pdf.set_font("Arial", '', 12)

    # Optional Map
    map_path = f"{VISUALS_FOLDER}/map_screenshot_{mission_id}.png"
    if os.path.exists(map_path):
        pdf.add_page()
        section_title("Route Map")
        pdf.image(map_path, x=15, y=30, w=180)

    # Save PDF
    output_path = os.path.join(REPORT_OUTPUT_FOLDER, f"Mission_Report_{mission_id}.pdf")
    pdf.output(output_path)
    print(f"PDF report saved as: {output_path}")

# === Run single mission for test ===
if __name__ == "__main__":
    generate_report("mission_road_3")
