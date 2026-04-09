from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from app.middleware import RateLimitMiddleware
import time

app = FastAPI(title="Distributed Rate Limiter & API Gateway", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RateLimitMiddleware, algorithm="token_bucket")

REQUESTS = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    REQUESTS.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
    LATENCY.labels(method=request.method, endpoint=request.url.path).observe(duration)
    return response

@app.get("/")
async def root():
    return {"service": "Rate Limiter API Gateway", "status": "operational"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v1/data")
async def get_data():
    return {"data": "Protected data", "timestamp": time.time()}

@app.post("/api/v1/echo")
async def echo(data: dict):
    return {"echo": data, "timestamp": time.time()}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)