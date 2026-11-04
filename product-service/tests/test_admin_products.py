import pytest
from rest_framework.test import APIClient

from products.models import Product
from tests.test_products import MockTokenUser


@pytest.fixture
def admin_client():
    client = APIClient()
    client.force_authenticate(user=MockTokenUser(role="admin"))
    return client


@pytest.mark.django_db
@pytest.mark.urls("product_service.urls")
class TestAdminProductList:

    def test_admin_can_list_products(self, admin_client):
        Product.objects.create(
            name="Admin Test Chair",
            description="Test product",
            price="149.99",
            image_url="https://example.com/chair.jpg",
            stock_quantity=10,
        )

        response = admin_client.get("/api/products/admin/")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Admin Test Chair"

    @pytest.mark.parametrize("role", ["customer", "staff"])
    def test_non_admin_cannot_list_products(self, role):
        client = APIClient()
        client.force_authenticate(user=MockTokenUser(role=role))

        response = client.get("/api/products/admin/")

        assert response.status_code == 403

    def test_unauthenticated_cannot_list_products(self):
        client = APIClient()

        response = client.get("/api/products/admin/")

        assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.urls("product_service.urls")
class TestAdminProductCreation:

    @staticmethod
    def valid_product():
        return {
            "name": "Admin Test Desk",
            "description": "Office desk",
            "price": "249.99",
            "image_url": "https://example.com/desk.jpg",
            "stock_quantity": 12,
        }

    def test_admin_can_create_product(self, admin_client):
        response = admin_client.post(
            "/api/products/admin/",
            self.valid_product(),
            format="json",
        )

        assert response.status_code == 201
        assert Product.objects.count() == 1
        assert Product.objects.get().name == "Admin Test Desk"

    @pytest.mark.parametrize("role", ["customer", "staff"])
    def test_non_admin_cannot_create_product(self, role):
        client = APIClient()
        client.force_authenticate(user=MockTokenUser(role=role))

        response = client.post(
            "/api/products/admin/",
            self.valid_product(),
            format="json",
        )

        assert response.status_code == 403
        assert Product.objects.count() == 0

    def test_unauthenticated_cannot_create_product(self):
        response = APIClient().post(
            "/api/products/admin/",
            self.valid_product(),
            format="json",
        )

        assert response.status_code == 401
        assert Product.objects.count() == 0

    @pytest.mark.parametrize("field,value", [
        ("price", "-1.00"),
        ("stock_quantity", -1),
    ])
    def test_rejects_negative_price_or_stock(
        self, admin_client, field, value
    ):
        payload = self.valid_product()
        payload[field] = value

        response = admin_client.post(
            "/api/products/admin/",
            payload,
            format="json",
        )

        assert response.status_code == 400
        assert Product.objects.count() == 0

    def test_rejects_client_controlled_timestamps(self, admin_client):
        payload = self.valid_product()
        payload["created_at"] = "2000-01-01T00:00:00Z"
        payload["updated_at"] = "2000-01-01T00:00:00Z"

        response = admin_client.post(
            "/api/products/admin/",
            payload,
            format="json",
        )

        assert response.status_code == 400
        assert Product.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.urls("product_service.urls")
class TestAdminProductUpdate:

    @pytest.fixture
    def product(self):
        return Product.objects.create(
            name="Original Desk",
            description="Original description",
            price="199.99",
            image_url="https://example.com/desk.jpg",
            stock_quantity=10,
        )

    def test_admin_can_update_product(self, admin_client, product):
        response = admin_client.put(
            f"/api/products/admin/{product.id}/",
            {"name": "Updated Desk", "stock_quantity": 20},
            format="json",
        )

        assert response.status_code == 200
        product.refresh_from_db()
        assert product.name == "Updated Desk"
        assert product.stock_quantity == 20

    @pytest.mark.parametrize("role", ["customer", "staff"])
    def test_non_admin_cannot_update_product(self, role, product):
        client = APIClient()
        client.force_authenticate(user=MockTokenUser(role=role))

        response = client.put(
            f"/api/products/admin/{product.id}/",
            {"name": "Unauthorized Change"},
            format="json",
        )

        assert response.status_code == 403
        product.refresh_from_db()
        assert product.name == "Original Desk"

    def test_unauthenticated_cannot_update_product(self, product):
        response = APIClient().put(
            f"/api/products/admin/{product.id}/",
            {"name": "Unauthorized Change"},
            format="json",
        )

        assert response.status_code == 401
        product.refresh_from_db()
        assert product.name == "Original Desk"

    @pytest.mark.parametrize("field,value", [
        ("price", "-10.00"),
        ("stock_quantity", -5),
    ])
    def test_rejects_negative_values(
        self, admin_client, product, field, value
    ):
        response = admin_client.put(
            f"/api/products/admin/{product.id}/",
            {field: value},
            format="json",
        )

        assert response.status_code == 400
        product.refresh_from_db()
        assert product.stock_quantity == 10
        assert str(product.price) == "199.99"

    def test_rejects_client_controlled_fields(self, admin_client, product):
        response = admin_client.put(
            f"/api/products/admin/{product.id}/",
            {"created_at": "2000-01-01T00:00:00Z"},
            format="json",
        )

        assert response.status_code == 400

    def test_missing_product_returns_404(self, admin_client):
        response = admin_client.put(
            "/api/products/admin/999999/",
            {"name": "Missing Product"},
            format="json",
        )

        assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.urls("product_service.urls")
class TestAdminProductDeletion:

    @pytest.fixture
    def product(self):
        return Product.objects.create(
            name="Delete Test Desk",
            description="Product for deletion tests",
            price="129.99",
            image_url="https://example.com/delete-desk.jpg",
            stock_quantity=5,
        )

    def test_admin_can_delete_product(self, admin_client, product):
        response = admin_client.delete(
            f"/api/products/admin/{product.id}/"
        )

        assert response.status_code == 200
        assert not Product.objects.filter(pk=product.id).exists()

    @pytest.mark.parametrize("role", ["customer", "staff"])
    def test_non_admin_cannot_delete_product(self, role, product):
        client = APIClient()
        client.force_authenticate(user=MockTokenUser(role=role))

        response = client.delete(
            f"/api/products/admin/{product.id}/"
        )

        assert response.status_code == 403
        assert Product.objects.filter(pk=product.id).exists()

    def test_unauthenticated_cannot_delete_product(self, product):
        response = APIClient().delete(
            f"/api/products/admin/{product.id}/"
        )

        assert response.status_code == 401
        assert Product.objects.filter(pk=product.id).exists()

    def test_missing_product_returns_404(self, admin_client):
        response = admin_client.delete(
            "/api/products/admin/999999/"
        )

        assert response.status_code == 404
