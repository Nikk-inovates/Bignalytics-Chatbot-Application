# Base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt .

# Install system packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

# Expose port (same as FastAPI default or uvicorn --port)
EXPOSE 8000

# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
