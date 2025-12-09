FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose both collector and OTLP ports
EXPOSE 8001 4318

# Start collector on both ports
CMD ["sh", "-c", "uvicorn collector:app --host 0.0.0.0 --port 8001 & uvicorn collector:app --host 0.0.0.0 --port 4318 & wait"]