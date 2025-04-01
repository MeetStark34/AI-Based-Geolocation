import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

# === CONFIG ===
DATA_PATH = "data/mission_dataset.csv"
MODEL_PATH = "models/anomaly_model.pkl"
FEATURES = ["distance_km", "duration_min", "avg_speed_kmh", "area_km2", "num_points"]

# === Load Dataset ===
df = pd.read_csv(DATA_PATH)

if df.empty or "label" not in df.columns:
    print("❌ Dataset is empty or missing 'label' column.")
    exit()

X = df[FEATURES]
y = df["label"]

# === Train/Test Split ===
if len(df) < 5:
    print("⚠️ Not enough data to split. Training with all available samples.")
    X_train, y_train = X, y
    X_test, y_test = X, y
else:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === Train Model ===
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# === Evaluate ===
y_pred = model.predict(X_test)
print("\n📊 Model Evaluation:\n")
print(classification_report(y_test, y_pred))

# === Save Model ===
os.makedirs("models", exist_ok=True)
joblib.dump(model, MODEL_PATH)
print(f"✅ Model saved to {MODEL_PATH}")
