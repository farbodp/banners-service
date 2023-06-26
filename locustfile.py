import random
from locust import HttpUser, task, between


class MyUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def get_images(self):
        random_number = random.randint(1, 100)
        self.client.get("/campaigns/" + str(random_number))
