FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

COPY . .
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8003

CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn order_service.wsgi:application --bind 0.0.0.0:8003 --workers 2 --worker-tmp-dir /tmp"]