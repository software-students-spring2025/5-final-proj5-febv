"""Flask app to analyze user's Youtube watch data."""

from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import os
import requests
import json

app = Flask(__name__)
client = MongoClient("mongodb://mongodb:27017")
db = client["youtube_history"]

@app.route("/")
def home():
    """Render the homepage."""
    return render_template("home.html")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or not file.filename.endswith(".json"):
        return {"error": "Please upload a JSON file."}, 400

    history = json.load(file)
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
    app.run(host="0.0.0.0", port=5002, debug=True)