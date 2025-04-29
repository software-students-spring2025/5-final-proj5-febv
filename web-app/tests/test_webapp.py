"""Testing web-app/app.py file."""

import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_page(client):
    """Test that home page loads successfully."""
    response = client.get("/")
    assert response.status_code == 200


def test_example_results(client):
    """Test that example results page loads successfully."""
    response = client.get("/example-results")
    assert response.status_code == 200


def test_upload_no_file(client):
    """Test upload endpoint with no file."""
    response = client.post("/upload")
    assert response.status_code == 400


def test_upload_wrong_file_type(client):
    """Test upload endpoint with wrong file type."""
    data = {"file": (b"test data", "test.txt")}
    response = client.post("/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 400 