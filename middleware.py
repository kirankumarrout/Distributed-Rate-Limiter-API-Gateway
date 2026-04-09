from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.rate_limiter import TokenBucketRateLimiter, SlidingWindowRateLimiter

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, algorithm: str = "token_bucket"):
        super().__init__(app)
        self.algorithm = algorithm
        self.token_limiter = TokenBucketRateLimiter()
        self.sliding_limiter = SlidingWindowRateLimiter()
    
    async def dispatch(self, request: Request, call_next):
        client_id = request.headers.get("X-API-Key") or request.client.host
        endpoint = request.url.path
        
        if self.algorithm == "token_bucket":
            allowed, remaining, retry_after = self.token_limiter.allow_request(client_id, endpoint)
        else:
            allowed, retry_after = self.sliding_limiter.allow_request(client_id, endpoint)
            remaining = 0
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                headers={"X-RateLimit-Retry-After": str(retry_after)},
                content={"error": "Rate limit exceeded", "retry_after_seconds": retry_after}
            )
        
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response