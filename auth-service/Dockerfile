# Stage 1 — install dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2 — lean runtime image
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

# Copy application code
COPY . .

# Collect Django static files using temporary build-time settings.
# No database connection is required for collectstatic.
RUN cd /app/auth_service && \
    SECRET_KEY=build-only-placeholder \
    JWT_SIGNING_KEY=build-only-placeholder \
    ALLOWED_HOSTS=localhost \
    CORS_ALLOWED_ORIGINS=http://localhost \
    DB_NAME=placeholder \
    DB_USER=placeholder \
    DB_PASSWORD=placeholder \
    DB_HOST=localhost \
    DB_PORT=5432 \
    python manage.py collectstatic --noinput

# Create application data directory and set ownership
RUN mkdir -p /app/data && \
    chown -R appuser:appgroup /app

# Give the application a writable home directory
ENV HOME=/tmp

USER appuser

EXPOSE 8001

CMD ["sh", "-c", "cd auth_service && python manage.py migrate --noinput && gunicorn auth_service.wsgi:application --bind 0.0.0.0:8001 --workers 2 --worker-tmp-dir /tmp"]