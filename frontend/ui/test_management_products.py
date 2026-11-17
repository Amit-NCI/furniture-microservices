"""Security tests for the server-side Product Service client."""

import io
import json
import urllib.error
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from .management_products import (
    ProductServiceError,
    request_admin_products,
)


class ProductServiceClientTests(SimpleTestCase):

    @patch("ui.management_products.urllib.request.build_opener")
    def test_list_products_uses_admin_bearer_token(self, build_opener):
        response = Mock()
        response.read.return_value = json.dumps([
            {"id": 1, "name": "Chair"}
        ]).encode("utf-8")

        opener = build_opener.return_value
        opener.open.return_value.__enter__.return_value = response

        products = request_admin_products("synthetic-admin-token")

        self.assertEqual(products[0]["name"], "Chair")

        request = opener.open.call_args.args[0]

        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(
            request.get_header("Authorization"),
            "Bearer synthetic-admin-token",
        )
        self.assertEqual(
            request.full_url,
            "http://product-service:8002/api/products/admin/",
        )

    @patch("ui.management_products.urllib.request.build_opener")
    def test_product_service_rejects_unauthorized_token(self, build_opener):
        error = urllib.error.HTTPError(
            "http://product-service:8002/api/products/admin/",
            401,
            "Unauthorized",
            {},
            io.BytesIO(b"Unauthorized"),
        )

        build_opener.return_value.open.side_effect = error

        with self.assertRaises(ProductServiceError) as context:
            request_admin_products("synthetic-admin-token")

        self.assertEqual(context.exception.status_code, 403)

    @override_settings(
        MANAGEMENT_PRODUCT_SERVICE_URL="http://untrusted.example/admin/"
    )
    @patch("ui.management_products.urllib.request.build_opener")
    def test_untrusted_service_destination_is_rejected(self, build_opener):
        with self.assertRaises(ProductServiceError) as context:
            request_admin_products("synthetic-admin-token")

        self.assertEqual(context.exception.status_code, 503)
        build_opener.assert_not_called()

    @patch("ui.management_products.urllib.request.build_opener")
    def test_redirect_response_is_rejected(self, build_opener):
        error = urllib.error.HTTPError(
            "http://product-service:8002/api/products/admin/",
            302,
            "Found",
            {"Location": "http://untrusted.example/"},
            io.BytesIO(b""),
        )

        build_opener.return_value.open.side_effect = error

        with self.assertRaises(ProductServiceError) as context:
            request_admin_products("synthetic-admin-token")

        self.assertEqual(context.exception.status_code, 502)

    @patch("ui.management_products.urllib.request.build_opener")
    def test_redirect_handler_disables_redirects(self, build_opener):
        response = Mock()
        response.read.return_value = b"[]"

        build_opener.return_value.open.return_value.__enter__.return_value = response

        request_admin_products("synthetic-admin-token")

        handler = build_opener.call_args.args[0]

        self.assertIsNone(
            handler.redirect_request(
                None,
                None,
                302,
                "Found",
                {},
                "http://untrusted.example/",
            )
        )

    def test_missing_admin_token_is_rejected(self):
        with self.assertRaises(ProductServiceError) as context:
            request_admin_products("")

        self.assertEqual(context.exception.status_code, 401)

    def test_invalid_product_id_is_rejected(self):
        with self.assertRaises(ValueError):
            request_admin_products(
                "synthetic-admin-token",
                method="DELETE",
                product_id=-1,
            )
