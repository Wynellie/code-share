from locust import HttpUser, task, between
import random
import string


def random_string(length=8):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))


class ApiUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        # генерим логин и пароль для каждого пользователя
        self.login = random_string()
        self.password = random_string()

    @task
    def register(self):
        self.client.post(
            "/api/auth/register",
            json={
                "login": self.login,
                "password": self.password
            }
        )
    @task
    def login(self):
        self.client.post( "/api/auth/login",
            json={
                "login": self.login,
                "password": self.password
            })
    @task
    def logout(self):
        self.client.get("/api/auth/logout")