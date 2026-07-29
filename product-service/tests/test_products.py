from unittest.mock import MagicMock
import sys

sys.modules['pika'] = MagicMock()

import pytest
from django.urls import path, include
from rest_framework.test import APIClient
from products.models import Product


def get_urls():
    from products.views import ProductList, ProductDetail, ProductUpdate, ProductDelete
    return [
        path('api/products/', ProductList.as_view()),
        path('api/products/<int:pk>/', ProductDetail.as_view()),
        path('api/products/update/<int:pk>/', ProductUpdate.as_view()),
        path('api/products/delete/<int:pk>/', ProductDelete.as_view()),
    ]


class MockTokenUser:
    def __init__(self, role='customer'):
        self.id = 1
        self.role = role
        self.is_authenticated = True
        self.is_active = True


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def product(db):
    return Product.objects.create(
        name='Test Chair',
        description='A comfortable chair',
        price='149.99',
        image_url='https://example.com/chair.jpg',
        stock_quantity=20,
    )


@pytest.fixture
def customer_client(client):
    client.force_authenticate(user=MockTokenUser(role='customer'))
    return client


@pytest.fixture
def staff_client(client):
    client.force_authenticate(user=MockTokenUser(role='staff'))
    return client


# ============================================================
# PRODUCT LIST TESTS
# ============================================================

@pytest.mark.django_db
@pytest.mark.urls('tests.test_products')
class TestProductList:

    def test_customer_can_list_products(self, customer_client, product):
        response = customer_client.get('/api/products/')
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['name'] == 'Test Chair'

    def test_product_list_returns_stock_quantity(self, customer_client, product):
        response = customer_client.get('/api/products/')
        assert response.status_code == 200
        assert response.data[0]['stock_quantity'] == 20

    def test_unauthenticated_cannot_list_products(self, client):
        response = client.get('/api/products/')
        assert response.status_code == 401

    def test_staff_can_create_product(self, staff_client):
        response = staff_client.post('/api/products/', {
            'name': 'New Table',
            'description': 'Oak dining table',
            'price': '299.99',
            'image_url': 'https://example.com/table.jpg',
            'stock_quantity': 5,
        }, format='json')
        assert response.status_code == 201
        assert response.data['name'] == 'New Table'
        assert Product.objects.filter(name='New Table').exists()

    def test_customer_cannot_create_product(self, customer_client):
        response = customer_client.post('/api/products/', {
            'name': 'Sneaky Product',
            'description': 'Should not be created',
            'price': '9.99',
            'image_url': 'https://example.com/x.jpg',
            'stock_quantity': 1,
        }, format='json')
        assert response.status_code == 403


# ============================================================
# PRODUCT DETAIL TESTS
# ============================================================

@pytest.mark.django_db
@pytest.mark.urls('tests.test_products')
class TestProductDetail:

    def test_anyone_can_get_product_detail(self, client, product):
        response = client.get(f'/api/products/{product.id}/')
        assert response.status_code == 200
        assert response.data['name'] == 'Test Chair'
        assert response.data['price'] == '149.99'

    def test_product_detail_not_found(self, client):
        response = client.get('/api/products/99999/')
        assert response.status_code == 404


# ============================================================
# STOCK QUANTITY TESTS
# ============================================================

@pytest.mark.django_db
class TestStockQuantity:

    def test_stock_defaults_to_zero(self, db):
        product = Product.objects.create(
            name='No Stock',
            description='Test',
            price='10.00',
            image_url='https://example.com/x.jpg',
        )
        assert product.stock_quantity == 0

    def test_stock_can_be_decremented(self, product):
        product.stock_quantity -= 5
        product.save()
        product.refresh_from_db()
        assert product.stock_quantity == 15

    def test_created_at_is_set(self, product):
        assert product.created_at is not None

    def test_updated_at_changes_on_save(self, product):
        original = product.updated_at
        product.stock_quantity = 99
        product.save()
        product.refresh_from_db()
        assert product.updated_at >= original


# ============================================================
# URL patterns for @pytest.mark.urls
# ============================================================
urlpatterns = get_urls()