"""Pytest functions for testing the web app."""

import io
from bson import ObjectId
from bson.errors import InvalidId
from unittest.mock import patch
import json
import pytest
from app import processWatchHistory, metrics, logOutput

@patch("app.requests.get")
def test_processWatchHistory_parses_and_enriches(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "items": [{
            "id": "abc123def45",
            "contentDetails": {"duration": "PT4M20S"},
            "snippet": {
                "title": "Test Video",
                "channelTitle": "Test Channel",
                "categoryId": "22",
                "tags": ["test", "demo"]
            }
        }]
    }

    mock_data = []
    for _ in range(52):
        mock_data.append({
            "title": "Watched Test Video",
            "time": "2023-10-01T12:00:00Z",
            "titleUrl": "https://www.youtube.com/watch?v=abc123def45"
        })
    file_obj = io.BytesIO(json.dumps(mock_data).encode("utf-8"))
    result = processWatchHistory(file_obj)

    assert result is not None
    assert metrics["total_watchtime"] > 0
    assert metrics["channel_stats"]["Test Channel"]["frequency"] == 2
    assert "test" in metrics["tag_frequency"]

def test_log_output_prints(capsys):
    logOutput()
    captured = capsys.readouterr()
    assert "Total Watchtime:" in captured.out


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"YouTube History Analyzer" in response.data
    assert b"Welcome to the YouTube Viewer Analyzer" in response.data
    assert b"Choose your YouTube JSON file" in response.data

def test_upload_success(client, mock_db, mock_requests_post):
    """Mock DB insert + requests.post to avoid hitting the analyzer service."""
    fake_file = io.BytesIO(b'[{"title": "Test Video", "time": "2023-10-01T12:00:00"}]')
    data = {'file': (fake_file, 'watch-history.json')}
    mock_db.Request.insert_one.return_value.inserted_id = ObjectId("6522b06b9f2e4e3d8f5b5e29")
    mock_requests_post.return_value.status_code = 200
    mock_requests_post.return_value.json.return_value = {"status": "ok"}

    response = client.post("/upload", data=data, content_type='multipart/form-data')
    assert response.status_code in [200, 302]
    if response.status_code == 302:
        assert "/results/" in response.location
    assert response.location.endswith("6522b06b9f2e4e3d8f5b5e29")



def test_results_page_valid_objectid(client, mock_db):
    """Ensure /results/<id> loads with valid analysis."""
    valid_id = str(ObjectId())
    mock_db.Request.find_one.return_value = {
        "_id": ObjectId(valid_id),
        "analysis": json.dumps({
            "watch_time": {  # top-level total watch time
                "total_seconds_watched": 12345,
                "daily_average": 3600,
                "busiest_day": "Saturday"
            },
            "channels": {
                "most_frequent": ["Mock Channel 1", "Mock Channel 2"],
                "watch_time": {
                    "Mock Channel 1": 100,
                    "Mock Channel 2": 80
                }
            },
            "categories": {
                "most_watched": ["Education", "Gaming"],
                "watch_time": {
                    "Education": 50,
                    "Gaming": 30
                }
            },
            "habits": {
                "summary": "Mock summary",
                "recommendations": ["Watch more documentaries", "Try different topics"],
                "top_tags": ["Education", "Gaming"]
            }
        })
    }

    response = client.get(f"/results/{valid_id}")
    assert response.status_code == 200
    assert b"YouTube History Analyzer" in response.data
    assert b"Back to Home" in response.data



def test_results_page_not_found(client, mock_db):
    """Simulate ObjectId is valid but nothing is found."""
    valid_id = str(ObjectId())
    mock_db.Request.find_one.return_value = None  # Not found in DB

    response = client.get(f"/results/{valid_id}")
    assert response.status_code == 400
    assert b"Couldn't generate results" in response.data
    assert b"Try again" in response.data
    
def test_results_page_invalid_objectid(client):
    """Test invalid ObjectId raises InvalidId error."""
    with patch("app.ObjectId", side_effect=InvalidId("bad id")):
        with pytest.raises(InvalidId):
            client.get("/results/invalid-object-id")
