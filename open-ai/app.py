from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from openai import OpenAI, AuthenticationError, RateLimitError, APIError
import os
from dotenv import load_dotenv
from config import OPENAI_API_KEY

load_dotenv()

app = Flask(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
mongo_client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = mongo_client["youtube_history"]

@app.route("/analyze", methods=["POST"])
def analyze():
    """Analyze YouTube watch history using OpenAI and update MongoDB with results."""
    try:
        # Get the request ID from the web app
        data = request.get_json()
        if not data or "id" not in data:
            return jsonify({"error": "Missing request ID"}), 400

        request_id = data["id"]
        
        # Get the record from MongoDB
        record = db.Request.find_one({"_id": ObjectId(request_id)})
        if not record:
            return jsonify({"error": "Request not found"}), 404

        # Prepare the data for analysis
        watch_history = record.get("raw_data", [])
        if not watch_history:
            return jsonify({"error": "No watch history data found"}), 400

        # Verify OpenAI API key
        if not client.api_key:
            return jsonify({"error": "OpenAI API key not configured"}), 500

        # Limit the data size for analysis
        if len(str(watch_history)) > 4000:  # Rough estimate of token limit
            watch_history = watch_history[:100]  # Take first 100 entries

        # Create a prompt for OpenAI
        prompt_json_structure = '''
        {{
            "categories": {{
                "most_watched": [],
                "watch_time": {{}}
            }},
            "patterns": {{
                "time_of_day": {{}},
                "days_of_week": {{}}
            }},
            "channels": {{
                "most_frequent": [],
                "watch_time": {{}}
            }},
            "habits": {{
                "summary": "",
                "recommendations": []
            }}
        }}
        '''
        prompt_json_example = '''
        {
            "categories": {
                "most_watched": [
                    "Category 1",
                    "Category 2",
                    "Category 3",
                    "Category 4",
                    "Category 5"
                ],
                "watch_time": {
                    "Category 1": 15,
                    "Category 2": 8,
                    "Category 3": 6,
                    "Category 4": 5,
                    "Category 5": 4
                }
            },
            "patterns": {
                "time_of_day": {
                    "morning": 5,
                    "afternoon": 12,
                    "evening": 15,
                    "night": 8
                },
                "days_of_week": {
                    "Monday": 3,
                    "Tuesday": 5,
                    "Wednesday": 7,
                    "Thursday": 10,
                    "Friday": 8,
                    "Saturday": 5,
                    "Sunday": 6
                }
            },
            "channels": {
                "most_frequent": [
                    "Channel 1",
                    "Channel 2",
                    "Channel 3",
                    "Channel 4",
                    "Channel 5"
                ],
                "watch_time": {
                    "Channel 1": 20,
                    "Channel 2": 15,
                    "Channel 3": 12,
                    "Channel 4": 10,
                    "Channel 5": 10
                }
            },
            "habits": {
                "summary": "Summary.",
                "recommendations": [
                    "Recommendation 1.",
                    "Recommendation 2.",
                    "Recommendation 3."
                ]
            }
        }
        '''
        prompt = f"""Analyze this YouTube watch history data and provide insights about:
1. Most watched categories
2. Watch time patterns
3. Most frequent channels
4. General viewing habits

Data: {watch_history}

Please provide a detailed analysis in JSON format with the following structure without internal comments or leading quotations, categories and channels should be organized descending by watchtime:
{prompt_json_structure}

An example output is included for your reference:
{prompt_json_example}
"""

        try:
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a YouTube watch history analyst. Analyze the data and provide insights in the specified JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            # Get the analysis from the response
            analysis = response.choices[0].message.content

            # Update the record in MongoDB
            db.Request.update_one(
                {"_id": ObjectId(request_id)},
                {"$set": {"analysis": analysis}}
            )

            return jsonify({"status": "success", "message": "Analysis completed"}), 200

        except AuthenticationError as e:
            return jsonify({"error": "OpenAI authentication failed", "details": str(e)}), 500
        except RateLimitError as e:
            return jsonify({"error": "OpenAI rate limit exceeded", "details": str(e)}), 429
        except APIError as e:
            return jsonify({"error": "OpenAI API error", "details": str(e)}), 500

    except Exception as e:
        app.logger.error(f"Error in analyze endpoint: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)