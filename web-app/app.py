"""Flask app to analyze user's Youtube watch data."""

from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import os
import requests
import json
import re

app = Flask(__name__)
client = MongoClient("mongodb://mongodb:27017")
db = client["youtube_history"]

def processWatchHistory(raw_data, chunk_size=5000):
    clean_data = []
    with open(raw_data, "r", encoding="utf-8") as f:
        records = json.load(f)
        for record in records:
            if "titleUrl" not in record:
                continue

            title_url = record["titleUrl"].encode().decode('unicode_escape')
            match = re.search(r"v=(.{11})", title_url)
            if not match:
                continue
            
            video_id = match.group(1)
            timestamp = datetime.fromisoformat(record["time"].replace("Z", "+00:00"))
            
            clean_data.append({
                "video_id": video_id,
                "timestamp": timestamp
            })
            
            if len(clean_data) >= chunk_size:
                saveWatchHistory(clean_data)
                clean_data = []
                
        if clean_data:
            saveWatchHistory(clean_data)

def saveWatchHistory(clean_chunk):
    print("Chunked")

@app.route("/")
def home():
    """Render the homepage."""
    return render_template("home.html")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or not file.filename.endswith(".json"):
        return {"error": "Please upload a JSON file."}, 400

    history = processWatchHistory(file)
    
    data = {
        "Timestamp": datetime.now(), 
        "raw_data": history, 
        "analysis": None
    }

    inserted = db.Request.insert_one(data)

    analysis_url = os.getenv("OPENAI_API_KEY", "http://open-ai:8000")
    requests.post(f"{analysis_url}/analyze", json={"id": str(inserted.inserted_id)})

    return redirect(url_for("results", id=str(inserted.inserted_id)))

@app.route("/results/<id>")
def results(id):
    data = db.Request.find_one({"_id": ObjectId(id)})
    if not data:
        return {"error": "Couldn't generate results. Try again."}, 400
    if not data.get("analysis"):
        return render_template("loading.html", id=id)

    return render_template("results.html", analysis=data["analysis"], id=id)

# main driver function
if __name__ == "__main__":
    processWatchHistory("watch-history.json")
    #app.run(host="0.0.0.0", port=5002, debug=True)