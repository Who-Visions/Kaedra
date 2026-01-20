# Use Python 3.12 Slim for better performance and smaller image size
FROM python:3.12-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONPATH /app

# Copy local code to the container image.
WORKDIR /app
COPY . ./

# Install production dependencies.
# We use --no-cache-dir to keep the image small.
RUN pip install --no-cache-dir -r requirements.txt

# Run the web service on container startup.
# We use Gunicorn with Uvicorn workers for production-grade reliability and performance.
# Cloud Run sets the PORT env var.
CMD exec gunicorn --bind :$PORT --workers 1 --worker-class uvicorn.workers.UvicornWorker --timeout 0 kaedra.api.main:app
