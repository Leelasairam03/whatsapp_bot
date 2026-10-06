import os
import time
import zipfile
import pandas as pd
import pywhatkit as kit
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
EXTRACT_FOLDER = "extracted_reports"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_zip():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "" or not file.filename.endswith(".zip"):
        return jsonify({"error": "Invalid file format"}), 400

    zip_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(zip_path)

    # Extract ZIP file
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(EXTRACT_FOLDER)

    # Check for CSV file
    csv_path = os.path.join(EXTRACT_FOLDER, "ff.csv")
    if not os.path.exists(csv_path):
        return jsonify({"error": "CSV file not found in ZIP"}), 400

    df = pd.read_csv(csv_path, dtype={"Phone": str})


    # Send WhatsApp messages with JPG reports
    for _, row in df.iterrows():
        USN = row["USN"]
        phone_number = row["Phone"]
        jpg_filename = f"{USN}.jpg"  # Report file is named as USN.jpg
        jpg_path = os.path.join(EXTRACT_FOLDER, jpg_filename)

        if os.path.exists(jpg_path):
            message = f"Dear Parent, here is the marks report for {USN}."
            try:
                kit.sendwhats_image(phone_number, jpg_path, caption=message, wait_time=10)
                print(f"✅ Sent report to {phone_number} ({USN})")
            except Exception as e:
                print(f"❌ Error sending message to {phone_number}: {str(e)}")
        else:
            print(f"⚠️ Report not found for USN: {USN}")

        time.sleep(15)  # Delay to avoid spam detection

    return jsonify({"message": "Reports sent successfully!"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
