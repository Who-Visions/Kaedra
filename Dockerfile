
# Use official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create local directories for Kaedra (to avoid permission issues if code tries to write there)
# Note: In Cloud Run, only /tmp is writable, but we'll create the structure in /root/.kaedra or similar if needed.
# The config uses Path.home() / ".kaedra", so it will try to write to /root/.kaedra.
# We should pre-create it or ensure it can handle it.
RUN mkdir -p /root/.kaedra/chat_logs /root/.kaedra/memory /root/.kaedra/profiles /root/.kaedra/config /root/.kaedra/videos

# Expose the port
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "kaedra.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
