FROM python:3.9-slim

WORKDIR /app

# Install pipenv and other system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip \
    && pip install pipenv

# Copy Pipfile and Pipfile.lock first to leverage Docker cache
COPY Pipfile Pipfile.lock* ./

# Install dependencies
RUN pipenv install --deploy --system

# Copy the rest of the application
COPY . .

EXPOSE 8000
CMD ["python", "app.py"]
