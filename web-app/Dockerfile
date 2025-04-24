FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install --upgrade pip && pip install pipenv
RUN pip install -r requirements.txt

EXPOSE 5002

CMD ["python", "app.py"]
