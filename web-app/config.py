import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
