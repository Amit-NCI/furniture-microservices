# Furniture E-Commerce Platform — Microservices Architecture

A production-hardened, Dockerized microservices e-commerce platform built with **Python, Django REST Framework, JWT Authentication, Gunicorn, Nginx, and Docker Compose**.

This project is being actively developed in phases, moving from a working prototype toward a production-grade system with PostgreSQL, RabbitMQ event-driven messaging, CI/CD, Prometheus/Grafana observability, and AWS deployment via Terraform.

> **Active development** — commits are ongoing. See the [Roadmap](#roadmap) section for what's built and what's next.

---

## Architecture

```
Browser
   │
   ▼
Nginx (port 80) ── single entry point, routes by path
   │
   ├── /              ──► Frontend Service  (port 8004)  Django Templates + JS
   ├── /api/auth/     ──► Auth Service      (port 8001)  JWT login/register
   ├── /api/products/ ──► Product Service   (port 8002)  Catalog + staff CRUD
   └── /api/orders/   ──► Order Service     (port 8003)  Cart + checkout
       /api/cart/
       /api/checkout/
```

**Key architectural decision:** The browser calls backend services directly via `fetch()` through Nginx — the Frontend service only serves HTML/CSS/JS. There is no server-side API proxying through Frontend. This keeps the frontend stateless and the API surface clean.

**JWT verification:** Order and Product services verify tokens locally using a shared signing key — no network call to Auth service required. This is stateless by design; moving to RS256 (asymmetric) is planned for Phase 3.

Each service has its own isolated SQLite database (PostgreSQL migration is Phase 2).

---

## Services

| Service | Port | Responsibility | Auth Required |
|---|---|---|---|
| Auth | 8001 | Registration, login, JWT issuance, role management | No (public endpoints) |
| Product | 8002 | Product catalog, staff CRUD | GET: any authenticated user; POST/PUT/DELETE: staff only |
| Order | 8003 | Cart, checkout, order history | Yes — JWT on all endpoints |
| Frontend | 8004 | Serves HTML/CSS/JS pages | No |
| Nginx | 80 | Reverse proxy, single entry point | — |

---

## Phase 1 — Production Hardening ✅ Complete

The v1 prototype had real security and operational problems. Phase 1 fixed them before adding any new features.

**What was wrong:**
- `DEBUG = True` in all services — would leak stack traces in production
- `SECRET_KEY` hardcoded and committed — and shared between Auth and Order services
- `CORS_ALLOW_ALL_ORIGINS = True` — wide open
- `python manage.py runserver` in Docker containers — single-threaded dev server, not suitable for any real load
- Containers running as root
- Internal service ports exposed directly on the host — bypassing Nginx
- `psycopg2-binary` in every `requirements.txt` despite the project using SQLite

**What was fixed:**
- All secrets moved to `.env` files loaded via `python-decouple` — never committed, per-service
- Unique `SECRET_KEY` per service — Auth and Order no longer share a key
- Dedicated `JWT_SIGNING_KEY` for token signing/verification, separate from Django's secret
- `DEBUG=False`, `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` restricted per service
- `runserver` replaced with **Gunicorn** (2 workers) in all four services
- Multi-stage Dockerfiles — builder stage installs dependencies, runtime stage is lean
- Containers run as non-root `appuser`
- Internal service ports removed from host exposure — only `nginx:80` is reachable externally
- Custom `JWTTokenAuthentication` in Product and Order services — reads user claims from token payload directly, no cross-service database lookup
- `IsStaffUser` and `IsCustomerOrStaff` permission classes in Product service
- `.env.example` files committed for all services so anyone cloning knows what variables are needed

---

## Roadmap

| Phase | Status | What it adds |
|---|---|---|
| 1 — Production hardening | Complete | Secrets, gunicorn, non-root containers, JWT token-only auth |
| 2 — PostgreSQL | Completed | One Postgres DB per service, proper migrations, Order model improvements |
| 3 — Event-driven messaging | Complete | RabbitMQ: Order service publishes `order.placed`, Product service consumes and decrements stock |
| 4 — Testing | ⏳ Planned | pytest, pylint, SonarQube quality gate, 80%+ coverage |
| 5 — CI/CD | ⏳ Planned | GitHub Actions: lint → test → scan → build → push to ECR → deploy |
| 6 — AWS + Terraform | ⏳ Planned | VPC, ECS Fargate, RDS, ECR, Secrets Manager — all provisioned via Terraform |
| 7 — Observability | ⏳ Planned | Prometheus metrics endpoint per service, Grafana dashboard |

---

## Local Development

### Prerequisites

- Docker Desktop
- Python 3.12 (for local key generation only)

### Setup

**1. Clone the repo:**
```bash
git clone https://github.com/Amit-NCI/furniture-microservices.git
cd furniture-microservices
```

**2. Create `.env` files for each service** (see `.env.example` in each service folder):

Generate a unique secret key for each service:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

Run it 5 times — one `SECRET_KEY` per service, one shared `JWT_SIGNING_KEY` for auth/order/product.

**`auth-service/.env`**
```
SECRET_KEY=your-unique-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,auth-service,nginx
CORS_ALLOWED_ORIGINS=http://localhost,http://127.0.0.1
JWT_SIGNING_KEY=your-shared-jwt-key-here
```

**`order-service/.env`** and **`product-service/.env`** follow the same pattern — include `JWT_SIGNING_KEY` (must match auth-service).

**`frontend/.env`** — same pattern, no `JWT_SIGNING_KEY` needed.

**3. Build and start:**
```bash
docker compose up --build
```

**4. Create a user:**
```bash
docker exec -it auth-service sh -c "cd auth_service && python manage.py shell -c \"
from users.models import User
User.objects.create_user(username='paul', password='Paul@15', role='customer', is_approved=True)
print('User created')
\""
```

**5. Test the system:**
```bash
# Login and capture token
TOKEN=$(curl -s -X POST http://localhost/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "paul", "password": "Paul@15"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access'])")

# Browse products
curl -s http://localhost/api/products/ -H "Authorization: Bearer $TOKEN"

# Add to cart
curl -s -X POST http://localhost/api/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2}'

# Order history
curl -s http://localhost/api/orders/history/2/ -H "Authorization: Bearer $TOKEN"
```

---

## API Reference

### Auth Service

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | No | Register new user |
| POST | `/api/auth/login/` | No | Login, returns JWT access + refresh tokens |

### Product Service

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/products/` | Customer or Staff | List all products |
| GET | `/api/products/<id>/` | No | Product detail |
| POST | `/api/products/` | Staff only | Create product |
| PUT | `/api/products/update/<id>/` | Staff only | Update product |
| DELETE | `/api/products/delete/<id>/` | Staff only | Delete product |

### Order Service

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/orders/` | Yes | Add item to cart |
| GET | `/api/cart/` | Yes | View cart |
| POST | `/api/cart/update/<id>/` | Yes | Update quantity |
| DELETE | `/api/cart/<id>/` | Yes | Remove cart item |
| POST | `/api/cart/remove-selected/<user_id>/` | Yes | Remove selected items |
| DELETE | `/api/cart/clear/<user_id>/` | Yes | Clear entire cart |
| POST | `/api/checkout/<user_id>/` | Yes | Checkout selected items |
| GET | `/api/orders/history/<user_id>/` | Yes | Order history |

---

## Order Status Lifecycle

```
cart → placed → shipped → delivered
```

`cart` and `placed` are implemented. `shipped` and `delivered` are planned for Phase 3 when order events drive status updates.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | Django 6, Django REST Framework |
| Authentication | SimpleJWT (HS256 → RS256 in Phase 3) |
| Server | Gunicorn |
| Proxy | Nginx |
| Containers | Docker, Docker Compose |
| Database | SQLite (→ PostgreSQL in Phase 2) |
| Secrets | python-decouple + .env files |
| Version Control | Git, GitHub |

**Coming in later phases:** PostgreSQL, RabbitMQ, pytest, pylint, SonarQube, GitHub Actions, Terraform, AWS ECS/Fargate, RDS, ECR, Prometheus, Grafana

---

## Docker Commands

```bash
# Build and start all services
docker compose up --build

# Run in background
docker compose up --build -d

# Stop all services
docker compose down

# View logs for a specific service
docker logs auth-service
docker logs product-service
docker logs order-service
docker logs frontend

# Restart a single service
docker compose restart auth-service
```

---

## Security Notes

- `.env` files are gitignored — never committed
- Each service has a unique `SECRET_KEY`
- JWT signing uses a dedicated `JWT_SIGNING_KEY` separate from Django's secret
- Product and Order services verify JWTs without any database lookup (token payload only)
- Only Nginx on port 80 is exposed to the host — internal services are network-isolated
- All containers run as non-root `appuser`
- `DEBUG=False` in all services

---

## Author

**Amit Kumar Yadav**
MSc Cloud Computing — National College of Ireland, Dublin

Cloud & DevOps Engineer | Python · Django · Docker · Kubernetes · AWS · Terraform · Microservices

- GitHub: [github.com/Amit-NCI](https://github.com/Amit-NCI)
- LinkedIn: [linkedin.com/in/amit-kumar-yadav-70117392](https://www.linkedin.com/in/amit-kumar-yadav-70117392/)