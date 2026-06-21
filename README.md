#  Furniture E-Commerce Platform (Microservices Architecture)

##  Project Overview

This project is a **Dockerized Microservices-Based E-Commerce Platform** built using **Python, Django REST Framework, JWT Authentication, Docker, Docker Compose, and Nginx**.

The application simulates a real-world online furniture store where users can register, browse products, add items to a cart, and place orders.

The system is designed using **Microservices Architecture**, where each service is responsible for a specific business domain and communicates through REST APIs.

---

#  System Architecture

![System Architecture](screenshots/architecture-diagram.png)

---

##  Application Screenshots

### Login Page

![Login Page](screenshots/login-page.png)

### Product Catalog

![Product Catalog](screenshots/products-page.png)

### Shopping Cart

![Shopping Cart](screenshots/cart-page.png)

### Order History

![Order History](screenshots/order-history-page.png)

---

# Summary

Designed and developed a Dockerized microservices e-commerce platform using Django REST Framework, JWT authentication, Nginx reverse proxy, and Docker Compose.

Implemented authentication, product catalog management, shopping cart functionality, checkout workflow, and order history tracking while applying microservices principles, REST API communication, container orchestration, and persistent storage management.

---

#  Key Features

##  Authentication Service

* User Registration
* User Login
* JWT Authentication
* Access Token & Refresh Token Generation
* User Approval Workflow
* Role-Based Users
* Protected API Access

---

## Product Service

* Product Catalog Management
* Product Listing API
* Product Detail API
* Product Retrieval via REST APIs

---

## Order Service

* Add Products to Cart
* Update Cart Quantity
* Remove Cart Items
* Checkout Selected Items
* Order History Tracking
* JWT Protected Endpoints
* Order Status Management

---

## Frontend Service

* Product Browsing Interface
* Cart Management UI
* Checkout Workflow
* Order Tracking Interface
* Django Templates + JavaScript

---

## Infrastructure

* Dockerized Services
* Docker Compose Orchestration
* Nginx Reverse Proxy
* Internal Docker Networking
* Persistent Storage using Docker Volumes
* Service Isolation

---

# Microservices Breakdown

## Auth Service (Port 8001)

Responsible for:

* Authentication
* User Registration
* JWT Token Generation
* User Approval Workflow
* Role Management

### Technologies

* Django
* Django REST Framework
* SimpleJWT
* SQLite

---

## Product Service (Port 8002)

Responsible for:

* Product Catalog
* Product Listing
* Product Details

### Technologies

* Django
* Django REST Framework
* SQLite

---

## Order Service (Port 8003)

Responsible for:

* Shopping Cart
* Checkout
* Order History
* Order Tracking

### Technologies

* Django
* Django REST Framework
* SQLite

---

## Frontend Service (Port 8004)

Responsible for:

* Rendering User Interface
* Calling Backend APIs
* Managing User Session

### Technologies

* Django Templates
* HTML
* CSS
* JavaScript

---

# Architecture Principles

## Loose Coupling

Each service is independently deployable and owns a single business domain.

## High Cohesion

Business logic is isolated within its respective service.

## Stateless APIs

Services communicate through REST APIs.

## Service Isolation

Every service runs inside its own Docker container.

## Container Orchestration

Docker Compose manages networking and service startup.

---

# Technology Stack

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

# Authentication Flow

## Login Endpoint

```http
POST /api/auth/login/
```

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

---

## Protected APIs

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

#  Application Workflow

## 1. User Login

User authenticates through the Auth Service.

↓

## 2. Browse Products

Frontend retrieves products from Product Service.

↓

## 3. Add To Cart

Order Service stores products with:

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

## 4. Checkout

Selected cart items become:

```text
placed
```

↓

## 5. Order History

Users retrieve previously placed orders.

Endpoint:

```http
GET /api/orders/history/<user_id>/
```

---

# 🛒 Cart Lifecycle

```text
cart
  ↓
placed
  ↓
shipped
  ↓
delivered
```

### Current Implementation

* cart
* placed

### Planned

* shipped
* delivered

---

#  API Endpoints

## Authentication Service

### Register

```http
POST /api/auth/register/
```

### Login

```http
POST /api/auth/login/
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

## Order Model

| Field      | Description                         |
| ---------- | ----------------------------------- |
| id         | Order ID                            |
| user_id    | User Reference                      |
| product_id | Product Reference                   |
| quantity   | Product Quantity                    |
| status     | cart / placed / shipped / delivered |

---

#  Docker Deployment

## Build & Start

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

The Auth Service uses Docker Volumes to persist user data.

docker-compose.yml:

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

## Login

```bash
curl -X POST http://localhost/api/auth/login/ \
-H "Content-Type: application/json" \
-d '{
  "username":"paul",
  "password":"Paul@15"
}'
```

---

## Add Product To Cart

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

## Checkout

```bash
curl -X POST http://localhost/api/checkout/1/ \
-H "Authorization: Bearer <token>" \
-H "Content-Type: application/json" \
-d '{
  "items":[37]
}'
```

---

## Order History

```bash
curl http://localhost/api/orders/history/1/ \
-H "Authorization: Bearer <token>"
```

---

#  Project Metrics

* 4 Independent Services
* JWT Authentication
* Dockerized Deployment
* Nginx Reverse Proxy
* Persistent Storage using Docker Volumes
* End-to-End Cart & Checkout Workflow
* REST API Based Communication
* Microservices Architecture

---

#  Challenges Solved

### Authentication

* JWT Token Validation Issues
* Expired Token Debugging
* Cross-Service Authentication Testing

### Docker

* Persistent SQLite Storage
* Docker Volume Configuration
* Container Rebuild Debugging

### Backend

* API Endpoint Mismatches
* Cart Status Inconsistencies
* Order Lifecycle Management
* Frontend-Backend Integration Bugs

### Infrastructure

* Nginx Reverse Proxy Routing
* Docker Networking
* Service Communication

---

# 📚 Skills Demonstrated

* Python
* Django
* Django REST Framework
* REST API Development
* JWT Authentication
* Docker
* Docker Compose
* Nginx
* SQLite
* Microservices Architecture
* Service-to-Service Communication
* Backend Development
* System Design
* API Testing
* Distributed System Debugging

---

#  Future Improvements

## Infrastructure

* PostgreSQL Migration
* Redis Caching
* RabbitMQ Event Messaging
* Kubernetes Deployment

## DevOps

* GitHub Actions CI/CD
* Automated Testing
* Docker Image Security Scanning

## Monitoring

* Prometheus Metrics
* Grafana Dashboards

## Cloud

* AWS EC2 Deployment
* AWS RDS
* S3 Storage

## Business Features

* Payment Gateway Integration
* Role-Based Authorization
* Product Search & Filtering
* Inventory Management

---

#  Author

**Amit Kumar Yadav**

Backend Developer | Python | Django | Django REST Framework | Docker | REST APIs | Microservices

GitHub:
https://github.com/Amit-NCI/furniture-microservices

LinkedIn:
https://www.linkedin.com/in/amit-kumar-yadav-70117392/
