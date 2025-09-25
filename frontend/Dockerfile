FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY ../pyproject.toml /app/
COPY ../uv.lock /app/ 2>/dev/null || true

# Install uv
RUN pip install uv

# Install dependencies
RUN uv sync --frozen

# Copy frontend code
COPY . /app/

# Expose port
EXPOSE 8501

# Command to run the application
CMD ["uv", "run", "streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
