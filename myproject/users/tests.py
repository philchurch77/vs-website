from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import NoReverseMatch, reverse


class HomepageTests(TestCase):
    def test_homepage_renders(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


class RegistrationDisabledTests(TestCase):
    """Self-registration is deliberately disabled — accounts come from the admin."""

    def test_register_url_is_gone(self):
        with self.assertRaises(NoReverseMatch):
            reverse("users:register")
        response = self.client.get("/users/register/")
        self.assertEqual(response.status_code, 404)

    def test_allauth_signup_is_not_mounted(self):
        # allauth ships its own open signup view; its urls must stay unmounted
        response = self.client.get("/accounts/signup/")
        self.assertEqual(response.status_code, 404)
        response = self.client.post("/accounts/signup/", {
            "username": "stranger",
            "email": "stranger@example.com",
            "password1": "complex-pass-123456",
            "password2": "complex-pass-123456",
        })
        self.assertEqual(response.status_code, 404)
        self.assertFalse(User.objects.filter(username="stranger").exists())


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("teacher", password="pass-12345")

    def test_login_page_renders(self):
        response = self.client.get(reverse("users:login"))
        self.assertEqual(response.status_code, 200)

    def test_login_redirects_to_home(self):
        response = self.client.post(reverse("users:login"), {
            "username": "teacher",
            "password": "pass-12345",
        })
        self.assertRedirects(response, "/")

    def test_login_follows_safe_relative_next(self):
        response = self.client.post(reverse("users:login"), {
            "username": "teacher",
            "password": "pass-12345",
            "next": "/resources/",
        })
        self.assertRedirects(response, "/resources/")

    def test_login_ignores_external_next(self):
        # An off-site `next` must not become an open redirect
        response = self.client.post(reverse("users:login"), {
            "username": "teacher",
            "password": "pass-12345",
            "next": "https://evil.example.com/phish",
        })
        self.assertRedirects(response, "/")

    def test_logout_redirects_to_home(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("users:logout"))
        self.assertRedirects(response, "/")
