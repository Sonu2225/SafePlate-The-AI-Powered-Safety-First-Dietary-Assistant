# Use a lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Run the database setup script, then start the server with Gunicorn
# Binding to 0.0.0.0 is required for Docker networking
CMD python setup_secure_db.py && gunicorn -w 2 -b 0.0.0.0:5000 app:app