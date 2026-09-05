FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies and create a non-root user
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser appuser

COPY requirements.txt .

RUN pip install --no-cache-dir pip==26.1.2 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application and microservices code
COPY app/ ./app
COPY services/ ./services
COPY alembic/ ./alembic
COPY alembic.ini .
COPY --chmod=0755 entrypoint.sh .

# Use the non-root user
USER appuser

EXPOSE 8000 8001 8002 8003 8004 8005

ENTRYPOINT ["/app/entrypoint.sh"]