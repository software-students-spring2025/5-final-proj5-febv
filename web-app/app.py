"""Flask app to analyze user's Youtube watch data."""

from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from collections import defaultdict
from config import YOUTUBE_API_KEY
import os
import requests
import json
import re
import isodate

app = Flask(__name__)
client = MongoClient("mongodb://mongodb:27017")
db = client["youtube_history"]

metrics = {
    "total_watchtime": 0,
    "total_videos": 0,
    "hourly_watchtime": {},
    "tag_frequency": {},
    "channel_stats": defaultdict(lambda: {"watchtime": 0, "frequency": 0}),
    "category_stats": defaultdict(lambda: {"watchtime": 0, "frequency": 0}),
    "longest_video": {"video_id": "", "duration": 0},
    "shortest_video": {"video_id": "", "duration": float("inf")},
}

def processWatchHistory(raw_data, chunk_size=5000, limit=1000):
    clean_data = []
    video_count = 0
    with open(raw_data, "r", encoding="utf-8") as f:
        records = json.load(f)
        for record in records:
            if video_count >= limit:
                break
            
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
            
            video_count += 1
            
            if len(clean_data) >= chunk_size:
                enrichData(clean_data)
                logOutput()
                clean_data = []
                
        if clean_data:
            enrichData(clean_data)
            logOutput()

def saveWatchHistory(clean_chunk, last_chunk=False):
    #save to mongodb
    return

def enrichData(clean_chunk):
    subchunk = []
    # collect 50 video ids to send to youtube
    for video in clean_chunk:
        # process hourly watchtime
        temp_time = video["timestamp"].hour - 4
        if temp_time < 0:
            temp_time += 24
        metrics["hourly_watchtime"][temp_time] = metrics["hourly_watchtime"].get(temp_time, 0) + 1
        
        subchunk.append(video["video_id"])
        
        if len(subchunk) == 50:
            api_ids = ",".join(subchunk)
            # api call
            params = {
                "key": YOUTUBE_API_KEY,
                "part": "snippet,contentDetails,statistics",
                "fields": "items(id,snippet(title,channelTitle,categoryId,tags,publishedAt),contentDetails(duration))",
                "id": api_ids,
            }
            response = requests.get("https://www.googleapis.com/youtube/v3/videos", params=params)
            enriched_video_data = response.json()
            
            for enriched_video in enriched_video_data["items"]:
                # temp datastore for easy access
                temp_duration = isodate.parse_duration(enriched_video["contentDetails"]["duration"]).total_seconds()
                # 6 hour cap
                if temp_duration > 21600:
                    continue
                temp_tags = enriched_video["snippet"].get("tags", [])
                temp_channel = enriched_video["snippet"].get("channelTitle", "UnknownChannel")
                temp_category = enriched_video["snippet"].get("categoryId", "UnknownCategory")
                
                # metrics update
                metrics["total_watchtime"] += temp_duration
                metrics["total_videos"] += 1
                for tag in temp_tags:
                    metrics["tag_frequency"][tag] = metrics["tag_frequency"].get(tag, 0) + 1
                metrics["channel_stats"][temp_channel]["watchtime"] += temp_duration
                metrics["channel_stats"][temp_channel]["frequency"] += 1
                metrics["category_stats"][temp_category]["watchtime"] += temp_duration
                metrics["category_stats"][temp_category]["frequency"] += 1
                if temp_duration > metrics["longest_video"]["duration"]:
                    metrics["longest_video"]["video_id"] = enriched_video["id"]
                    metrics["longest_video"]["duration"] = temp_duration
                if temp_duration < metrics["shortest_video"]["duration"]:
                    metrics["shortest_video"]["video_id"] = enriched_video["id"]
                    metrics["shortest_video"]["duration"] = temp_duration
            subchunk = []
    # TODO still need to process last subchunk
    return

def logOutput():
    print("Total Watchtime: ", metrics["total_watchtime"])
    print("Total Videos: ", metrics["total_videos"])
    print("Hourly Watchtime: ", metrics["hourly_watchtime"])
    print("\nTag Frequency: ")
    sorted_tags = sorted(metrics["tag_frequency"].items(), key=lambda x: x[1], reverse=True)[:100]
    for tag, freq in sorted_tags:
        print(f"{tag}: {freq}")
    print("\nChannel Stats: ")
    sorted_channels = sorted(metrics["channel_stats"].items(), key=lambda x: x[1]["frequency"], reverse=True)[:100]
    for channel, freq in sorted_channels:
        print(f"{channel}: {freq}")
    print("\nCategory Stats: ")
    sorted_categories = sorted(metrics["category_stats"].items(), key=lambda x: x[1]["frequency"], reverse=True)[:100]
    for category, freq in sorted_categories:
        print(f"{category}: {freq}")
    print("\nLongest Video: ", '"', metrics["longest_video"]["video_id"], '" ', '"', metrics["longest_video"]["duration"], '"')
    print("Shortest Video: ", '"', metrics["shortest_video"]["video_id"], '" ', '"', metrics["shortest_video"]["duration"], '"')

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
    # processWatchHistory("watch-history.json")
    app.run(host="0.0.0.0", port=5002, debug=True)
