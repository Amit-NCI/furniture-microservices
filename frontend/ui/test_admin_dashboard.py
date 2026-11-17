from unittest.mock import Mock, patch

from django.test import SimpleTestCase, TestCase
from django.urls import resolve


class AdminDashboardRouteTests(SimpleTestCase):

    def test_management_route_exists(self):
        match = resolve("/management/")
        self.assertEqual(match.url_name, "management-dashboard")

    def test_management_dashboard_template_is_not_exposed_anonymously(self):
        response = self.client.get("/management/")
        self.assertEqual(response.status_code, 403)
        self.assertTemplateNotUsed(response, "management/dashboard.html")

    def test_existing_django_admin_route_remains_available(self):
        match = resolve("/admin/")
        self.assertEqual(match.url_name, "index")


class AdminDashboardAccessTests(SimpleTestCase):

    def test_anonymous_visitor_cannot_view_management_dashboard(self):
        response = self.client.get("/management/")
        self.assertIn(response.status_code, (302, 401, 403))

    def test_client_supplied_admin_role_does_not_grant_access(self):
        response = self.client.get(
            "/management/",
            HTTP_X_USER_ROLE="admin",
        )
        self.assertIn(response.status_code, (302, 401, 403))

    def test_unverified_bearer_token_does_not_grant_access(self):
        response = self.client.get(
            "/management/",
            HTTP_AUTHORIZATION="Bearer invalid-token",
        )
        self.assertIn(response.status_code, (302, 401, 403))


class AdminAuthenticationTests(SimpleTestCase):

    def test_management_login_page_is_available(self):
        response = self.client.get("/management/login/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "management/login.html")

    def test_management_login_rejects_get_submission(self):
        response = self.client.get("/management/authenticate/")
        self.assertEqual(response.status_code, 405)

    def test_management_login_rejects_missing_credentials(self):
        response = self.client.post(
            "/management/authenticate/",
            data={"username": "", "password": ""},
        )
        self.assertIn(response.status_code, (400, 401))

    def test_management_dashboard_requires_verified_session(self):
        response = self.client.get("/management/")
        self.assertEqual(response.status_code, 403)


class AdminSessionSecurityTests(TestCase):

    def test_unverified_admin_role_in_session_cannot_access_dashboard(self):
        session = self.client.session
        session["role"] = "admin"
        session.save()

        response = self.client.get("/management/")

        self.assertEqual(response.status_code, 403)
        self.assertTemplateNotUsed(
            response,
            "management/dashboard.html",
        )

    def test_expired_admin_session_cannot_access_dashboard(self):
        session = self.client.session
        session["role"] = "admin"
        session.set_expiry(-1)
        session.save()

        response = self.client.get("/management/")

        self.assertEqual(response.status_code, 403)
        self.assertTemplateNotUsed(
            response,
            "management/dashboard.html",
        )



    def test_forged_management_session_flags_cannot_access_dashboard(self):
        session = self.client.session
        session["management_verified_admin"] = True
        session["management_admin_role"] = "admin"
        session["management_admin_id"] = 999
        session["management_admin_username"] = "forged-admin"
        session.save()

        response = self.client.get("/management/")

        self.assertEqual(response.status_code, 403)
        self.assertTemplateNotUsed(
            response,
            "management/dashboard.html",
        )


class AdminVerifiedLoginTests(TestCase):

    @patch("ui.views.verify_admin_credentials")
    def test_verified_admin_can_access_dashboard(self, verify):
        import base64
        import json
        from datetime import timedelta
        from unittest.mock import patch as mock_patch

        from cryptography.fernet import Fernet
        from django.utils import timezone

        payload = {
            "exp": int(
                (timezone.now() + timedelta(minutes=30)).timestamp()
            ),
            "token_type": "access",
        }

        encoded_payload = base64.urlsafe_b64encode(
            json.dumps(payload).encode("utf-8")
        ).rstrip(b"=").decode("ascii")

        synthetic_token = f"test-header.{encoded_payload}.test-signature"

        verify.return_value = {
            "id": 1,
            "username": "testadmin",
            "role": "admin",
            "access_token": synthetic_token,
        }

        test_key = Fernet.generate_key().decode("ascii")

        with mock_patch.dict(
            "os.environ",
            {"MANAGEMENT_TOKEN_ENCRYPTION_KEY": test_key},
        ):
            self._verify_successful_admin_login()

    def _verify_successful_admin_login(self):
        response = self.client.post(
            "/management/authenticate/",
            {"username": "testadmin", "password": "test-password"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/management/")

        dashboard = self.client.get("/management/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertTemplateUsed(
            dashboard,
            "management/dashboard.html",
        )

    @patch("ui.views.verify_admin_credentials")
    def test_customer_cannot_establish_admin_session(self, verify):
        verify.return_value = {
            "id": 2,
            "username": "testcustomer",
            "role": "customer",
        }

        response = self.client.post(
            "/management/authenticate/",
            {"username": "testcustomer", "password": "test-password"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            self.client.get("/management/").status_code,
            403,
        )

    @patch("ui.views.verify_admin_credentials")
    def test_staff_cannot_establish_admin_session(self, verify):
        verify.return_value = {
            "id": 3,
            "username": "teststaff",
            "role": "staff",
        }

        response = self.client.post(
            "/management/authenticate/",
            {"username": "teststaff", "password": "test-password"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            self.client.get("/management/").status_code,
            403,
        )

    @patch("ui.views.verify_admin_credentials")
    def test_invalid_credentials_cannot_establish_session(self, verify):
        verify.return_value = None

        response = self.client.post(
            "/management/authenticate/",
            {"username": "invalid", "password": "invalid"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            self.client.get("/management/").status_code,
            403,
        )


class AdminAuthServiceVerificationTests(SimpleTestCase):

    @patch("urllib.request.urlopen")
    def test_valid_admin_response_is_accepted(self, urlopen):
        from ui.views import verify_admin_credentials

        response = Mock()
        response.status = 200
        response.read.return_value = (
            b'{"id":1,"username":"testadmin","role":"admin",'
            b'"access":"test-access-token"}'
        )
        urlopen.return_value.__enter__.return_value = response

        result = verify_admin_credentials("testadmin", "test-password")

        self.assertIsNotNone(result)
        self.assertEqual(result["role"], "admin")
        self.assertEqual(result["id"], 1)

    @patch("urllib.request.urlopen")
    def test_invalid_credentials_are_rejected(self, urlopen):
        from urllib.error import HTTPError
        from ui.views import verify_admin_credentials

        urlopen.side_effect = HTTPError(
            "http://auth-service:8001/api/auth/login/",
            401,
            "Unauthorized",
            {},
            None,
        )

        result = verify_admin_credentials("invalid", "invalid")

        self.assertIsNone(result)

    @patch("urllib.request.urlopen")
    def test_customer_role_is_rejected(self, urlopen):
        from ui.views import verify_admin_credentials

        response = Mock()
        response.status = 200
        response.read.return_value = (
            b'{"id":2,"username":"customer","role":"customer",'
            b'"access":"test-access-token"}'
        )
        urlopen.return_value.__enter__.return_value = response

        result = verify_admin_credentials("customer", "test-password")

        self.assertIsNone(result)

    @patch("urllib.request.urlopen")
    def test_malformed_response_is_rejected(self, urlopen):
        from ui.views import verify_admin_credentials

        response = Mock()
        response.status = 200
        response.read.return_value = b"invalid-json"
        urlopen.return_value.__enter__.return_value = response

        result = verify_admin_credentials("testadmin", "test-password")

        self.assertIsNone(result)


class AdminTokenLogoutTests(TestCase):
    """Verify logout removes stored administrator credentials."""

    @patch("ui.views.verify_admin_credentials")
    def test_logout_removes_stored_token_and_blocks_dashboard(self, verify):
        import base64
        import json
        from datetime import timedelta
        from unittest.mock import patch as mock_patch

        from cryptography.fernet import Fernet
        from django.utils import timezone

        from ui.models import ManagementAuthToken

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

        test_key = Fernet.generate_key().decode("ascii")

        with mock_patch.dict(
            "os.environ",
            {"MANAGEMENT_TOKEN_ENCRYPTION_KEY": test_key},
        ):
            login = self.client.post(
                "/management/authenticate/",
                {
                    "username": "testadmin",
                    "password": "test-password",
                },
            )

            self.assertEqual(login.status_code, 302)

            session_key = self.client.session.session_key

            self.assertTrue(
                ManagementAuthToken.objects.filter(
                    session_key=session_key,
                ).exists()
            )

            self.assertEqual(
                ManagementAuthToken.objects.count(),
                1,
            )

            logout = self.client.post("/management/logout/")

            self.assertEqual(logout.status_code, 302)
            self.assertEqual(
                logout.url,
                "/management/login/",
            )

            self.assertFalse(
                ManagementAuthToken.objects.filter(
                    session_key=session_key,
                ).exists()
            )

            self.assertEqual(
                ManagementAuthToken.objects.count(),
                0,
            )

            dashboard = self.client.get("/management/")

            self.assertEqual(dashboard.status_code, 403)
