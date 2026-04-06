# 🛋️ Furniture E-Commerce Microservices System

## 📌 Project Summary
This project is a **microservices-based e-commerce application** designed to simulate a real-world online furniture store.  
It demonstrates how independent services communicate via REST APIs to handle authentication, product management, cart operations, and order processing.

The system is built using **Django, Django REST Framework, and JavaScript**, following modern backend architecture practices.

---

## 🎯 Key Highlights

- Designed using **Microservices Architecture**
- Built **independent backend services**
- Implemented **REST API communication**
- Developed **complete cart & checkout system**
- Created **order lifecycle tracking (cart → placed → shipped → delivered)**
- Debugged real-world issues like:
  - API mismatches
  - Status inconsistencies
  - Frontend-backend integration bugs

---

## 🏗️ System Architecture
User (Browser)
↓
Frontend Service (Django + JS) [Port 8004]
↓
┌───────────────┬───────────────┬───────────────┐
↓ ↓ ↓
Auth Service Product Service Order Service
(8001) (8002) (8003)


### Architecture Principles:
- **Loose Coupling** – Each service is independent  
- **High Cohesion** – Each service has a single responsibility  
- **Stateless APIs** – Communication via HTTP requests  

---

## ⚙️ Microservices Breakdown

### 🔐 Auth Service (Port 8001)
- Handles user registration and login
- Stores user credentials
- Returns user data for session handling

---

### 📦 Product Service (Port 8002)
- Manages product catalog
- Provides product details via API
- Used by frontend to display items

---

### 🛒 Order Service (Port 8003)
- Core business logic of the application
- Handles:
  - Add to cart
  - Remove from cart
  - Update quantity
  - Checkout process
  - Order history
  - Order status tracking

---

### 🌐 Frontend Service (Port 8004)
- Built using Django templates + JavaScript
- Responsible for:
  - Rendering UI
  - Calling backend APIs
  - Managing user session (localStorage)

---

## 🔄 Application Workflow

### 1. User Authentication
- User registers/logs in via Auth Service
- User data stored in browser (localStorage)

---

### 2. Product Browsing
- Frontend fetches products from Product Service
- Displays product catalog

---

### 3. Cart Management
- User adds items → stored in Order Service (status = `cart`)
- User can:
  - Remove items
  - Update quantity
  - Select items for checkout

---

### 4. Checkout Process
- Selected cart items are converted to `placed`
- Order Service updates database
- Frontend redirects to order page

---

### 5. Order Tracking
- Orders are fetched using: /api/orders/history/<user_id>/

**Status displayed dynamically:**
- 🟡 Pending  
- 🔵 Shipped  
- 🟢 Delivered  

---

## 📡 API Design (Sample)

### Create Order / Add to Cart
POST /api/orders/:

```json
{
  "user_id": 1,
  "product_id": 2,
  "quantity": 1,
  "status": "cart"
}
Checkout: POST /api/checkout/<user_id>/
Order History: GET /api/orders/history/<user_id>/

Database Design:
| Field      | Description                         |
| ---------- | ----------------------------------- |
| id         | Order ID                            |
| user_id    | User reference                      |
| product_id | Product reference                   |
| quantity   | Quantity                            |
| status     | cart / placed / shipped / delivered |

===================================================
Tech Stack

Backend: Django, Django REST Framework

Frontend: HTML, CSS, JavaScript

Database: SQLite

Architecture: Microservices

Communication: REST APIs
=======================

How to Run Locally:          -------Start all services:
----------------------------------------------------------

# Auth Service
cd auth-service
python manage.py runserver 8001

# Product Service
cd product-service
python manage.py runserver 8002

# Order Service
cd order-service
python manage.py runserver 8003

# Frontend
cd frontend
python manage.py runserver 8004
==================================
Challenges Solved
==================================
Fixed 404 API errors due to wrong endpoints

Solved undefined user ID issue

Fixed status mismatch (placed vs ordered)

Implemented cart item deletion API

Built dynamic order tracking UI

Debugged frontend-backend JSON issues:
====================

## 🌟 What I Learned

- Designing scalable microservices systems  
- Handling API communication between services  
- Debugging real-world integration issues  
- Managing state between frontend and backend  
- Building complete end-to-end applications  