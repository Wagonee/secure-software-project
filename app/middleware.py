import threading
import time
from collections import defaultdict
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse

from app.logging_config import correlation_id_ctx, get_logger

logger = get_logger("middleware")


class RateLimiter:
    def __init__(self, requests_per_minute: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.lock = threading.Lock()

    async def __call__(self, request: Request, call_next):
        # Генерируем или берем correlation_id из заголовка запроса
        cid = request.headers.get("X-Correlation-ID", str(uuid4()))
        correlation_id_ctx.set(cid)

        client_ip = request.headers.get("x-forwarded-for") or request.client.host
        now = time.time()

        with self.lock:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip] if now - req_time < 60
            ]

            if len(self.requests[client_ip]) >= self.requests_per_minute:
                logger.warning(f"Rate limit exceeded for {client_ip}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "type": "about:blank",
                        "title": "Too Many Requests",
                        "status": 429,
                        "detail": "Rate limit exceeded. Please try again later.",
                        "correlation_id": cid,
                    },
                    headers={"X-Correlation-ID": cid},
                )

            self.requests[client_ip].append(now)

        response = await call_next(request)
        # Добавляем correlation_id в заголовки ответа
        response.headers["X-Correlation-ID"] = cid
        return response
