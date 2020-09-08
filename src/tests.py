import json
import unittest
from app import app


class MainRoute(unittest.TestCase):
    """Test Redirect and content type for /"""

    def setUp(self):
        app.testing = True   #  
        self.client = app.test_client()

    def test_redirect(self):
        resp = self.client.get("/")
        self.assertEqual(resp.location, 'http://localhost/login')

    def test_content_type(self):
        resp = self.client.get("/login")
        self.assertEqual(resp.content_type, 'text/html; charset=utf-8')

class LoginFlow(unittest.TestCase):
    """Test Login Flow"""

    def setUp(self):
        app.testing = True   #  
        self.client = app.test_client()

    def test_login_false(self):
        resp = self.client.post("/login", data={"username": "admin", "password":"wrongpassword"})
        self.assertEqual(resp.location, 'http://localhost/login')

    def test_login_true(self):
        resp = self.client.post("/login", data={"username": "admin", "password":"admin"})
        self.assertEqual(resp.location, 'http://localhost/')

    def test_login_true_cookie(self):
        resp = self.client.post("/login", data={"username": "admin", "password":"admin"})
        self.assertIsNotNone(resp.headers.get('Set-Cookie'))

    def test_logout(self):
        self.client.post("/login", data={"username": "admin", "password":"admin"})
        resp = self.client.get("/logout/")
        self.assertEqual(resp.location, 'http://localhost/')

    def test_admin_unauth(self):
        self.client.get("/logout/")
        resp = self.client.get("/admin")
        self.assertEqual(resp.status, '308 PERMANENT REDIRECT')

    def test_admin_auth(self):
        self.client.post("/login", data={"username": "admin", "password":"admin"})
        resp = self.client.get("/admin")
        self.assertEqual(resp.location, 'http://localhost/admin/')



if __name__ == '__main__':
    unittest.main()