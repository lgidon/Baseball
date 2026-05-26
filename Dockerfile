FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Reduce image size and install build deps for potential wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies if requirements.txt exists at build time
COPY requirements.txt requirements.txt
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi || true

# Copy project
COPY . .

# Expose a commonly used port (change if your app uses another)
EXPOSE 5000

CMD ["python", "app.py"]
