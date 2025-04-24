from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import openai
import os
from dotenv import load_dotenv
from config import OPENAI_API_KEY

load_dotenv()

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client["youtube_history"]

@app.route("/analyze", methods=["POST"])
def analyze():
    return None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
