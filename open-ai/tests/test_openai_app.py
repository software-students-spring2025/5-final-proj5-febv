"""Testing open-ai/app.py file."""

import json
import pytest
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_analyze_missing_id(client):
    """
    Testing that a bad request returns error code.
    """
    response = client.post("/analyze", json={})
    assert response.status_code == 400
    assert b"Missing request ID" in response.data


@patch("app.db")
def test_analyze_record_not_found(mock_db, client):
    """
    Testing that a non-existing record returns error code.
    """
    mock_db.Request.find_one.return_value = None
    response = client.post("/analyze", json={"id": "012345678901234567890123"})
    assert response.status_code == 404
    assert b"Request not found" in response.data


@patch("app.db")
def test_analyze_no_data(mock_db, client):
    """
    Testing that a record without any data returns error code.
    """
    mock_db.Request.find_one.return_value = {"raw_data": []}
    response = client.post("/analyze", json={"id": "012345678901234567890123"})
    assert response.status_code == 400
    assert b"No watch history data found" in response.data


@patch("app.client")
@patch("app.db")
def test_analyze_no_api_key(mock_db, mock_client, client):
    """
    Testing that a missing API key returns error code.
    """
    mock_db.Request.find_one.return_value = {"raw_data": ["sample data"]}
    mock_client.api_key = None
    response = client.post("/analyze", json={"id": "012345678901234567890123"})
    assert response.status_code == 500
    assert b"OpenAI API key not configured" in response.data


@patch("app.client")
@patch("app.db")
def test_analyze_success(mock_db, mock_client, client):
    """
    Testing that a valid request is accepted.
    """
    mock_db.Request.find_one.return_value = {"raw_data": ["sample data"]}
    mock_client.api_key = "fake-key"

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"fake": "result"}'))]
    mock_client.chat.completions.create.return_value = mock_response

    response = client.post("/analyze", json={"id": "012345678901234567890123"})
    assert response.status_code == 200
    assert b"success" in response.data


@patch("app.client")
@patch("app.db")
def test_analyze_openai_auth_error(mock_db, mock_client, client):
    """
    Testing that authentication errors are handled.
    """
    mock_db.Request.find_one.return_value = {"raw_data": ["sample data"]}
    mock_client.api_key = "fake-key"
    mock_client.chat.completions.create.side_effect = Exception("Authentication error")

    response = client.post("/analyze", json={"id": "012345678901234567890123"})
    assert response.status_code == 500
    assert b"Internal server error" in response.data


@patch("app.client")
@patch("app.db")
def test_analyze_openai_rate_limit_error(mock_db, mock_client, client):
    """
    Testing that issue with OpenAI rate limit returns error code.
    """
    mock_db.Request.find_one.return_value = {"raw_data": ["sample data"]}
    mock_client.api_key = "fake-key"
    mock_client.chat.completions.create.side_effect = Exception("Rate limit exceeded")

    response = client.post("/analyze", json={"id": "012345678901234567890123"})
    assert response.status_code == 500
    assert b"Internal server error" in response.data


@patch("app.client")
@patch("app.db")
def test_analyze_openai_api_error(mock_db, mock_client, client):
    """
    Testing that miscellaneous OpenAI API error returns an error code.
    """
    mock_db.Request.find_one.return_value = {"raw_data": ["sample data"]}
    mock_client.api_key = "fake-key"
    mock_client.chat.completions.create.side_effect = Exception("API Error")

    response = client.post("/analyze", json={"id": "012345678901234567890123"})
    assert response.status_code == 500
    assert b"Internal server error" in response.data
