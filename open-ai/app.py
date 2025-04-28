from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
mongo_client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = mongo_client["youtube_history"]

@app.route("/summarize", methods=["POST"])
def summarize():
    """Pull YouTube history from MongoDB by ID and summarize."""
    data = request.get_json()
    request_id = data.get("id")

    if not request_id:
        return jsonify({"error": "No ID provided."}), 400

    req = db.Request.find_one({"_id": ObjectId(request_id)})
    if not req:
        return jsonify({"error": "Request ID not found."}), 404

    youtube_data = req.get("raw_data")
    if not youtube_data:
        return jsonify({"error": "No YouTube data found."}), 400

    try:
        title = [entry.get("title", "") for entry in youtube_data]
        title = title[:20] #only 20 videos because it was getting overloaded with more

        if not title:
            return jsonify({"error": "No valid titles found to summarize."}), 400

        titles_text = "\n".join(title)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": ("You are a playful and concise assistant who analyzes YouTube watch histories. You should:\n"
                    "- summarize the user's viewing habits in a fun, upbeat tone\n"
                    "- be imaginative but concise and return a 2-3 sentence paragraph style analysis."
                )},
                {"role": "user", "content": f"Here is their YouTube watch history (titles only):\n{titles_text}"}
            ],
            temperature=0.8
        )

        summary = response.choices[0].message.content

        db.Request.update_one(
            {"_id": ObjectId(request_id)},
            {"$set": {"analysis": summary}}
        )

        return jsonify({"summary": summary})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)

