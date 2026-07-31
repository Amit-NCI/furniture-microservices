import pytest
from django.urls import path
from rest_framework.test import APIClient
from users.models import User


def get_urls():
    from users.views import RegisterView, LoginView
    return [
        path('api/auth/register/', RegisterView.as_view()),
        path('api/auth/login/', LoginView.as_view()),
    ]


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def customer_user(db):
    return User.objects.create_user(
        username='testcustomer',
        password='TestPass@123',
        role='customer',
        is_approved=True,
    )


@pytest.fixture
def staff_user_approved(db):
    return User.objects.create_user(
        username='teststaff',
        password='TestPass@123',
        role='staff',
        is_approved=True,
    )


@pytest.fixture
def staff_user_pending(db):
    return User.objects.create_user(
        username='pendingstaff',
        password='TestPass@123',
        role='staff',
        is_approved=False,
    )


# ============================================================
# REGISTER TESTS
# ============================================================

@pytest.mark.django_db
@pytest.mark.urls('tests.test_auth')
class TestRegister:

    def test_register_customer_success(self, client):
        response = client.post('/api/auth/register/', {
            'username': 'newuser',
            'password': 'NewPass@123',
            'role': 'customer',
        }, format='json')
        assert response.status_code == 201
        assert response.data['username'] == 'newuser'
        assert response.data['role'] == 'customer'
        assert response.data['approved'] is True

    def test_register_staff_starts_unapproved(self, client):
        response = client.post('/api/auth/register/', {
            'username': 'newstaff',
            'password': 'NewPass@123',
            'role': 'staff',
        }, format='json')
        assert response.status_code == 201
        assert response.data['role'] == 'staff'
        assert response.data['approved'] is False

    def test_register_duplicate_username(self, client, customer_user):
        response = client.post('/api/auth/register/', {
            'username': 'testcustomer',
            'password': 'AnotherPass@123',
        }, format='json')
        assert response.status_code == 400
        assert 'already exists' in response.data['error']

    def test_register_missing_username(self, client):
        response = client.post('/api/auth/register/', {
            'password': 'TestPass@123',
        }, format='json')
        assert response.status_code == 400
        assert 'required' in response.data['error']

    def test_register_missing_password(self, client):
        response = client.post('/api/auth/register/', {
            'username': 'newuser',
        }, format='json')
        assert response.status_code == 400
        assert 'required' in response.data['error']


# ============================================================
# LOGIN TESTS
# ============================================================

@pytest.mark.django_db
@pytest.mark.urls('tests.test_auth')
class TestLogin:

    def test_login_customer_success(self, client, customer_user):
        response = client.post('/api/auth/login/', {
            'username': 'testcustomer',
            'password': 'TestPass@123',
        }, format='json')
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert response.data['role'] == 'customer'
        assert response.data['username'] == 'testcustomer'

    def test_login_returns_jwt_tokens(self, client, customer_user):
        response = client.post('/api/auth/login/', {
            'username': 'testcustomer',
            'password': 'TestPass@123',
        }, format='json')
        assert response.status_code == 200
        access = response.data['access']
        assert len(access.split('.')) == 3

    def test_login_wrong_password(self, client, customer_user):
        response = client.post('/api/auth/login/', {
            'username': 'testcustomer',
            'password': 'WrongPassword',
        }, format='json')
        assert response.status_code == 401
        assert 'Invalid credentials' in response.data['error']

    def test_login_nonexistent_user(self, client):
        response = client.post('/api/auth/login/', {
            'username': 'nobody',
            'password': 'TestPass@123',
        }, format='json')
        assert response.status_code == 401

    def test_login_approved_staff_succeeds(self, client, staff_user_approved):
        response = client.post('/api/auth/login/', {
            'username': 'teststaff',
            'password': 'TestPass@123',
        }, format='json')
        assert response.status_code == 200
        assert response.data['role'] == 'staff'

    def test_login_unapproved_staff_blocked(self, client, staff_user_pending):
        response = client.post('/api/auth/login/', {
            'username': 'pendingstaff',
            'password': 'TestPass@123',
        }, format='json')
        assert response.status_code == 403
        assert 'not approved' in response.data['error']

    def test_login_missing_fields(self, client):
        response = client.post('/api/auth/login/', {
            'username': 'testcustomer',
        }, format='json')
        assert response.status_code == 400
        assert 'required' in response.data['error']


# ============================================================
# URL patterns for @pytest.mark.urls
# ============================================================
urlpatterns = get_urls()