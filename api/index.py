import sys
from pathlib import Path

# Agregar raíz del repositorio a sys.path para importar app.main
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.main import app as fastapi_app

class VercelPathMiddleware:
    """Restaura la ruta original solicitada por el usuario desde los encabezados de Vercel."""
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            
            # Vercel inyecta la ruta original en x-matched-path o x-forwarded-uri
            raw_path = headers.get(b"x-matched-path") or headers.get(b"x-forwarded-uri")
            if raw_path:
                orig_path = raw_path.decode("utf-8", errors="ignore").split("?")[0]
                if orig_path:
                    scope["path"] = orig_path
            elif scope.get("path") in ("/api/index.py", "/api/index", "/api"):
                scope["path"] = "/"

        await self.asgi_app(scope, receive, send)

app = VercelPathMiddleware(fastapi_app)
