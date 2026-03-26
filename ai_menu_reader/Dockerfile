# Use exact Python version
FROM python:3.10.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (fixed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgtk-3-0 \
    libgl1 \
    libatlas-base-dev \
    liblapack-dev \
    libblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip (recommended)
RUN pip install --upgrade pip

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Extra packages
RUN pip install --no-cache-dir sarvamai python-dotenv

# Copy app
COPY . .

# Expose port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# ✅ 5️⃣ Build Docker Image
# docker build -t be-project .

# ✅ 6️⃣ Run Container
# docker run --rm --env-file .env -p 8000:8000 be-project
