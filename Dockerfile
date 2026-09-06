# Use lightweight official Python image
FROM python:3.11-slim

# Install FFmpeg, ffprobe and required media tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install python dependencies
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend and frontend source files
COPY backend /app/backend
COPY frontend /app/frontend

# Create storage directories
RUN mkdir -p /app/backend/uploads /app/backend/projects /app/backend/data/branding

# Set default port
EXPOSE 8000
ENV PORT=8000
WORKDIR /app/backend

# Launch Umar AI Video Studio
CMD ["python", "app.py"]
