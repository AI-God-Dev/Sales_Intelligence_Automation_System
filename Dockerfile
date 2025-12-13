# Multi-stage Dockerfile for Sales Intelligence System
# Stage 1: Build dependencies
FROM python:3.11-slim



WORKDIR /app



# Copy requirements from web_app
COPY web_app/requirements.txt .



# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt



# Copy the utils and config directories
COPY utils ./utils
COPY config ./config



# Copy web_app files
COPY web_app/app.py .
COPY web_app/.streamlit ./.streamlit



# Expose Streamlit port
EXPOSE 8080



# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]


