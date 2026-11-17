"""Access-control tests for the administrator product listing."""

import base64
import json
from datetime import timedelta
from unittest.mock import patch

from cryptography.fernet import Fernet
from django.test import TestCase
from django.utils import timezone

from .models import ManagementAuthToken


class ManagementProductViewTests(TestCase):

    def test_anonymous_visitor_cannot_access_products(self):
        response = self.client.get("/management/products/")

        self.assertEqual(response.status_code, 403)

    def test_product_listing_rejects_post_requests(self):
        response = self.client.post("/management/products/")

        self.assertEqual(response.status_code, 405)

    @patch("ui.views.verify_admin_credentials")
    @patch("ui.management_products.urllib.request.build_opener")
    def test_verified_admin_can_list_products(self, build_opener, verify):
        payload = {
            "exp": int(
                (timezone.now() + timedelta(minutes=30)).timestamp()
            ),
            "token_type": "access",
        }

        encoded_payload = base64.urlsafe_b64encode(
            json.dumps(payload).encode("utf-8")
        ).rstrip(b"=").decode("ascii")

        synthetic_token = (
            f"test-header.{encoded_payload}.test-signature"
        )

        verify.return_value = {
            "id": 1,
            "username": "testadmin",
            "role": "admin",
            "access_token": synthetic_token,
        }

        response_data = [
            {
                "id": 1,
                "name": "Office Chair",
                "price": "129.99",
                "stock_quantity": 10,
            }
        ]

        from unittest.mock import Mock

        upstream = Mock()
        upstream.read.return_value = json.dumps(
            response_data
        ).encode("utf-8")

        build_opener.return_value.open.return_value.__enter__.return_value = (
            upstream
        )

        with patch.dict(
            "os.environ",
            {
                "MANAGEMENT_TOKEN_ENCRYPTION_KEY":
                    Fernet.generate_key().decode("ascii")
            },
        ):
            login = self.client.post(
                "/management/authenticate/",
                {
                    "username": "testadmin",
                    "password": "test-password",
                },
            )

            self.assertEqual(login.status_code, 302)
            self.assertEqual(ManagementAuthToken.objects.count(), 1)

            response = self.client.get("/management/products/")

            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(
                response,
                "management/products.html",
            )
            self.assertContains(response, "Office Chair")
            self.assertContains(response, "129.99")
            self.assertContains(response, "10")

            self.assertEqual(
                response.context["products"][0]["name"],
                "Office Chair",
            )

            self.assertNotIn(
                synthetic_token,
                response.content.decode("utf-8"),
            )

            self.assertEqual(
                build_opener.return_value.open.call_count,
                1,
            )
