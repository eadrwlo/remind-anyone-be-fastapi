FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (needed for psycopg2 compilation sometimes, though using binary)
# gcc and others might be needed if packages require compilation
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Command to run the application
# Using reload for development, in production remove --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
