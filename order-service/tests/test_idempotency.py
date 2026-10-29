import pytest

from orders.models import Order
from tests.test_orders import MockTokenUser

from rest_framework.test import APIClient


@pytest.mark.django_db
@pytest.mark.urls('tests.test_orders')
class TestOrderIdempotency:

    def test_repeated_request_returns_original_order(self):
        client = APIClient()
        client.force_authenticate(
            user=MockTokenUser(user_id=1)
        )

        payload = {
            'product_id': 5,
            'quantity': 1,
        }

        headers = {
            'HTTP_IDEMPOTENCY_KEY': 'buy-now-test-key-001',
        }

        first = client.post(
            '/api/orders/',
            payload,
            format='json',
            **headers,
        )

        second = client.post(
            '/api/orders/',
            payload,
            format='json',
            **headers,
        )

        assert first.status_code == 200
        assert second.status_code == 200

        assert first.data['order_id'] == second.data['order_id']

        assert Order.objects.filter(
            user_id=1,
            product_id=5,
        ).count() == 1


@pytest.mark.django_db
@pytest.mark.urls('tests.test_orders')
class TestOrderIdempotencySecurity:

    def test_same_key_different_product_returns_409(self):
        client = APIClient()
        client.force_authenticate(user=MockTokenUser(user_id=1))

        headers = {'HTTP_IDEMPOTENCY_KEY': 'product-conflict-001'}

        first = client.post(
            '/api/orders/',
            {'product_id': 5, 'quantity': 1},
            format='json',
            **headers
        )

        second = client.post(
            '/api/orders/',
            {'product_id': 6, 'quantity': 1},
            format='json',
            **headers
        )

        assert first.status_code == 200
        assert second.status_code == 409
        assert Order.objects.filter(user_id=1).count() == 1

    def test_same_key_different_quantity_returns_409(self):
        client = APIClient()
        client.force_authenticate(user=MockTokenUser(user_id=1))

        headers = {'HTTP_IDEMPOTENCY_KEY': 'quantity-conflict-001'}

        first = client.post(
            '/api/orders/',
            {'product_id': 5, 'quantity': 1},
            format='json',
            **headers
        )

        second = client.post(
            '/api/orders/',
            {'product_id': 5, 'quantity': 2},
            format='json',
            **headers
        )

        assert first.status_code == 200
        assert second.status_code == 409
        assert Order.objects.filter(user_id=1).count() == 1

    def test_same_key_different_users_creates_separate_orders(self):
        client = APIClient()
        headers = {'HTTP_IDEMPOTENCY_KEY': 'shared-key-001'}

        client.force_authenticate(user=MockTokenUser(user_id=1))
        first = client.post(
            '/api/orders/',
            {'product_id': 5, 'quantity': 1},
            format='json',
            **headers
        )

        client.force_authenticate(user=MockTokenUser(user_id=2))
        second = client.post(
            '/api/orders/',
            {'product_id': 5, 'quantity': 1},
            format='json',
            **headers
        )

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.data['order_id'] != second.data['order_id']
        assert Order.objects.count() == 2

    @pytest.mark.parametrize('key', [
        '',
        'x' * 129,
        'invalid\nkey',
        'non-ascii-€',
    ])
    def test_invalid_idempotency_key_returns_400(self, key):
        client = APIClient()
        client.force_authenticate(user=MockTokenUser(user_id=1))

        response = client.post(
            '/api/orders/',
            {'product_id': 5, 'quantity': 1},
            format='json',
            HTTP_IDEMPOTENCY_KEY=key,
        )

        assert response.status_code == 400
        assert Order.objects.count() == 0

    def test_requests_without_key_preserve_existing_behavior(self):
        client = APIClient()
        client.force_authenticate(user=MockTokenUser(user_id=1))

        payload = {'product_id': 5, 'quantity': 1}

        first = client.post('/api/orders/', payload, format='json')
        second = client.post('/api/orders/', payload, format='json')

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.data['order_id'] != second.data['order_id']
        assert Order.objects.filter(user_id=1, product_id=5).count() == 2
