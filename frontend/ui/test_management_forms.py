"""Tests for administrator product form validation."""

from django.test import SimpleTestCase

from .management_forms import ManagementProductForm


class ManagementProductFormTests(SimpleTestCase):

    def valid_data(self):
        return {
            "name": "Office Chair",
            "description": "Comfortable ergonomic office chair",
            "price": "129.99",
            "image_url": "https://example.com/chair.jpg",
            "stock_quantity": "10",
        }

    def test_valid_product_data(self):
        form = ManagementProductForm(data=self.valid_data())

        self.assertTrue(form.is_valid(), form.errors)

    def test_negative_price_rejected(self):
        data = self.valid_data()
        data["price"] = "-10.00"

        form = ManagementProductForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_negative_stock_rejected(self):
        data = self.valid_data()
        data["stock_quantity"] = "-1"

        form = ManagementProductForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("stock_quantity", form.errors)

    def test_invalid_image_url_rejected(self):
        data = self.valid_data()
        data["image_url"] = "javascript:alert(1)"

        form = ManagementProductForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("image_url", form.errors)

    def test_product_name_length_limit(self):
        data = self.valid_data()
        data["name"] = "A" * 256

        form = ManagementProductForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_valid_payload_conversion(self):
        form = ManagementProductForm(data=self.valid_data())

        self.assertTrue(form.is_valid())

        payload = form.to_api_payload()

        self.assertEqual(payload["name"], "Office Chair")
        self.assertEqual(payload["price"], "129.99")
        self.assertEqual(payload["stock_quantity"], 10)
        self.assertEqual(
            payload["image_url"],
            "https://example.com/chair.jpg",
        )

        self.assertNotIn("created_at", payload)
        self.assertNotIn("updated_at", payload)

    def test_invalid_form_cannot_create_payload(self):
        data = self.valid_data()
        data["price"] = "-5.00"

        form = ManagementProductForm(data=data)

        with self.assertRaises(ValueError):
            form.to_api_payload()
