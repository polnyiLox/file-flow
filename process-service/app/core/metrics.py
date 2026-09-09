from time import perf_counter

from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

http_requests = Counter("http_requests_total", "HTTP requests", ["method", "path", "status"])
http_duration = Histogram("http_request_duration_seconds", "HTTP request duration", ["method", "path"])
images_processed = Counter("images_processed_total", "Processed images")
processing_failed = Counter("image_processing_failed_total", "Invalid images")
processing_duration = Histogram("image_processing_duration_seconds", "Thumbnail processing duration")
rabbitmq_failures = Counter("rabbitmq_processing_failed_total", "Command handling failures")


def setup_metrics(app) -> None:
    @app.middleware("http")
    async def measure_request(request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)
        started = perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            route = request.scope.get("route")
            path = getattr(route, "path", "unmatched")
            http_requests.labels(request.method, path, str(status)).inc()
            http_duration.labels(request.method, path).observe(perf_counter() - started)

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})
