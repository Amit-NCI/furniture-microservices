FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app/order-service

EXPOSE 8003

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8003"]