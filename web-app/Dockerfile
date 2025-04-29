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

# Install dependencies using pipenv
RUN pipenv install --deploy --system

# Copy requirements.txt and install dependencies using pip as a backup
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

EXPOSE 5002

CMD ["python", "app.py"]
