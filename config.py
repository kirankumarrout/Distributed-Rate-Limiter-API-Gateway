import os

class Config:
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    DEFAULT_CAPACITY = int(os.getenv('DEFAULT_CAPACITY', 100))
    DEFAULT_REFILL_RATE = float(os.getenv('DEFAULT_REFILL_RATE', 100/60))
    SLIDING_WINDOW_SECONDS = int(os.getenv('SLIDING_WINDOW_SECONDS', 60))
    SLIDING_WINDOW_MAX_REQUESTS = int(os.getenv('SLIDING_WINDOW_MAX_REQUESTS', 100))