# Use the official Python image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.in .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.in

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p db_memoria documenti_da_processare documenti_archiviati

# Expose port for Streamlit
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
