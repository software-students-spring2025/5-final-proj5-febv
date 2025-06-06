![Web App CI/CD](https://github.com/software-students-spring2025/5-final-proj5-febv/actions/workflows/web-app.yml/badge.svg?branch=)
![OpenAI CI/CD](https://github.com/software-students-spring2025/5-final-proj5-febv/actions/workflows/open-ai.yml/badge.svg?branch=)

# YouTube Watch History Analyzer

This project allows users to upload their YouTube watch history and recieved a synthesized analysis of their viewing habits. 

## Deployed App
Check out the [deployed app](http://45.55.231.88:5002/).

## Container Images
- [Web-App Docker Image](https://hub.docker.com/r/emney/web-app)
- [Open-AI Docker Image](https://hub.docker.com/r/emney/open-ai)

## Team Members:
- [Forrest Williams](https://github.com/Zeklin)
- [Vladimir Kartamyshev](https://github.com/lawaldemur)
- [Brian Tylo](https://github.com/brian105)
- [Emily Ney](https://github.com/EmilyNey)

## How to Run This Project:
### Setup:
1. Clone the repository:<br>
```
git clone https://github.com/software-students-spring2025/5-final-proj5-febv.git
```
2. Create a `.env` file based on the `.env.example` file:<br>
```
OPENAI_API_KEY=your_openai_api_key
YOUTUBE_API_KEY=your_youtube_api_key
```
3. Build and start the application with docker:<br>
```
docker compose up --build
```
The web application will be available at http://localhost:5002

The Open-AI service will run on http://localhost:8000

### How to Upload Data:
After starting the project, visit http://localhost:5002 and use the Upload page to submit a YouTube Watch History JSON file. The file must match the format exported by Google's Takeout under YouTube Watch History. There are instructions about how to access this data on the site. 

### Environment Variables:
An example .env file is provided (.env.example) with placeholder values. Before running the system, you must:
- Create your own .env file by copying env.example
- Replace the dummy values with your actual OpenAI and YouTube API keys.

### Testing
Tests for both the web application and backend can be run locally:
```
cd web-app && pytest tests/
cd open-ai && pytest tests/
```