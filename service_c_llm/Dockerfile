FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# This service doesn't have a DB setup, so just start Gunicorn
# We use -k gthread to support the streaming generator
CMD gunicorn -w 1 --threads 4 -b 0.0.0.0:5002 app:app