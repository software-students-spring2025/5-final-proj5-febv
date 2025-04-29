
# import os
# import sys
# import pytest

# # Make it possible to `import app` even though the folder is called `web-app`
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# import app  # this is web-app/app.py
# print("Imported app from:", app.__file__)

# @pytest.fixture
# def client():
#     app.app.config["TESTING"] = True
#     app.app.secret_key = "test"
#     with app.app.test_client() as client:
#         with client.session_transaction() as session:
#             session["logged_in"] = True
#             session["username"] = "testuser"
#         yield client

"""Pytest fixtures for testing the web app."""

import os
import sys
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app  # web-app/app.py


@pytest.fixture
def mock_db():
    with patch("app.db") as mock_db:
        yield mock_db


@pytest.fixture
def mock_requests_post():
    with patch("app.requests.post") as mock_post:
        yield mock_post


@pytest.fixture
def client(mock_db, mock_requests_post):
    app.app.config["TESTING"] = True
    app.app.secret_key = "test"
    with app.app.test_client() as client:
        with client.session_transaction() as session:
            session["logged_in"] = True
            session["username"] = "testuser"
        yield client
