FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside container
WORKDIR /

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc libglib2.0-0 libsm6 libxrender1 libxext6 \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    build-essential \
    curl \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements first (to leverage Docker cache)
COPY requirements.txt .
COPY .streamlit/ /.streamlit/

# Install Python packages
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source code
COPY src/ ./src/

# Expose Streamlit default port
EXPOSE 8080

# Start Streamlit
CMD ["streamlit", "run", "src/main_app.py", "--server.port=8080", "--server.enableCORS=false"]
