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
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy application code and env file
COPY . .

# Auth service needs the data directory for SQLite volume mount
RUN mkdir -p /app/data && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8001

CMD ["sh", "-c", "cd auth_service && python manage.py migrate --noinput && gunicorn auth_service.wsgi:application --bind 0.0.0.0:8001 --workers 2 --worker-tmp-dir /tmp"]