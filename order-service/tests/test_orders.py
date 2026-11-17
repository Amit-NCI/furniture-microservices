from unittest.mock import patch, MagicMock
import sys

# Mock pika and the entire publisher/authentication modules
# before any Django imports to prevent connection attempts
sys.modules['pika'] = MagicMock()

import pytest
from django.urls import path
from rest_framework.test import APIClient
from orders.models import Order


# ============================================================
# Minimal URL config for tests — avoids importing all views
# which would trigger pika/RabbitMQ connections
# ============================================================
def get_urls():
    from orders.views import (
        CreateOrder, CartList, Checkout, OrderHistory,
        DeleteCartItem, UpdateQuantity, RemoveSelectedItems,
        ClearCart, GetUserOrders,
    )
    return [
        path('api/orders/', CreateOrder.as_view()),
        path('api/orders/<int:user_id>/', GetUserOrders.as_view()),
        path('api/cart/', CartList.as_view()),
        path('api/checkout/<int:user_id>/', Checkout.as_view()),
        path('api/orders/history/<int:user_id>/', OrderHistory.as_view()),
        path('api/cart/<int:order_id>/', DeleteCartItem.as_view()),
        path('api/cart/update/<int:order_id>/', UpdateQuantity.as_view()),
        path('api/cart/remove-selected/<int:user_id>/', RemoveSelectedItems.as_view()),
        path('api/cart/clear/<int:user_id>/', ClearCart.as_view()),
    ]


class MockTokenUser:
    def __init__(self, user_id=1, role='customer'):
        self.id = user_id
        self.role = role
        self.is_authenticated = True
        self.is_active = True


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def auth_client(client):
    client.force_authenticate(user=MockTokenUser(user_id=1))
    return client


@pytest.fixture
def other_user_client(client):
    client.force_authenticate(user=MockTokenUser(user_id=2))
    return client


@pytest.fixture
def cart_item(db):
    return Order.objects.create(
        user_id=1,
        product_id=1,
        product_name='Test Chair',
        price_at_purchase='149.99',
        quantity=2,
        status='cart',
    )


@pytest.fixture
def placed_order(db):
    return Order.objects.create(
        user_id=1,
        product_id=1,
        product_name='Test Chair',
        price_at_purchase='149.99',
        quantity=1,
        status='placed',
    )


# ============================================================
# CART TESTS
# ============================================================

@pytest.mark.django_db
@pytest.mark.urls('tests.test_orders')
class TestCart:

    def test_add_to_cart(self, auth_client):
        with patch('orders.views.Order') as MockOrder:
            MockOrder.objects.create.return_value = MagicMock(id=123)
            response = auth_client.post('/api/orders/', {
                'product_id': 1,
                'quantity': 3,
            }, format='json')
        assert response.status_code == 200

    def test_view_cart(self, auth_client, cart_item):
        response = auth_client.get('/api/cart/')
        assert response.status_code == 200
        items = response.data
        assert any(item['id'] == cart_item.id for item in items)

    def test_unauthenticated_cannot_view_cart(self, client):
        response = client.get('/api/cart/')
        assert response.status_code in [401, 403]

    def test_increase_quantity(self, auth_client, cart_item):
        response = auth_client.post(
            f'/api/cart/update/{cart_item.id}/',
            {'action': 'increase'},
            format='json',
        )
        assert response.status_code == 200
        cart_item.refresh_from_db()
        assert cart_item.quantity == 3

    def test_decrease_quantity(self, auth_client, cart_item):
        response = auth_client.post(
            f'/api/cart/update/{cart_item.id}/',
            {'action': 'decrease'},
            format='json',
        )
        assert response.status_code == 200
        cart_item.refresh_from_db()
        assert cart_item.quantity == 1

    def test_quantity_cannot_go_below_one(self, auth_client, db):
        item = Order.objects.create(
            user_id=1, product_id=1, quantity=1, status='cart'
        )
        auth_client.post(
            f'/api/cart/update/{item.id}/',
            {'action': 'decrease'},
            format='json',
        )
        item.refresh_from_db()
        assert item.quantity == 1

    def test_delete_cart_item(self, auth_client, cart_item):
        response = auth_client.delete(f'/api/cart/{cart_item.id}/')
        assert response.status_code == 200
        assert not Order.objects.filter(id=cart_item.id).exists()

    def test_cannot_delete_other_users_cart_item(self, other_user_client, cart_item):
        response = other_user_client.delete(f'/api/cart/{cart_item.id}/')
        assert response.status_code == 404
        assert Order.objects.filter(id=cart_item.id).exists()


# ============================================================
# CHECKOUT TESTS
# ============================================================

@pytest.mark.django_db
@pytest.mark.urls('tests.test_orders')
class TestCheckout:

    @patch('orders.views.publish_order_placed')
    def test_checkout_places_order(self, mock_publish, auth_client, cart_item):
        response = auth_client.post(
            '/api/checkout/1/',
            {'items': [cart_item.id]},
            format='json',
        )
        assert response.status_code == 200
        cart_item.refresh_from_db()
        assert cart_item.status == 'placed'

    @patch('orders.views.publish_order_placed')
    def test_checkout_publishes_event(self, mock_publish, auth_client, cart_item):
        auth_client.post(
            '/api/checkout/1/',
            {'items': [cart_item.id]},
            format='json',
        )
        assert mock_publish.called

    @patch('orders.views.publish_order_placed')
    def test_checkout_empty_items_rejected(self, mock_publish, auth_client):
        response = auth_client.post(
            '/api/checkout/1/',
            {'items': []},
            format='json',
        )
        assert response.status_code == 400

    @patch('orders.views.publish_order_placed')
    def test_checkout_nonexistent_items_rejected(self, mock_publish, auth_client):
        response = auth_client.post(
            '/api/checkout/1/',
            {'items': [99999]},
            format='json',
        )
        assert response.status_code == 404

    @patch('orders.views.publish_order_placed')
    def test_checkout_succeeds_even_if_rabbitmq_fails(self, mock_publish, auth_client, cart_item):
        """
        Resilience test: RabbitMQ failure must not affect checkout response.
        Order is placed — event delivery is best-effort.
        """
        mock_publish.side_effect = Exception('RabbitMQ connection refused')
        response = auth_client.post(
            '/api/checkout/1/',
            {'items': [cart_item.id]},
            format='json',
        )
        assert response.status_code == 200
        cart_item.refresh_from_db()
        assert cart_item.status == 'placed'


# ============================================================
# ORDER HISTORY TESTS
# ============================================================

@pytest.mark.django_db
@pytest.mark.urls('tests.test_orders')
class TestOrderHistory:

    def test_history_shows_placed_orders(self, auth_client, placed_order):
        response = auth_client.get('/api/orders/history/1/')
        assert response.status_code == 200
        ids = [o['id'] for o in response.data]
        assert placed_order.id in ids

    def test_history_excludes_cart_items(self, auth_client, cart_item):
        response = auth_client.get('/api/orders/history/1/')
        assert response.status_code == 200
        ids = [o['id'] for o in response.data]
        assert cart_item.id not in ids

    def test_unauthenticated_cannot_view_history(self, client):
        response = client.get('/api/orders/history/1/')
        assert response.status_code in [401, 403]


# ============================================================
# URL patterns for @pytest.mark.urls
# ============================================================
urlpatterns = get_urls()

# ============================================================
# CREATE ORDER SECURITY VALIDATION TESTS
# ============================================================

@pytest.mark.django_db
@pytest.mark.urls('tests.test_orders')
class TestCreateOrderSecurity:

    def test_valid_order_returns_order_id(self, auth_client):
        response = auth_client.post(
            '/api/orders/',
            {'product_id': 1, 'quantity': 2},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['message'] == 'Item added to cart'
        assert isinstance(response.data['order_id'], int)

        order = Order.objects.get(id=response.data['order_id'])

        assert order.user_id == 1
        assert order.product_id == 1
        assert order.quantity == 2
        assert order.status == 'cart'

    @pytest.mark.parametrize(
        'payload',
        [
            {},
            {'quantity': 2},
            {'product_id': None},
            {'product_id': 0},
            {'product_id': -1},
            {'product_id': 'abc'},
            {'product_id': '1'},
            {'product_id': True},
        ],
    )
    def test_invalid_product_id_rejected(self, auth_client, payload):
        before = Order.objects.count()

        response = auth_client.post(
            '/api/orders/',
            payload,
            format='json',
        )

        assert response.status_code == 400
        assert 'error' in response.data
        assert Order.objects.count() == before

    @pytest.mark.parametrize(
        'quantity',
        [
            0,
            -1,
            -5,
            'abc',
            '2',
            None,
            True,
            1.5,
        ],
    )
    def test_invalid_quantity_rejected(self, auth_client, quantity):
        before = Order.objects.count()

        response = auth_client.post(
            '/api/orders/',
            {
                'product_id': 1,
                'quantity': quantity,
            },
            format='json',
        )

        assert response.status_code == 400
        assert 'error' in response.data
        assert Order.objects.count() == before

    @pytest.mark.parametrize(
        'requested_status',
        [
            'placed',
            'shipped',
            'delivered',
        ],
    )
    def test_client_cannot_override_order_status(
        self,
        auth_client,
        requested_status,
    ):
        response = auth_client.post(
            '/api/orders/',
            {
                'product_id': 1,
                'quantity': 1,
                'status': requested_status,
            },
            format='json',
        )

        assert response.status_code == 200

        order = Order.objects.get(id=response.data['order_id'])

        assert order.status == 'cart'

    def test_client_cannot_override_user_id(self, auth_client):
        response = auth_client.post(
            '/api/orders/',
            {
                'user_id': 2,
                'product_id': 1,
                'quantity': 1,
            },
            format='json',
        )

        assert response.status_code == 200

        order = Order.objects.get(id=response.data['order_id'])

        assert order.user_id == 1

    def test_quantity_defaults_to_one(self, auth_client):
        response = auth_client.post(
            '/api/orders/',
            {'product_id': 1},
            format='json',
        )

        assert response.status_code == 200

        order = Order.objects.get(id=response.data['order_id'])

        assert order.quantity == 1

    def test_unauthenticated_cannot_create_order(self, client):
        response = client.post(
            '/api/orders/',
            {
                'product_id': 1,
                'quantity': 1,
            },
            format='json',
        )

        assert response.status_code in (401, 403)
        assert Order.objects.count() == 0
