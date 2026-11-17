from django.shortcuts import render


def home(request):
    return render(request, 'home.html')

def dashboard(request):
    return render(request, 'dashboard.html')

# ✅ ADD THIS
def cart_view(request):
    return render(request, 'cart.html')

def orders_view(request):
    return render(request, 'orders.html')


def checkout_view(request):
    return render(request, 'checkout.html')


def management_dashboard(request):
    """Allow access only through a verified administrator session."""
    from django.http import HttpResponseForbidden

    if request.session.get("management_verified_admin") is not True:
        return HttpResponseForbidden(
            "Verified administrator authentication required."
        )

    if request.session.get("management_admin_role") != "admin":
        return HttpResponseForbidden(
            "Administrator access required."
        )

    from django.core import signing

    marker = request.session.get("management_auth_marker")
    admin_id = request.session.get("management_admin_id")

    if not marker or not admin_id:
        return HttpResponseForbidden(
            "Verified administrator session required."
        )

    try:
        signed_id = signing.loads(
            marker,
            salt="furniture-management-admin",
            max_age=3600,
        )
    except signing.BadSignature:
        return HttpResponseForbidden(
            "Invalid administrator session."
        )

    if signed_id != admin_id:
        return HttpResponseForbidden(
            "Invalid administrator session."
        )

    from django.db import DatabaseError
    from django.http import HttpResponse
    from .management_tokens import get_management_token

    try:
        access_token = get_management_token(
            request.session.session_key
        )
    except (DatabaseError, RuntimeError, OSError):
        return HttpResponse(
            "Administrator authentication is temporarily unavailable.",
            status=503,
        )

    if not access_token:
        return HttpResponseForbidden(
            "Administrator authentication has expired."
        )

    return render(request, "management/dashboard.html")


def management_login(request):
    """Display the administrator login page."""
    return render(request, "management/login.html")


def management_authenticate(request):
    """Authenticate administrators and establish a protected session."""
    from django.http import (
        HttpResponseBadRequest,
        HttpResponseForbidden,
        HttpResponseNotAllowed,
        HttpResponse,
    )
    from django.shortcuts import redirect

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")

    if not username or not password:
        return HttpResponseBadRequest(
            "Username and password are required."
        )

    verified_user = verify_admin_credentials(username, password)

    if not verified_user:
        return HttpResponse(
            "Invalid credentials.",
            status=401,
        )

    if verified_user.get("role") != "admin":
        return HttpResponseForbidden(
            "Administrator access required."
        )

    if not verified_user.get("id") or not verified_user.get("username"):
        return HttpResponse(
            "Invalid authentication response.",
            status=401,
        )

    access_token = verified_user.get("access_token")

    if not isinstance(access_token, str) or not access_token:
        return HttpResponse(
            "Invalid authentication response.",
            status=401,
        )

    from django.core import signing
    from django.db import DatabaseError
    from .management_tokens import (
        delete_management_token,
        store_management_token,
    )

    request.session.flush()

    try:
        request.session.create()
        session_key = request.session.session_key

        store_management_token(
            session_key,
            access_token,
        )

        request.session["management_verified_admin"] = True
        request.session["management_admin_role"] = "admin"
        request.session["management_admin_id"] = verified_user["id"]
        request.session["management_admin_username"] = verified_user["username"]

        request.session["management_auth_marker"] = signing.dumps(
            verified_user["id"],
            salt="furniture-management-admin",
        )
        request.session.set_expiry(3600)
        request.session.save()

    except (ValueError, RuntimeError, DatabaseError, OSError):
        if request.session.session_key:
            try:
                delete_management_token(request.session.session_key)
            except DatabaseError:
                pass

        request.session.flush()

        return HttpResponse(
            "Administrator authentication is temporarily unavailable.",
            status=503,
        )

    return redirect("/management/")



def management_logout(request):
    """End the administrator session and remove its stored token."""
    from django.db import DatabaseError
    from django.http import HttpResponse, HttpResponseNotAllowed
    from django.shortcuts import redirect

    from .management_tokens import delete_management_token

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    session_key = request.session.session_key

    try:
        delete_management_token(session_key)
    except DatabaseError:
        return HttpResponse(
            "Administrator logout is temporarily unavailable.",
            status=503,
        )

    request.session.flush()
    return redirect("/management/login/")


def verify_admin_credentials(username, password):
    """Verify administrator credentials with the internal Auth service."""
    import json
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen

    from django.conf import settings

    if not username or not password:
        return None

    auth_url = getattr(
        settings,
        "MANAGEMENT_AUTH_URL",
        "http://auth-service:8001/api/auth/login/",
    )

    payload = json.dumps({
        "username": username,
        "password": password,
    }).encode("utf-8")

    request = Request(
        auth_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=5) as response:
            if response.status != 200:
                return None

            data = json.loads(response.read(16384))

    except (HTTPError, URLError, TimeoutError, ValueError, OSError):
        return None

    if not isinstance(data, dict):
        return None

    if data.get("role") != "admin":
        return None

    admin_id = data.get("id")
    admin_username = data.get("username")
    access_token = data.get("access")

    if type(admin_id) is not int or admin_id <= 0:
        return None

    if not isinstance(admin_username, str) or not admin_username:
        return None

    if not isinstance(access_token, str) or not access_token:
        return None

    return {
        "id": admin_id,
        "username": admin_username,
        "role": "admin",
        "access_token": access_token,
    }


def management_products(request):
    """List products for verified administrators only."""

    from django.db import DatabaseError
    from django.http import (
        HttpResponse,
        HttpResponseForbidden,
        HttpResponseNotAllowed,
        JsonResponse,
    )

    from .management_products import (
        ProductServiceError,
        request_admin_products,
    )
    from .management_tokens import get_management_token

    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    # Reuse the dashboard's complete administrator session validation.
    authorization = management_dashboard(request)

    if authorization.status_code != 200:
        return authorization

    try:
        access_token = get_management_token(
            request.session.session_key
        )

        if not access_token:
            return HttpResponseForbidden(
                "Administrator authentication has expired."
            )

        products = request_admin_products(
            access_token,
            method="GET",
        )

    except (DatabaseError, RuntimeError, OSError):
        return HttpResponse(
            "Administrator authentication is temporarily unavailable.",
            status=503,
        )

    except ProductServiceError as exc:
        return HttpResponse(
            str(exc),
            status=exc.status_code,
        )

    if not isinstance(products, list):
        return HttpResponse(
            "Product Service returned an unexpected response.",
            status=502,
        )

    return render(
        request,
        "management/products.html",
        {"products": products},
        status=200,
    )


def management_product_create(request):
    """Create products through a verified administrator session."""
    from django.db import DatabaseError
    from django.http import (
        HttpResponse,
        HttpResponseForbidden,
        HttpResponseNotAllowed,
    )
    from django.shortcuts import redirect

    from .management_forms import ManagementProductForm
    from .management_products import (
        ProductServiceError,
        request_admin_products,
    )
    from .management_tokens import get_management_token

    if request.method not in {"GET", "POST"}:
        return HttpResponseNotAllowed(["GET", "POST"])

    authorization = management_dashboard(request)

    if authorization.status_code != 200:
        return authorization

    if request.method == "GET":
        return render(
            request,
            "management/product_form.html",
            {"form": ManagementProductForm()},
        )

    form = ManagementProductForm(request.POST)

    if not form.is_valid():
        return render(
            request,
            "management/product_form.html",
            {"form": form},
            status=400,
        )

    try:
        access_token = get_management_token(
            request.session.session_key
        )

        if not access_token:
            return HttpResponseForbidden(
                "Administrator authentication has expired."
            )

        result = request_admin_products(
            access_token,
            method="POST",
            data=form.to_api_payload(),
        )

    except (DatabaseError, RuntimeError, OSError):
        return HttpResponse(
            "Administrator authentication is temporarily unavailable.",
            status=503,
        )

    except ProductServiceError as exc:
        return HttpResponse(
            str(exc),
            status=exc.status_code,
        )

    if not isinstance(result, dict) or not result.get("id"):
        return HttpResponse(
            "Product Service returned an unexpected response.",
            status=502,
        )

    return redirect("management-products")


def management_product_edit(request, product_id):
    """Edit an existing product through a verified administrator session."""
    from django.db import DatabaseError
    from django.http import (
        HttpResponse,
        HttpResponseForbidden,
        HttpResponseNotAllowed,
    )
    from django.shortcuts import redirect

    from .management_forms import ManagementProductForm
    from .management_products import (
        ProductServiceError,
        get_admin_product,
        request_admin_products,
    )
    from .management_tokens import get_management_token

    if request.method not in {"GET", "POST"}:
        return HttpResponseNotAllowed(["GET", "POST"])

    authorization = management_dashboard(request)

    if authorization.status_code != 200:
        return authorization

    try:
        access_token = get_management_token(
            request.session.session_key
        )

        if not access_token:
            return HttpResponseForbidden(
                "Administrator authentication has expired."
            )

    except (DatabaseError, RuntimeError, OSError):
        return HttpResponse(
            "Administrator authentication is temporarily unavailable.",
            status=503,
        )

    if request.method == "GET":
        try:
            product = get_admin_product(access_token, product_id)
        except ProductServiceError as exc:
            return HttpResponse(
                str(exc),
                status=exc.status_code,
            )

        form = ManagementProductForm(initial={
            "name": product.get("name", ""),
            "description": product.get("description", ""),
            "price": product.get("price", ""),
            "image_url": product.get("image_url", ""),
            "stock_quantity": product.get("stock_quantity", 0),
        })

        return render(
            request,
            "management/product_form.html",
            {
                "form": form,
                "editing": True,
                "product_id": product_id,
            },
        )

    form = ManagementProductForm(request.POST)

    if not form.is_valid():
        return render(
            request,
            "management/product_form.html",
            {
                "form": form,
                "editing": True,
                "product_id": product_id,
            },
            status=400,
        )

    try:
        result = request_admin_products(
            access_token,
            method="PUT",
            product_id=product_id,
            data=form.to_api_payload(),
        )
    except ProductServiceError as exc:
        return HttpResponse(
            str(exc),
            status=exc.status_code,
        )

    if not isinstance(result, dict) or result.get("id") != product_id:
        return HttpResponse(
            "Product Service returned an unexpected response.",
            status=502,
        )

    return redirect("management-products")


def management_product_delete(request, product_id):
    """Delete a product only after verified administrator confirmation."""
    from django.db import DatabaseError
    from django.http import (
        HttpResponse,
        HttpResponseForbidden,
        HttpResponseNotAllowed,
    )
    from django.shortcuts import redirect

    from .management_products import (
        ProductServiceError,
        get_admin_product,
        request_admin_products,
    )
    from .management_tokens import get_management_token

    if request.method not in {"GET", "POST"}:
        return HttpResponseNotAllowed(["GET", "POST"])

    authorization = management_dashboard(request)

    if authorization.status_code != 200:
        return authorization

    try:
        access_token = get_management_token(
            request.session.session_key
        )

        if not access_token:
            return HttpResponseForbidden(
                "Administrator authentication has expired."
            )

    except (DatabaseError, RuntimeError, OSError):
        return HttpResponse(
            "Administrator authentication is temporarily unavailable.",
            status=503,
        )

    if request.method == "GET":
        try:
            product = get_admin_product(access_token, product_id)
        except ProductServiceError as exc:
            return HttpResponse(
                str(exc),
                status=exc.status_code,
            )

        return render(
            request,
            "management/product_confirm_delete.html",
            {"product": product},
        )

    try:
        result = request_admin_products(
            access_token,
            method="DELETE",
            product_id=product_id,
        )
    except ProductServiceError as exc:
        return HttpResponse(
            str(exc),
            status=exc.status_code,
        )

    if not isinstance(result, dict) or result.get("message") != "Product deleted.":
        return HttpResponse(
            "Product Service returned an unexpected response.",
            status=502,
        )

    return redirect("management-products")
