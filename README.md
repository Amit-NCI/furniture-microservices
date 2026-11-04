# Furniture E-Commerce Platform

A furniture shopping application built with Python, Django REST Framework, PostgreSQL, RabbitMQ, Docker, and Nginx. I started this project to learn how the different parts of an e-commerce system work together when they are built as separate services.

The project is still in development. The main shopping flows are working, and I am now focusing on testing, reliability, and preparing the application for cloud deployment.

## How the application works

The application has four services:

- **Auth service:** Handles user registration, login, JWT tokens, and user roles.
- **Product service:** Manages the furniture catalogue and staff-only product changes.
- **Order service:** Handles shopping carts, checkout, and order history.
- **Frontend service:** Serves the pages and JavaScript used by customers.

Nginx provides one entry point for the application. The browser sends API requests through Nginx, which forwards each request to the correct service. The frontend serves the website; it does not act as another API proxy.

```text
Browser
   |
   v
Nginx (port 80)
   |
   +-- /               --> Frontend (port 8004)
   +-- /api/auth/      --> Auth (port 8001)
   +-- /api/products/  --> Product (port 8002)
   +-- /api/orders/    --> Order (port 8003)
   +-- /api/cart/      --> Order (port 8003)
   +-- /api/checkout/  --> Order (port 8003)

Auth, Product and Order each have their own PostgreSQL database.
Order publishes order events to RabbitMQ; Product consumes them.
```

The Auth service issues JWTs. The Product and Order services check the tokens locally, without making a database request to Auth for every API call.

## What is implemented

### Shopping features

- User registration and login.
- JWT-based authentication and role-based access.
- Product browsing and staff-only product management.
- Add to cart, update quantities, remove items, and clear the cart.
- Checkout for selected cart items and order history.
- A Buy Now preview page that shows the selected product before checkout.

**Buy Now is not enabled for placing orders yet.** The frontend intentionally blocks the final Buy Now submission while its backend reliability checks are being completed.

### Django migration verification

I also tested the Order service's Django migrations against a disposable PostgreSQL 16.14 database. Django connected successfully using the isolated `django_idempotency_test` schema, and all migrations completed, including `orders.0004_orderidempotencykey`.

This test did not change the live database. The new idempotency migration has not been deployed. Django API concurrency tests have since passed against the same disposable PostgreSQL environment.

### PostgreSQL and order safety

Each backend service uses its own PostgreSQL database. The Order service stores order details, including product information and the price at the time of purchase.

I have also added an idempotency-key mechanism to the Order service. An optional `Idempotency-Key` request header lets the backend recognise a repeated order-creation request from the same user. A repeated key with the same product and quantity should return the original order ID. Reusing that key with a different product or quantity is rejected.

The implementation uses a database unique constraint and an atomic transaction to avoid saving an extra order when two requests compete for the same key.

The idempotency logic has passed the current backend and disposable PostgreSQL integration tests. Migration `0004_orderidempotencykey.py` has **not** been applied to the live PostgreSQL database. Buy Now submission remains disabled until the deployment and remaining safety checks are completed.

### Messaging with RabbitMQ

The Order service publishes an `order.placed` event when an order is placed. The Product service consumes order events to update stock. This allows the services to communicate without the Order service directly changing the Product database.

### Security and deployment improvements

- Application secrets are kept in local `.env` files, with `.env.example` files provided for setup.
- JWT signing uses a dedicated key, separate from each service's Django secret key.
- Debug mode and allowed hosts/origins are controlled through configuration.
- Gunicorn runs the Django applications in Docker instead of Django's development server.
- Application containers run as a non-root user.
- Nginx is the external entry point; backend service ports are not published directly to the host.
- Multi-stage Docker builds are used for the application images.

These measures improve the setup, but the project should not be treated as a fully audited production deployment.

## Testing

Testing is an important part of this project because order and checkout bugs can affect customer data.

The latest verified results are:

| Check | Result |
| --- | --- |
| Order-service backend tests | 56 passed |
| Frontend JavaScript tests | 19 passed |
| PostgreSQL duplicate-key rollback scenario | Passed |
| PostgreSQL simultaneous-transaction scenario | Passed |
| Django endpoint concurrency against PostgreSQL | Passed in disposable database |
| Django endpoint retry and conflict checks | Passed in disposable database |
| Django endpoint concurrent conflicting requests | Passed in disposable database |

The PostgreSQL checks ran in a separate disposable database, not against customer data. They confirmed that the unique constraint prevents two competing transactions from committing duplicate idempotency records, and that a failed transaction does not leave behind an extra committed order.

I also tested the actual Django order-creation endpoint against the disposable PostgreSQL database. Two simultaneous requests with the same user, product, quantity, and idempotency key both returned HTTP 200 and the same order ID. PostgreSQL committed one order and one idempotency record.

Retrying the same request returned the original order ID. Reusing the key with a different product or quantity returned HTTP 409 without creating another order. In a separate concurrent test, two requests used the same key but different quantities. One returned HTTP 200, the other returned HTTP 409, and only the successful request's order was committed.

After these checks, I reran the Order service regression suite: all 56 backend tests passed. The previously verified frontend suite also passed all 19 tests, giving 75 passing automated tests in total. These tests do not mean the idempotency feature has been deployed to the live database.

## Technology used

| Area | Tools |
| --- | --- |
| Backend | Python 3.12, Django 6, Django REST Framework |
| Frontend | Django templates, HTML, CSS, JavaScript |
| Authentication | JWT / SimpleJWT |
| Database | PostgreSQL 16 |
| Messaging | RabbitMQ |
| Web server and routing | Gunicorn, Nginx |
| Containers | Docker, Docker Compose |
| Testing | pytest, frontend JavaScript tests, PostgreSQL transaction tests |
| Automation | GitHub Actions |
| Planned cloud infrastructure | AWS, Terraform |
| Planned monitoring | Prometheus, Grafana |

## Running the project locally

You will need Docker Desktop and Git. Python is useful for generating local secret values.

1. Clone the repository:

   ```bash
   git clone https://github.com/Amit-NCI/furniture-microservices.git
   cd furniture-microservices
   ```

2. Create the `.env` files required by each service using the matching `.env.example` files. Use different Django `SECRET_KEY` values for each service and the same dedicated `JWT_SIGNING_KEY` wherever JWTs are issued or verified. Configure the database and RabbitMQ settings as shown in the examples.

   You can generate random secret values with:

   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

3. Build and start the services:

   ```bash
   docker compose up --build -d
   ```

4. Open `http://localhost` in your browser.

5. Check container status and logs if a service does not start:

   ```bash
   docker compose ps
   docker compose logs --tail=100 order-service
   ```

To stop the application without deleting database volumes:

```bash
docker compose down
```

**Data safety:** Do not use `docker compose down -v` if you want to keep existing database data. Avoid testing order-creation and checkout endpoints against a database containing real customer records.

## Main API routes

| Method | Route | Purpose |
| --- | --- | --- |
| POST | `/api/auth/register/` | Register a user |
| POST | `/api/auth/login/` | Log in and receive JWT tokens |
| GET | `/api/products/` | List products |
| GET | `/api/products/<id>/` | View a product |
| POST | `/api/products/` | Add a product (staff) |
| PUT | `/api/products/update/<id>/` | Update a product (staff) |
| DELETE | `/api/products/delete/<id>/` | Delete a product (staff) |
| POST | `/api/orders/` | Create a cart order; optional idempotency key is under test |
| GET | `/api/cart/` | View the cart |
| POST | `/api/cart/update/<id>/` | Change quantity |
| DELETE | `/api/cart/<id>/` | Remove an item |
| POST | `/api/cart/remove-selected/<user_id>/` | Remove selected items |
| DELETE | `/api/cart/clear/<user_id>/` | Clear the cart |
| POST | `/api/checkout/<user_id>/` | Check out selected cart items |
| GET | `/api/orders/history/<user_id>/` | View order history |

The order and cart APIs require authentication. Some product operations are restricted to staff users.

## Development roadmap

| Work | Status |
| --- | --- |
| Docker-based services and Nginx routing | Completed |
| Secrets, JWT checks, non-root containers, and Gunicorn | Completed |
| Separate PostgreSQL databases | Completed |
| RabbitMQ order events and stock updates | Completed |
| Automated backend and frontend tests | In place; continuing to expand |
| GitHub Actions CI/CD | Implemented; ongoing improvements |
| Idempotency model, migration, and backend logic | Implemented locally; not deployed |
| PostgreSQL transaction and concurrency checks | Completed in disposable database |
| Django/PostgreSQL integration and concurrent API tests | Completed in disposable database; not deployed |
| Enable Buy Now order submission | Planned after testing |
| AWS deployment using Terraform | Planned |
| Prometheus and Grafana monitoring | Planned |

## What I learned

Building this project has helped me understand how authentication, product data, orders, databases, and messaging fit together in a microservices application. It has also shown me why deployment and testing matter as much as writing an API.

A recent focus has been making order creation safer when users retry requests or when two requests arrive at nearly the same time. I used PostgreSQL transactions and unique constraints to test these situations in an isolated environment before making changes to the running application.

## Author

**Amit Kumar Yadav**
MSc Cloud Computing, National College of Ireland, Dublin

GitHub: [Amit-NCI](https://github.com/Amit-NCI)
LinkedIn: [Amit Kumar Yadav](https://www.linkedin.com/in/amit-kumar-yadav-70117392/)


### Frontend Buy Now idempotency preparation

The Buy Now checkout page now has a helper for preparing an idempotency key.

The helper uses a secure random UUID and stores it in browser session storage.
It reuses the same key when the same user refreshes the checkout page for
the same product. It refuses to reuse a stored attempt for another user or
product. If secure storage or UUID generation is unavailable, it fails
instead of creating an unprotected checkout key.

Three new frontend tests cover page refreshes, different users or products,
and missing secure browser features.

All 24 frontend tests passed. The backend test suite previously passed
56 tests, giving 80 passing automated tests across both suites.

This is preparation only. The helper is not yet connected to the order
creation request, and Buy Now submission remains disabled.

The idempotency database migration has only been tested against disposable
PostgreSQL. It has not been applied to the live database.

### Buy Now idempotency header testing

The Buy Now order-creation helper now includes an `Idempotency-Key` header in its order API request. The key is generated with `crypto.randomUUID()` and stored in `sessionStorage` for the current user, product, and checkout attempt.

The frontend tests verify that the request includes the stored key, the same checkout attempt reuses its key, and repeated calls do not create duplicate requests. They also verify that an invalid user session or unavailable secure storage prevents the order API request.

All 25 frontend tests pass. The backend suite previously passed 56 tests, giving 81 passing tests across both suites.

Buy Now submission is still disabled in the checkout handler. The idempotency database migration has been tested only in disposable PostgreSQL and has not been applied to the live database.


### Buy Now checkout attempt completion

The Buy Now checkout page now includes a helper for clearing a completed
checkout attempt from session storage.

The helper checks the user ID, product ID, and stored idempotency key before
removing the attempt. It refuses to clear an attempt belonging to another
user or product.

This allows a future purchase to receive a new idempotency key after the
previous checkout has been confirmed as completed.

A new frontend regression test checks that another user or product cannot
clear the stored attempt, that a matching attempt can be cleared, and that
a later purchase receives a different key.

All 25 frontend tests passed. The Order service backend suite previously
passed 56 tests, giving 81 passing automated tests across both suites.

The completion helper is not connected to checkout submission yet.
It must only be called after successful checkout has been confirmed.

Buy Now submission remains disabled. The idempotency database migration
has not been applied to the live PostgreSQL database.

### Buy Now checkout state integrity and failure recovery

I added more frontend tests to check how Buy Now handles damaged or
unavailable browser storage.

The checkout now has additional checks for these situations:

- Corrupted checkout data is rejected without creating an order.
- If saving the pending state fails, no order request is sent.
- If saving the confirmed state fails, another order request is blocked.
- Unexpected checkout states are rejected without changing stored data.
- After saving the pending state, the frontend reads it back and checks
  the user ID, product ID, idempotency key, and pending state before
  sending the order request.

These checks help prevent duplicate orders when storage fails or the
checkout page is refreshed.

The frontend checkout test suite now has 34 passing tests. The previously
verified backend regression suite had 56 passing tests. Together, these
represent 90 passing tests across the two suites, although the backend
suite was not rerun as part of this frontend change.

Buy Now order submission remains disabled. The checkout completion
helper is not connected to the submission handler, and the backend
idempotency migration has not been applied to the live database.

No live orders or customer database records were used for these tests.

### Buy Now confirmed-order completion safety

The Buy Now completion helper now refuses to clear a stored idempotency attempt unless the attempt has a confirmed state and a valid positive integer order ID.

This prevents prepared, pending, and invalid confirmed attempts from being cleared prematurely. Keeping unresolved attempts in sessionStorage helps prevent accidental duplicate order creation after a retry or page refresh.

The regression tests verify that:

- Attempts without a confirmed state cannot be cleared.
- Prepared and pending attempts remain stored.
- Confirmed attempts with missing or invalid order IDs remain stored.
- A valid confirmed attempt can be cleared.
- The existing user and product ownership checks continue to work.

Validation: All 40 frontend checkout tests passed, with zero failures.

Buy Now submission remains disabled. The order idempotency migration has not been applied to the live database.

### Buy Now HTTP 401 and 403 authentication retry protection

The Buy Now frontend now includes regression tests for HTTP 401 Unauthorized and HTTP 403 Forbidden responses from the order service.

These responses indicate authentication or permission failures. The frontend rejects order creation without treating the request as successful.

The tests verify that:

- HTTP 401 and HTTP 403 do not produce a confirmed Buy Now order ID.
- The pending idempotency attempt remains stored in sessionStorage.
- Another order-creation request is blocked on the same page.
- A page refresh does not allow another order-creation request.
- Only one mocked order-creation POST is sent for each test.

This milestone adds regression tests only. No production checkout behavior was changed.

Validation: All 39 frontend checkout tests passed, with zero failures.

Buy Now submission remains disabled. The order idempotency migration has not been applied to the live database.

### Buy Now HTTP 409 conflict retry protection

The Buy Now frontend now has a regression test for HTTP 409 Conflict responses from the order service.

The backend returns HTTP 409 when an idempotency key is reused with different order details. The frontend must not treat this response as successful order creation.

The test verifies that:

- An HTTP 409 response does not produce a confirmed Buy Now order ID.
- The pending idempotency attempt remains stored in sessionStorage.
- Another order-creation request is blocked on the same page.
- A page refresh does not allow another order-creation request.
- Only one mocked order-creation POST is sent.

This milestone adds test coverage only. No production checkout behavior was changed.

Validation: All 37 frontend checkout tests passed, with zero failures.

Buy Now submission remains disabled. The order idempotency migration has not been applied to the live database.

### Buy Now HTTP 400 retry protection

Added a frontend regression test for HTTP 400 responses during
Buy Now order creation.

The test verifies that an HTTP 400 response does not report
successful order creation and that the checkout attempt remains
stored as pending.

It also verifies that a second order-creation request is blocked
in the current page and after a simulated page refresh.

The existing frontend implementation already provided this
protection, so no production code changes were necessary.

All 36 frontend checkout tests passed, including the new HTTP 400
regression test. The previously verified backend suite had 56
passing tests, but it was not rerun for this milestone.

Buy Now submission remains disabled, and the backend idempotency
migration has not been applied to the live database.

No live orders or customer database records were used.

### Buy Now confirmed-state persistence verification

The Buy Now order-creation helper now checks that the confirmed order
record was actually saved in browser session storage before reporting
success.

After receiving a valid order ID from the backend, the helper saves
the checkout attempt as confirmed. It then reads the stored record
back and checks the user ID, product ID, idempotency key, confirmed
state, and order ID.

If the confirmed record is missing, corrupted, or does not match,
the helper marks the order-creation outcome as uncertain and blocks
another order-creation attempt.

I added a regression test that simulates browser storage silently
ignoring the confirmed-state write without throwing an error.

All 35 frontend checkout tests passed after the fix. The previously
verified backend suite had 56 passing tests, but it was not rerun
for this frontend milestone.

Buy Now submission remains disabled. The checkout completion helper
is not connected to the submission handler, and the backend
idempotency migration has not been applied to the live database.

No live orders or customer database records were used.

### Buy Now checkout state persistence and page-refresh recovery

The Buy Now order-creation helper now saves the checkout attempt state in
browser session storage.

Before sending an order-creation request, it saves the attempt as `pending`.
This records that the request may have reached the backend. If the page is
refreshed while an attempt is pending, the frontend blocks another order
request instead of risking a duplicate order.

After receiving a valid order ID, the helper saves the attempt as `confirmed`
along with that order ID. If the page is refreshed, the frontend can restore
the confirmed order ID without sending another order-creation request.

The recovery logic checks the stored user ID, product ID, idempotency key,
and order ID. Invalid confirmed order IDs are rejected. The idempotency key
is not removed when an order is created because order creation alone does
not mean checkout has been completed.

The frontend regression tests cover pending attempts after refresh,
confirmed-order recovery, invalid stored order IDs, and duplicate-request
prevention.

The latest frontend suite passed all 29 tests. The Order service backend
suite previously passed all 56 tests, giving 85 passing automated tests
across the two suites.

Buy Now submission remains disabled. The checkout completion helper is not
connected to the submission handler. The backend idempotency migration has
only been tested in disposable PostgreSQL and has not been applied to the
live database. No live orders were created during these frontend tests.

### Admin product management API

The Product service now includes dedicated admin-only endpoints for
managing the furniture product catalogue.

These endpoints use JWT authentication and require the exact `admin`
role. Customer and staff roles cannot access them.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/products/admin/` | List products |
| POST | `/api/products/admin/` | Create a product |
| PUT | `/api/products/admin/<id>/` | Update a product |
| DELETE | `/api/products/admin/<id>/` | Delete a product |

Product creation and updates validate input and reject negative prices
and stock quantities. Client-supplied IDs and server-managed timestamps
are rejected. Updating or deleting a nonexistent product returns HTTP 404.

The existing customer and staff product endpoints remain separate.

#### Admin product API testing

The Product service has 58 passing automated tests, including 24
admin product API tests. The full test suite achieved 87.01% coverage,
exceeding the configured 60% minimum.

Tests cover product listing, creation, editing, deletion, JWT role
restrictions, validation, and missing-product handling.

The tests use an isolated test database and do not modify live
PostgreSQL data.

This milestone implements the backend product management APIs.
The frontend admin dashboard, order management, customer management,
and analytics remain future development work.

Buy Now submission remains disabled. The order idempotency migration
has not been applied to the live database.
