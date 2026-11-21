import sys
import json
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.main import app as fastapi_app

class VercelPathMiddleware:
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            
            # Si debug=1, devolver inspección directa
            query = scope.get("query_string", b"").decode("utf-8")
            if "debug=1" in query:
                header_dict = {k.decode("latin1"): v.decode("latin1") for k, v in scope.get("headers", [])}
                body = json.dumps({
                    "scope_path": scope.get("path"),
                    "scope_raw_path": scope.get("raw_path", b"").decode("latin1", errors="ignore"),
                    "query": query,
                    "headers": header_dict
                }, indent=2).encode("utf-8")
                
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"application/json"]]
                })
                await send({
                    "type": "http.response.body",
                    "body": body,
                    "more_body": False
                })
                return

            # Restaurar ruta
            for h_name in (b"x-forwarded-uri", b"x-matched-path", b"x-vercel-sc-path", b"x-envoy-original-path"):
                v = headers.get(h_name)
                if v:
                    path = v.decode("latin1").split("?")[0]
                    if path and path not in ("/api/index.py", "/api/index"):
                        scope["path"] = path
                        break

        await self.asgi_app(scope, receive, send)

app = VercelPathMiddleware(fastapi_app)
