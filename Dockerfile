# Use Python 3.12 slim base image
FROM python:3.12-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy requirements first (cache layer)
COPY requirements.txt .

# Upgrade pip, setuptools, wheel, and install dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project
COPY . .

# Expose port (for webhooks / uvicorn)
EXPOSE 8000

# Command to run the bot with Uvicorn using factory flag
CMD ["sh", "-c", "uvicorn bot:create_app --factory --host 0.0.0.0 --port ${PORT:-8000} --loop asyncio"]
