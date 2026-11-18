# Furniture E-Commerce Platform

**A containerized, event-driven microservices project developed as a practical Cloud, DevOps and Site Reliability Engineering portfolio.**

[GitHub repository](https://github.com/Amit-NCI/furniture-microservices) · [Docker Hub images](https://hub.docker.com/u/amitky15)

> **Project status (November 2026):** The application runs locally using Docker Compose; automated backend and frontend Django tests have passed; GitHub Actions has successfully tested and published four application images to Docker Hub. AWS infrastructure has been provisioned using Terraform, and an EC2 deployment configuration is being prepared. **The current release has not yet been deployed and functionally verified on EC2.**

## 1. Project overview

This project explores how to design, test, package and operate an e-commerce application as independently deployed services rather than one monolithic application. It combines application engineering (authentication, product management, carts and orders) with infrastructure and operational concerns (separate databases, asynchronous messaging, CI, container image publishing, health checks and cloud deployment).

### Architecture

```text
                         Customer / admin browser
                                   |
                              HTTP :80
                                   |
                                 Nginx
                                   |
          +------------------------+-----------------------+
          |                        |                       |
      Frontend                 API routing            Static assets
    Django + JS                    |
                     +-------------+-------------+
                     |             |             |
                  Auth API     Product API     Order API
                     |             |             |
                Auth PostgreSQL  Product DB   Order PostgreSQL
                                   ^             |
                                   |             | order.placed
                           Product consumer <--- RabbitMQ
                           (separate process)
```

Nginx routes `/` to the frontend, `/api/auth/` to authentication, `/api/products/` to products, and order/cart/checkout APIs to the Order service. The Auth, Product and Order services each own a PostgreSQL database. JWTs issued by Auth are checked by other services. The Order service publishes `order.placed` events; the Product consumer processes them to update inventory.

The frontend is a Django-rendered website with JavaScript interactions; it is not an additional API gateway.

### Components

| Component | Responsibility | Implementation |
| --- | --- | --- |
| Auth service | Registration, login, JWT issuance, user roles and approval checks | Django REST Framework, PostgreSQL |
| Product service | Catalogue, product APIs, restricted product administration | Django REST Framework, PostgreSQL |
| Order service | Cart, order creation, checkout, order history and idempotency safeguards | Django REST Framework, PostgreSQL |
| Frontend | Shopping pages, cart, checkout preparation and management interface | Django templates, JavaScript, CSS |
| RabbitMQ | Asynchronous `order.placed` messages | RabbitMQ |
| Product consumer | Processes order events independently of HTTP workers | Django management command |
| Nginx | Single HTTP entry point, reverse proxy and static assets | Nginx |

The normal Compose deployment has **nine active services** (three databases, RabbitMQ, four application services and Nginx). A **tenth service**, `product-consumer`, is defined under the optional `consumer-migration` profile. It uses the Product image and runs `python manage.py consume_orders`; it is a separate process, **not a new business microservice**. Consumer activation and migration must be coordinated to avoid running two inventory consumers unintentionally.

## 2. Implemented application features

### Customer experience

- User registration, login and JWT-based authentication.
- Product browsing and product detail endpoints.
- Shopping cart: add items, update quantities, remove selected items, clear cart and review totals.
- Selected-item checkout and order history.
- Buy Now preview and substantial client-side retry/idempotency preparation.

**Important Buy Now limitation:** The README's documented development history states that final Buy Now order submission remains intentionally disabled pending deployment and safety verification. Its idempotency helpers and tests should not be interpreted as a live, end-to-end purchase flow.

### Administration

- Product service admin APIs for listing, creating, editing and deleting products.
- JWT role enforcement for the dedicated admin product endpoints; customer and staff roles are not accepted by those admin endpoints.
- Input validation for prices, quantities, protected fields and nonexistent products.
- Frontend management dashboard, login and product-management pages have been added to the repository, with dedicated Django tests. Their behavior has been verified in tests, **not yet through a public EC2 deployment**.

### Event-driven inventory

The Order service publishes `order.placed` messages to RabbitMQ, and the Product service includes a stock-update consumer. The consumer has also been extracted into a dedicated Django management command to allow it to run separately from Gunicorn HTTP workers. Event-processing reliability, redelivery and duplicate-event behavior should be verified before describing the system as fully production-ready.

## 3. Order idempotency and failure handling

Order creation supports an optional `Idempotency-Key` header. The backend associates the key with a user and request details, uses an atomic database transaction and a unique constraint, and is designed to:

- Return the same order for an identical retry.
- Reject reuse of a key with different product/quantity details (HTTP 409).
- Prevent competing requests from committing duplicate idempotency records.
- Avoid leaving an extra committed order after a failed transaction.

**Database deployment caveat:** Migration `orders.0004_orderidempotencykey` was exercised against a disposable PostgreSQL environment. The recorded development history explicitly says it **has not been applied to the live database**. This must be reconciled and verified before enabling the Buy Now submission flow or upgrading an existing deployment.

The frontend Buy Now helpers use `crypto.randomUUID()` and `sessionStorage` to associate a checkout attempt with its user and product. They track prepared, pending and confirmed states, preserve unresolved attempts across refreshes, reject malformed state, and block duplicate requests after uncertain outcomes. Regression tests cover HTTP 400/401/403/409 responses, browser storage failures, state persistence and confirmed-order recovery. These are defensive mechanisms, not a guarantee of exactly-once execution.

## 4. Automated testing and verification

### Latest verified service test runs

The following results were captured from local Docker Compose test executions after the latest application changes:

| Service | Command | Passing tests | Coverage reported |
| --- | --- | ---: | ---: |
| Frontend | `docker compose run --rm --no-deps frontend python manage.py test ui` | **44** | Not reported by this command |
| Auth | `docker compose run --rm --no-deps auth-service python -m pytest tests/ -q` | **14** | **77.38%** (70% minimum) |
| Order | `docker compose run --rm --no-deps order-service python -m pytest tests/ -q` | **56** | **79.57%** (60% minimum) |
| Product | `docker compose run --rm --no-deps product-service python -m pytest tests/ -q` | **58** | **80.90%** (60% minimum) |
| **Total** | **Four verified runs** | **172 passed** | **Not a combined coverage figure** |

The historical README also records separate frontend JavaScript regression suites and disposable-PostgreSQL transaction/concurrency tests. Their counts varied as the test suite evolved; they are **not added to the 172-test total**, because they were not all rerun together in the latest verification.

### Reliability scenarios covered during development

- Duplicate idempotency keys, retries with changed request details and concurrent order-creation requests.
- PostgreSQL unique-constraint and rollback behavior in an isolated test database.
- JWT authentication and permission enforcement.
- Product administration validation and role restrictions.
- Checkout attempt recovery, failed browser-storage writes and HTTP error handling.
- Django frontend management routes and product forms.

**Scope:** Passing automated tests do not establish that the application has passed full browser-based end-to-end testing on AWS. Tests involving a disposable database do not prove that migrations are safe to apply to an existing database without a backup and migration plan.

## 5. CI and Docker image delivery

GitHub Actions workflow: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

On pushes and pull requests to `main`, a matrix job installs dependencies and runs Pylint and pytest for **Auth, Order and Product**. On a successful push to `main`, a downstream matrix builds and pushes four images to Docker Hub using Docker Buildx and GitHub Actions secrets. The latest observed workflow run for commit `f26067a` showed all three lint/test jobs and all four image publishing jobs successful.

| Image | Docker Hub repository |
| --- | --- |
| Auth | [`amitky15/furniture-auth-service`](https://hub.docker.com/r/amitky15/furniture-auth-service) |
| Order | [`amitky15/furniture-order-service`](https://hub.docker.com/r/amitky15/furniture-order-service) |
| Product | [`amitky15/furniture-product-service`](https://hub.docker.com/r/amitky15/furniture-product-service) |
| Frontend | [`amitky15/furniture-frontend`](https://hub.docker.com/r/amitky15/furniture-frontend) |

Images are tagged with `latest` and the source commit SHA. The verified images use `linux/amd64`, compatible with the x86_64 EC2 instance. The Product consumer reuses the Product image with a different command; no fifth application image is required.

**Pipeline boundaries:** The workflow currently publishes images but does **not** deploy them to EC2 automatically. Frontend Django tests were run locally; they are not currently part of the three-service GitHub Actions test matrix. The pipeline should therefore be described as **CI plus automated image publishing**, rather than complete continuous deployment.

## 6. Scenario-wise engineering roadmap

This project is organized as a sequence of independently verifiable engineering scenarios. A scenario is marked complete only when the relevant implementation and checks have been performed.

| Scenario | Engineering focus | Current status | Evidence / next milestone |
| --- | --- | --- | --- |
| **1 — Local microservices** | Docker Compose, service isolation, PostgreSQL, RabbitMQ, Nginx, customer workflows | **Implemented and locally tested** | Compose configuration, application code and local tests |
| **2 — Quality and delivery** | Unit/regression tests, JWT and idempotency checks, GitHub Actions, Docker Hub | **Implemented; ongoing improvement** | 172 latest verified tests; successful CI and four image pushes |
| **3 — AWS infrastructure and EC2 deployment** | Terraform-managed EC2/networking, production Compose override, image pull, runtime configuration | **In progress** | Existing `t3.medium` EC2 provisioned and stopped; deployment not yet verified |
| **4 — AWS functional and security validation** | Browser flows, health checks, migrations, backups, security groups, logs and recovery | **Planned** | Verify the running stack and document test evidence |
| **5 — Kubernetes and Helm** | Deployments, Services, Ingress, ConfigMaps, Secrets, probes and scaling | **Planned** | Local Kubernetes first, then cloud orchestration as appropriate |
| **6 — Observability and SRE** | Metrics, dashboards, alerts, SLI/SLO, incident response and failure testing | **Planned** | Prometheus/Grafana and reliability exercises |
| **7 — Azure platform engineering** | Azure networking, compute, identity, monitoring and later AKS | **Planned** | Reuse the application to compare cloud deployment patterns |

### Scenario 3: AWS deployment details

The existing infrastructure was managed with Terraform in `eu-west-1`. The instance was resized in place from `t3.micro` to `t3.medium` (2 vCPU, 4 GiB RAM), with a 30 GiB gp3 root volume. The last verified instance state was **stopped**. Security group checks showed public HTTP (`80`), HTTPS (`443`) and SSH (`22`) restricted to a single IPv4 `/32`; there was no public RabbitMQ management (`15672`) ingress. Opening `443` does not itself mean TLS has been configured.

The production Compose override (`docker-compose.prod.yml`) selects the four published images by commit SHA, disables local application builds and configures the separate Product consumer image. It requires `EC2_PUBLIC_HOST` at deployment time and sets `DEBUG=False` for application services. At the time of this README update, this override had been created and validated locally but was awaiting inclusion in Git.

The Nginx configuration bind-mounts `nginx/nginx.conf` and the frontend static directory. These files must exist on the deployment host, which is why the deployment requires more than simply pulling container images. The EC2 bootstrap script installs Docker and Compose, but does not automatically clone the application or start the stack.

**Before starting EC2:** arrange deployment files, ignored environment files and secret delivery; confirm the current public hostname and `ALLOWED_HOSTS`; plan database migrations and persistent volumes; and verify the consumer activation strategy. Running EC2 and retaining EBS storage may incur AWS charges.

## 7. Technology stack

| Area | Technologies |
| --- | --- |
| Backend | Python 3.12, Django, Django REST Framework |
| Frontend | Django templates, HTML, CSS, JavaScript |
| Authentication | JWT / SimpleJWT, role-based authorization |
| Data | PostgreSQL 16, SQLite-backed frontend state where configured |
| Messaging | RabbitMQ, Django management-command consumer |
| Runtime | Gunicorn, Nginx, Docker, Docker Compose |
| Quality | Django TestCase, pytest, coverage, Pylint, PostgreSQL integration testing |
| Delivery | Git, GitHub Actions, Docker Buildx, Docker Hub |
| Infrastructure | AWS EC2, VPC/security groups, Terraform |
| Planned | Kubernetes, Helm, Prometheus, Grafana, Azure |

## 8. Run locally

**Prerequisites:** Docker with Compose and Git. Use local test data only.

```bash
git clone https://github.com/Amit-NCI/furniture-microservices.git
cd furniture-microservices
```

Create the required service `.env` files from the relevant `.env.example` templates. Set independent Django `SECRET_KEY` values, a consistent dedicated `JWT_SIGNING_KEY` for JWT issuers/verifiers, appropriate PostgreSQL and RabbitMQ credentials, and valid allowed hosts/origins. Never commit actual `.env` files or private keys. To generate a random secret locally:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(50))'
```

Start the development stack:

```bash
docker compose up --build -d
docker compose ps
```

Open **http://localhost**. For troubleshooting:

```bash
docker compose logs --tail=100 order-service
```

Stop containers without deleting persistent data:

```bash
docker compose down
```

**Data warning:** `docker compose down -v` deletes Compose-managed named volumes. Do not run destructive commands against data you need to retain. The `product-consumer` service is profile-gated and should not be enabled alongside another active consumer until the migration plan is verified.

### Run the verified test suites

```bash
docker compose run --rm --no-deps frontend python manage.py test ui
docker compose run --rm --no-deps auth-service python -m pytest tests/ -q
docker compose run --rm --no-deps order-service python -m pytest tests/ -q
docker compose run --rm --no-deps product-service python -m pytest tests/ -q
```

These are the commands used for the recorded results; some tests depend on the project's local configuration and test fixtures.

## 9. API reference

Routes are accessed through Nginx. Authorization and request body requirements vary by endpoint.

| Method | Route | Purpose |
| --- | --- | --- |
| POST | `/api/auth/register/` | Register |
| POST | `/api/auth/login/` | Obtain JWT |
| GET | `/api/products/` | List products |
| GET | `/api/products/<id>/` | Product details |
| POST | `/api/products/` | Create product (restricted) |
| PUT | `/api/products/update/<id>/` | Update product (restricted) |
| DELETE | `/api/products/delete/<id>/` | Delete product (restricted) |
| GET / POST | `/api/products/admin/` | Admin product listing / creation |
| PUT / DELETE | `/api/products/admin/<id>/` | Admin product update / deletion |
| POST | `/api/orders/` | Create order; optional idempotency key |
| GET | `/api/cart/` | View cart |
| POST | `/api/cart/update/<id>/` | Change quantity |
| DELETE | `/api/cart/<id>/` | Remove item |
| POST | `/api/cart/remove-selected/<user_id>/` | Remove selected items |
| DELETE | `/api/cart/clear/<user_id>/` | Clear cart |
| POST | `/api/checkout/<user_id>/` | Checkout selected cart items |
| GET | `/api/orders/history/<user_id>/` | Order history |

For the most current route definitions, consult the Django `urls.py` files in each service and `nginx/nginx.conf`.

## 10. Security, limitations and next validation

Security measures implemented or configured include ignored local secret files, separate JWT signing configuration, `DEBUG` and allowed-host settings, non-root application containers, multi-stage Dockerfiles, JWT role checks and reduced external port exposure. The GitHub Actions workflow uses repository secrets to authenticate to Docker Hub.

This is a learning and portfolio system, **not a security-audited production commerce service**. Known validation gaps include live migration rollout, complete browser-based EC2 functional testing, HTTPS/TLS configuration, reliable secret delivery, backups/restore testing, consumer redelivery behavior, full monitoring/alerting and automated rollback. Do not use real payment details or customer data for demonstrations.

## 11. Engineering lessons

The main technical lessons have been that service boundaries create operational responsibilities: databases must be isolated, messages require careful consumer behavior, retries need durable idempotency safeguards, and successful unit tests do not replace database concurrency or end-to-end deployment testing. Building the GitHub Actions and Docker Hub pipeline also separates **producing a deployable artifact** from **proving that artifact works on cloud infrastructure**.

## Author

**Amit Kumar Yadav**
MSc Cloud Computing, National College of Ireland, Dublin
[GitHub](https://github.com/Amit-NCI) · [LinkedIn](https://www.linkedin.com/in/amit-kumar-yadav-70117392/)
