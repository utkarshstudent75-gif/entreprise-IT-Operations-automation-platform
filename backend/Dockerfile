FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies and create a non-root user in a single RUN instruction
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser appuser

COPY requirements.txt .

RUN pip install --no-cache-dir pip==25.0.1 && \
    pip install --no-cache-dir -r requirements.txt

# Copy files with default root ownership (read-only for the non-root appuser)
COPY app/ ./app
COPY alembic/ ./alembic
COPY alembic.ini .
COPY --chmod=0755 entrypoint.sh .

# Use the non-root user
USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]