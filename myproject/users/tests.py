from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class HomepageTests(TestCase):
    def test_homepage_renders(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


class RegistrationTests(TestCase):
    def test_register_page_renders(self):
        response = self.client.get(reverse("users:register"))
        self.assertEqual(response.status_code, 200)

    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(reverse("users:register"), {
            "username": "newteacher",
            "password1": "complex-pass-123",
            "password2": "complex-pass-123",
        })
        self.assertRedirects(response, reverse("posts:list"))
        self.assertTrue(User.objects.filter(username="newteacher").exists())
        self.assertTrue(response.wsgi_request.user.is_authenticated)


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("teacher", password="pass-12345")

    def test_login_page_renders(self):
        response = self.client.get(reverse("users:login"))
        self.assertEqual(response.status_code, 200)

    def test_login_redirects_to_posts(self):
        response = self.client.post(reverse("users:login"), {
            "username": "teacher",
            "password": "pass-12345",
        })
        self.assertRedirects(response, reverse("posts:list"))

    def test_logout_redirects_to_posts(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("users:logout"))
        self.assertRedirects(response, reverse("posts:list"))
