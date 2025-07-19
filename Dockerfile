# Use a Python base image
FROM python:3.10-slim-buster

# Set working directory in the container
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire source code
COPY src/ ./src/

# Expose the port Streamlit runs on
EXPOSE 8501

# Set environment variable for Streamlit server port
ENV PORT=8501

# Command to run the Streamlit application
CMD ["streamlit", "run", "src/main_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]