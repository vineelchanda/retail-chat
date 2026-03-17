FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Cloud Run sets PORT env var (default 8080)
ENV PORT=8080
EXPOSE ${PORT}

# Run Streamlit on the Cloud Run PORT, listening on all interfaces
CMD streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true
