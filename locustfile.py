from locust import HttpUser, task, between

class RateLimiterUser(HttpUser):
    wait_time = between(0.01, 0.05)
    
    @task(3)
    def get_root(self):
        self.client.get("/")
    
    @task(5)
    def get_data(self):
        self.client.get("/api/v1/data")
    
    @task(2)
    def post_echo(self):
        self.client.post("/api/v1/echo", json={"test": "data"})