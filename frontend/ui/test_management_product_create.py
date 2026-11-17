"""Tests for the administrator Create Product view."""

import base64
import json
from datetime import timedelta
from unittest.mock import patch

from cryptography.fernet import Fernet
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import ManagementAuthToken


class ManagementProductCreateTests(TestCase):

    def setUp(self):
        self.url = reverse("management-product-create")
        self.product_data = {
            "name": "Office Chair",
            "description": "Ergonomic office chair",
            "price": "129.99",
            "image_url": "https://example.com/chair.jpg",
            "stock_quantity": "10",
        }

    def authenticate_admin(self, verify):
        payload = {
            "exp": int(
                (timezone.now() + timedelta(minutes=30)).timestamp()
            ),
            "token_type": "access",
        }

        encoded = base64.urlsafe_b64encode(
            json.dumps(payload).encode("utf-8")
        ).rstrip(b"=").decode("ascii")

        token = f"test-header.{encoded}.test-signature"

        verify.return_value = {
            "id": 1,
            "username": "testadmin",
            "role": "admin",
            "access_token": token,
        }

        response = self.client.post(
            "/management/authenticate/",
            {
                "username": "testadmin",
                "password": "test-password",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ManagementAuthToken.objects.count(), 1)

        return token

    def test_anonymous_get_forbidden(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    @patch("ui.management_products.request_admin_products")
    def test_anonymous_post_forbidden(self, request_products):
        response = self.client.post(
            self.url,
            self.product_data,
        )

        self.assertEqual(response.status_code, 403)
        request_products.assert_not_called()

    @patch("ui.views.verify_admin_credentials")
    def test_verified_admin_can_open_form(self, verify):
        with patch.dict(
            "os.environ",
            {
                "MANAGEMENT_TOKEN_ENCRYPTION_KEY":
                    Fernet.generate_key().decode("ascii")
            },
        ):
            self.authenticate_admin(verify)

            response = self.client.get(self.url)

            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(
                response,
                "management/product_form.html",
            )
            self.assertContains(response, "Create Product")

    @patch("ui.views.verify_admin_credentials")
    @patch("ui.management_products.request_admin_products")
    def test_invalid_product_rejected(
        self,
        request_products,
        verify,
    ):
        with patch.dict(
            "os.environ",
            {
                "MANAGEMENT_TOKEN_ENCRYPTION_KEY":
                    Fernet.generate_key().decode("ascii")
            },
        ):
            self.authenticate_admin(verify)

            invalid = self.product_data.copy()
            invalid["price"] = "-10.00"

            response = self.client.post(self.url, invalid)

            self.assertEqual(response.status_code, 400)
            self.assertIn("price", response.context["form"].errors)
            request_products.assert_not_called()

    @patch("ui.views.verify_admin_credentials")
    @patch("ui.management_products.request_admin_products")
    def test_valid_product_forwarded_to_service(
        self,
        request_products,
        verify,
    ):
        with patch.dict(
            "os.environ",
            {
                "MANAGEMENT_TOKEN_ENCRYPTION_KEY":
                    Fernet.generate_key().decode("ascii")
            },
        ):
            token = self.authenticate_admin(verify)

            request_products.return_value = {
                "id": 42,
                "name": "Office Chair",
            }

            response = self.client.post(
                self.url,
                self.product_data,
            )

            self.assertRedirects(
                response,
                reverse("management-products"),
                fetch_redirect_response=False,
            )

            request_products.assert_called_once()

            args, kwargs = request_products.call_args

            self.assertEqual(args[0], token)
            self.assertEqual(kwargs["method"], "POST")
            self.assertEqual(
                kwargs["data"]["name"],
                "Office Chair",
            )
            self.assertEqual(
                kwargs["data"]["price"],
                "129.99",
            )
            self.assertEqual(
                kwargs["data"]["stock_quantity"],
                10,
            )

            self.assertNotIn(
                token,
                response.content.decode("utf-8"),
            )
