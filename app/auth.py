"""Contraseñas Argon2, sesiones en servidor y CSRF."""
import hashlib, os, secrets
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Request, Response, Depends
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from sqlalchemy import select
from .db import SessionLocal, Nurse, LoginSession

hash_password = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
COOKIE = 'samu_sesion'
COOKIE_SECURE = os.getenv('COOKIE_SECURE', '1' if os.getenv('APP_ENV') == 'production' else '0') == '1'

def now(): return datetime.now(timezone.utc)
def naive_utc(dt): return dt.replace(tzinfo=timezone.utc) if dt and dt.tzinfo is None else dt

def hash_token(token): return hashlib.sha256(token.encode('utf-8')).hexdigest()

def authenticated(request: Request):
    raw = request.cookies.get(COOKIE, '')
    if not raw: raise HTTPException(status_code=401, detail='Inicia sesión como personal de enfermería.')
    db = SessionLocal()
    try:
        s = db.scalar(select(LoginSession).where(LoginSession.token_hash==hash_token(raw)))
        if not s or naive_utc(s.expires) < now(): raise HTTPException(status_code=401, detail='Sesión vencida.')
        user = db.get(Nurse,s.user_id)
        if not user or not user.active: raise HTTPException(status_code=403, detail='Cuenta deshabilitada.')
        if request.method not in ('GET','HEAD','OPTIONS'):
            csrf = request.headers.get('X-CSRF-Token','')
            if not csrf or not secrets.compare_digest(csrf,s.csrf):
                raise HTTPException(status_code=403, detail='Token CSRF inválido.')
        return user, s
    finally: db.close()

def requires_admin(current=Depends(authenticated)):
    user,session=current
    if user.role!='admin': raise HTTPException(status_code=403, detail='Solo administración.')
    return user,session

def new_login(user, response):
    raw=secrets.token_urlsafe(48)
    s=LoginSession(token_hash=hash_token(raw), csrf=secrets.token_urlsafe(40),user_id=user.id,expires=now()+timedelta(hours=12))
    with SessionLocal.begin() as db: db.add(s)
    response.set_cookie(key=COOKIE,value=raw,max_age=12*3600,httponly=True,secure=COOKIE_SECURE,samesite='lax',path='/')
    return s

def check_password(hashed,plain):
    try: return hash_password.verify(hashed,plain)
    except (VerifyMismatchError,VerificationError): return False
