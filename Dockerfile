FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run app
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]

# ✅ 5️⃣ Build Docker Image
# docker build -t sarvam-speech .
# docker build -t sarvam-speech . 

# ✅ 6️⃣ Run Container
# docker run --rm  sarvam-speech
# docker run --rm --env-file .env -p 8000:8000 sarvam-speech
