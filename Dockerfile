FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Reduce image size
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY src/ ./src/

# Create non-root user
RUN addgroup --system app && adduser --system --group app
USER app

# Expose a commonly used port (change if your app uses another)
EXPOSE 5000


# HEALTHCHECK goes here (after USER, before CMD)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/live || exit 1

ARG GUNICORN_WORKERS=4
ENV GUNICORN_WORKERS=$GUNICORN_WORKERS
CMD ["gunicorn", "--workers", "$GUNICORN_WORKERS", "--bind", "0.0.0.0:5000", "src.app:app"]
