# Use Python 3.12 slim base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Upgrade pip, setuptools, wheel, and install dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Copy the rest of your project
COPY . .

# Expose port (for webhooks / uvicorn)
EXPOSE 8000

# Command to run your bot
# Replace bot:app with your entry point if different
CMD ["uvicorn", "bot:app", "--host", "0.0.0.0", "--port", "8000"]
