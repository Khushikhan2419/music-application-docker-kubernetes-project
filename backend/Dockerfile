# Use an official Python image as the base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy app code
COPY app.py /app/
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose backend port
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
