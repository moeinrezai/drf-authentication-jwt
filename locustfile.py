from locust import HttpUser, task, between
import random
import string

class AuthFlowUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # تنظیم User-Agent موبایل برای غیرفعال‌سازی CSRF
        self.client.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })

        # ایجاد کاربر تصادفی
        suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
        self.email = f"loadtest_{suffix}@example.com"
        self.password = "TestPass123"
        self.name = f"User {suffix}"

        # ثبت‌نام
        resp = self.client.post("/api/accounts/v1/register/", json={
            "email": self.email,
            "name": self.name,
            "password": self.password,
            "password2": self.password
        })
        if resp.status_code == 201:
            data = resp.json()
            self.access = data.get("access")
            self.refresh = data.get("refresh")
        else:
            # اگر کاربر وجود داشت، لاگین کن
            resp = self.client.post("/api/accounts/v1/login/", json={
                "email": self.email,
                "password": self.password
            })
            if resp.status_code == 200:
                data = resp.json()
                self.access = data.get("access")
                self.refresh = data.get("refresh")
            else:
                self.access = None
                self.refresh = None

    @task(5)
    def view_profile(self):
        if self.access:
            self.client.get(
                "/api/accounts/v1/profile/",
                headers={"Authorization": f"Bearer {self.access}"}
            )

    @task(2)
    def refresh_token(self):
        if self.refresh:
            self.client.post(
                "/api/accounts/v1/refresh/",
                json={"refresh": self.refresh}
            )

    @task(1)
    def login_again(self):
        self.client.post(
            "/api/accounts/v1/login/",
            json={
                "email": self.email,
                "password": self.password
            }
        )

    @task(1)
    def logout(self):
        if self.access and self.refresh:
            self.client.post(
                "/api/accounts/v1/logout/",
                json={"refresh": self.refresh},
                headers={"Authorization": f"Bearer {self.access}"}
            )
            self.on_start()