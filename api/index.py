import sys
from pathlib import Path
from fastapi import Request

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.main import app

@app.middleware("http")
async def ensure_api_prefix(request: Request, call_next):
    p = request.scope.get("path", "")
    if p and not p.startswith("/api/") and not p.startswith("/descargar/") and p not in ("/", "/healthz", "/index.html"):
        request.scope["path"] = "/api/" + p.lstrip("/")
    return await call_next(request)
