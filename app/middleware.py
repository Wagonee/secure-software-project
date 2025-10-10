from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
import threading

class RateLimiter:
    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.lock = threading.Lock()

    async def __call__(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()
        
        with self.lock:
            self.requests[client_ip] = [req_time for req_time in self.requests[client_ip] 
                                      if now - req_time < 60]
            
            if len(self.requests[client_ip]) >= self.requests_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"error": {"code": "rate_limit_exceeded", 
                                     "message": "Too many requests"}}
                )
            
            self.requests[client_ip].append(now)
        
        return await call_next(request)

