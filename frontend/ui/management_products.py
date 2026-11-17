"""Server-side client for the Product Service administrator API."""

import json
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from django.conf import settings


class ProductServiceError(Exception):
    """A Product Service request could not be completed safely."""

    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


def request_admin_products(access_token, method="GET", product_id=None, data=None):
    """Call the Product Service without exposing the JWT to the browser."""

    if not isinstance(access_token, str) or not access_token.strip():
        raise ProductServiceError(
            "Administrator authentication required.",
            status_code=401,
        )

    if method not in {"GET", "POST", "PUT", "DELETE"}:
        raise ValueError("Unsupported Product Service operation.")

    if method in {"PUT", "DELETE"}:
        if type(product_id) is not int or product_id <= 0:
            raise ValueError("A valid product ID is required.")
    elif product_id is not None:
        raise ValueError("Product ID is not valid for this operation.")

    if method in {"POST", "PUT"}:
        if not isinstance(data, dict):
            raise ValueError("Product data must be a JSON object.")
    elif data is not None:
        raise ValueError("Unexpected product data.")

    base_url = getattr(
        settings,
        "MANAGEMENT_PRODUCT_SERVICE_URL",
        "http://product-service:8002/api/products/admin/",
    )

    if not isinstance(base_url, str):
        raise ProductServiceError("Product Service configuration is invalid.", 503)

    parsed = urlsplit(base_url)

    if (
        parsed.scheme != "http"
        or parsed.hostname != "product-service"
        or parsed.port != 8002
        or parsed.path.rstrip("/") != "/api/products/admin"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ProductServiceError(
            "Product Service configuration is invalid.",
            status_code=503,
        )

    base_url = base_url.rstrip("/") + "/"

    url = (
        f"{base_url}{product_id}/"
        if product_id is not None
        else base_url
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    payload = None

    if data is not None:
        payload = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=payload,
        headers=headers,
        method=method,
    )

    class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirectHandler())

    try:
        with opener.open(request, timeout=5) as response:
            body = response.read(2_000_001)

            if len(body) > 2_000_000:
                raise ProductServiceError(
                    "Product Service response is too large."
                )

            if not body:
                return None

            return json.loads(body.decode("utf-8"))

    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            raise ProductServiceError(
                "Product Service rejected administrator authorization.",
                status_code=403,
            ) from None

        if exc.code == 404:
            raise ProductServiceError(
                "Product not found.",
                status_code=404,
            ) from None

        if exc.code == 400:
            raise ProductServiceError(
                "Product Service rejected the submitted data.",
                status_code=400,
            ) from None

        raise ProductServiceError(
            "Product Service request failed."
        ) from None

    except (urllib.error.URLError, TimeoutError, OSError):
        raise ProductServiceError(
            "Product Service is temporarily unavailable.",
            status_code=503,
        ) from None

    except (ValueError, UnicodeError):
        raise ProductServiceError(
            "Product Service returned an invalid response."
        ) from None


def get_admin_product(access_token, product_id):
    """Retrieve one product from the protected administrator listing."""

    if type(product_id) is not int or product_id <= 0:
        raise ValueError("A valid product ID is required.")

    products = request_admin_products(
        access_token,
        method="GET",
    )

    if not isinstance(products, list):
        raise ProductServiceError(
            "Product Service returned an unexpected response.",
            status_code=502,
        )

    for product in products:
        if not isinstance(product, dict):
            raise ProductServiceError(
                "Product Service returned an unexpected response.",
                status_code=502,
            )

        if type(product.get("id")) is int and product["id"] == product_id:
            return product

    raise ProductServiceError(
        "Product not found.",
        status_code=404,
    )
