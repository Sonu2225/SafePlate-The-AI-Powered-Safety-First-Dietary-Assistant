FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run DB setup (downloads CSV, builds FTS index) then start server
CMD python setup_db.py && gunicorn -w 2 -b 0.0.0.0:5001 app:app