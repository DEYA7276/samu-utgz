import sys
import json
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.main import app as fastapi_app

async def app(scope, receive, send):
    if scope["type"] == "http":
        headers = {k.decode("latin1"): v.decode("latin1") for k, v in scope.get("headers", [])}
        
        # Si la petición pide debug o /debug
        query = scope.get("query_string", b"").decode("latin1")
        if "debug" in query or "debug" in scope.get("path", ""):
            body = json.dumps({
                "scope_path": scope.get("path"),
                "query": query,
                "headers": headers
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

        # Restaurar la ruta real usando los encabezados que Vercel envía
        # Vercel envía x-matched-path con la ruta real antes del rewrite
        real_path = headers.get("x-matched-path") or headers.get("x-forwarded-uri")
        if real_path:
            scope["path"] = real_path.split("?")[0]

    await fastapi_app(scope, receive, send)
