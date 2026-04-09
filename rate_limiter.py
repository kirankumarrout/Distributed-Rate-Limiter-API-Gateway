import redis
import time
import hashlib
from app.config import Config

class TokenBucketRateLimiter:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True
        )
    
    def _get_key(self, client_id: str, endpoint: str) -> str:
        key_string = f"ratelimit:token:{client_id}:{endpoint}"
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def allow_request(self, client_id: str, endpoint: str, tokens: int = 1):
        lua_script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local requested = tonumber(ARGV[3])
        local now = tonumber(ARGV[4])
        
        local data = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(data[1]) or capacity
        local last_refill = tonumber(data[2]) or now
        
        local time_passed = now - last_refill
        local refill = time_passed * refill_rate
        tokens = math.min(capacity, tokens + refill)
        
        if tokens >= requested then
            tokens = tokens - requested
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, math.ceil(capacity / refill_rate) + 60)
            return {1, math.floor(tokens)}
        else
            local retry_after = math.ceil((requested - tokens) / refill_rate)
            return {0, math.floor(tokens), retry_after}
        end
        """
        
        key = self._get_key(client_id, endpoint)
        now = time.time()
        
        result = self.redis_client.eval(lua_script, 1, key, Config.DEFAULT_CAPACITY, Config.DEFAULT_REFILL_RATE, tokens, now)
        
        if result[0] == 1:
            return True, result[1], 0
        else:
            return False, result[1], result[2]


class SlidingWindowRateLimiter:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True
        )
    
    def _get_key(self, client_id: str, endpoint: str) -> str:
        key_string = f"ratelimit:sliding:{client_id}:{endpoint}"
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def allow_request(self, client_id: str, endpoint: str):
        key = self._get_key(client_id, endpoint)
        now = time.time()
        window_start = now - Config.SLIDING_WINDOW_SECONDS
        
        lua_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window_start = tonumber(ARGV[2])
        local max_requests = tonumber(ARGV[3])
        
        redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)
        local current = redis.call('ZCARD', key)
        
        if current < max_requests then
            redis.call('ZADD', key, now, now .. ':' .. math.random())
            redis.call('EXPIRE', key, 60)
            return {1, max_requests - current - 1}
        else
            local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
            local retry_after = math.ceil((tonumber(oldest[2]) + max_requests) - now)
            return {0, 0, retry_after}
        end
        """
        
        result = self.redis_client.eval(lua_script, 1, key, now, window_start, Config.SLIDING_WINDOW_MAX_REQUESTS)
        
        if result[0] == 1:
            return True, result[1]
        else:
            return False, result[2]