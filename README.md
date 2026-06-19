#  Furniture E-Commerce Platform (Microservices Architecture)

##  Project Overview

This project is a containerized e-commerce platform built using a Microservices Architecture.

The application is divided into independent services responsible for authentication, product management, order processing, and frontend rendering. All services communicate through REST APIs and are orchestrated using Docker Compose.

The project was built to gain hands-on experience with:

* Microservices Architecture
* Django REST Framework
* JWT Authentication
* Docker & Docker Compose
* Nginx Reverse Proxy
* Service-to-Service Communication
* REST API Design
* Persistent Storage
* Backend System Design

---

#  Key Features

### Authentication Service

* User Registration
* User Login
* JWT Authentication
* Access Token & Refresh Token Generation
* Role-Based Users
* User Approval Workflow

### Product Service

* Product Catalog Management
* Product Listing API
* Product Detail API

### Order Service

* Add Products to Cart
* Update Cart Quantity
* Remove Items from Cart
* Checkout Selected Items
* Order History
* Order Status Tracking
* JWT Protected Endpoints

### Frontend Service

* Product Browsing
* Cart Management
* Checkout Flow
* Order Tracking UI

### Infrastructure

* Dockerized Microservices
* Docker Compose Orchestration
* Nginx Reverse Proxy
* Internal Service Networking
* Persistent User Storage using Docker Volumes

---

#  System Architecture

Client Browser
|
v
Nginx Reverse Proxy
|
+-------------------------------+
| | |
v v v
Auth Service Product Service Order Service
(8001) (8002) (8003)
|
v
Frontend Service (8004)

---

## Architecture Principles

### Loose Coupling

Each service is independently deployable and responsible for a single business domain.

### High Cohesion

Each microservice owns its own logic and data.

### Stateless APIs

Communication happens through REST APIs using HTTP requests.

### Service Isolation

Services run in separate Docker containers.

---

#  Technology Stack

## Backend

* Python 3.12
* Django
* Django REST Framework

## Authentication

* JWT (SimpleJWT)

## Frontend

* Django Templates
* HTML
* CSS
* JavaScript

## Infrastructure

* Docker
* Docker Compose
* Nginx

## Database

* SQLite

## Version Control

* Git
* GitHub

---

#  Authentication Flow

### Login

Endpoint:

POST /api/auth/login/

Request:

```json
{
  "username": "paul",
  "password": "Paul@15"
}
```

Response:

```json
{
  "id": 1,
  "username": "paul",
  "role": "customer",
  "access": "JWT_ACCESS_TOKEN",
  "refresh": "JWT_REFRESH_TOKEN"
}
```

### Using Protected APIs

Header:

```text
Authorization: Bearer <access_token>
```

Example:

```bash
curl http://localhost/api/orders/history/1/ \
-H "Authorization: Bearer <access_token>"
```

---

#  Product Workflow

### 1. User Login

User authenticates through Auth Service.

↓

### 2. Product Browsing

Frontend retrieves products from Product Service.

↓

### 3. Add to Cart

Order Service creates a cart item:

```json
{
  "product_id": 1,
  "quantity": 2
}
```

Status:

```text
cart
```

↓

### 4. Checkout

Selected cart items are converted to:

```text
placed
```

↓

### 5. Order History

User views previously ordered items.

Endpoint:

```text
GET /api/orders/history/<user_id>/
```

---

#  Cart Lifecycle

```text
cart
  ↓
placed
  ↓
shipped
  ↓
delivered
```

Current implementation supports:

* cart
* placed

Future versions will support:

* shipped
* delivered

---

#  API Endpoints

## Authentication Service

### Login

```http
POST /api/auth/login/
```

### Register

```http
POST /api/auth/register/
```

---

## Product Service

### Get Products

```http
GET /api/products/
```

### Product Details

```http
GET /api/products/<id>/
```

---

## Order Service

### Add To Cart

```http
POST /api/orders/
```

### View Cart

```http
GET /api/cart/
```

### Update Cart Item

```http
PUT /api/cart/update/<order_id>/
```

### Remove Cart Item

```http
DELETE /api/cart/<order_id>/
```

### Checkout

```http
POST /api/checkout/<user_id>/
```

### Order History

```http
GET /api/orders/history/<user_id>/
```

---

#  Database Design

Order Model

| Field      | Description                         |
| ---------- | ----------------------------------- |
| id         | Order ID                            |
| user_id    | User Reference                      |
| product_id | Product Reference                   |
| quantity   | Product Quantity                    |
| status     | cart / placed / shipped / delivered |

---

#  Docker Deployment

## Start All Services

```bash
docker compose up --build -d
```

---

## Stop Services

```bash
docker compose down
```

---

## Restart Service

```bash
docker compose restart auth-service
```

---

## View Logs

```bash
docker logs auth-service

docker logs product-service

docker logs order-service
```

---

#  Persistent Storage

Auth Service uses a Docker Volume to persist user data.

docker-compose.yml

```yaml
volumes:
  - auth_db:/app/data
```

Benefits:

* User accounts survive container restarts
* User accounts survive image rebuilds
* SQLite database remains persistent

Verified through:

```bash
docker compose down
docker compose up --build -d
```

without losing users.

---

#  Testing the System

### Login

```bash
curl -X POST http://localhost/api/auth/login/ \
-H "Content-Type: application/json" \
-d '{
  "username":"paul",
  "password":"Paul@15"
}'
```

---

### Add Product To Cart

```bash
curl -X POST http://localhost/api/orders/ \
-H "Authorization: Bearer <token>" \
-H "Content-Type: application/json" \
-d '{
  "product_id":1,
  "quantity":2
}'
```

---

### Checkout

```bash
curl -X POST http://localhost/api/checkout/1/ \
-H "Authorization: Bearer <token>" \
-H "Content-Type: application/json" \
-d '{
  "items":[37]
}'
```

---

### Order History

```bash
curl http://localhost/api/orders/history/1/ \
-H "Authorization: Bearer <token>"
```

---

#  Challenges Solved

During development several real-world issues were identified and resolved:

### Authentication

* JWT token validation issues
* Expired token debugging
* Cross-service authentication testing

### Docker

* Persistent SQLite storage
* Docker Volume configuration
* Container rebuild debugging

### Backend

* API endpoint mismatches
* Cart status inconsistencies
* Order lifecycle management
* Frontend-backend integration bugs

### Infrastructure

* Nginx reverse proxy routing
* Docker networking
* Service communication

---

#  What I Learned

This project helped me gain practical experience with:

* Microservices Architecture
* Django REST Framework
* JWT Authentication
* Docker & Docker Compose
* Nginx Reverse Proxy
* REST API Design
* Persistent Storage
* Backend System Design
* Service Isolation
* API Debugging
* Production-style Development Workflow

---

#  Future Improvements

Planned enhancements:

* PostgreSQL Migration
* Redis Caching
* RabbitMQ Event Messaging
* Kubernetes Deployment
* Swagger / OpenAPI Documentation
* Automated Testing
* GitHub Actions CI/CD Pipeline
* Prometheus Monitoring
* Grafana Dashboards
* AWS Deployment (EC2 + RDS + Nginx)
* Role-Based Authorization
* Payment Gateway Integration

---

#  Author

Amit Kumar Yadav

Backend Developer | Python | Django | Django REST Framework | Docker | REST APIs | Microservices

GitHub:
https://github.com/Amit-NCI/furniture-microservices.git

LinkedIn:
https://www.linkedin.com/in/amit-kumar-yadav-70117392/
