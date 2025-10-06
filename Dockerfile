FROM python:3.11-slim
WORKDIR /app

# Install system dependencies for LightGBM
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn","api.main:app","--host","0.0.0.0","--port","8080"]

