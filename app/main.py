"""SAMU UTGZ v2: backend API, sesiones seguras, PDF y mensajería SMTP."""
import base64, hashlib, io, os, re, secrets
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
from email.utils import parseaddr
from typing import Any
from PIL import Image
from fastapi import FastAPI, Request, Response, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func, or_, desc
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from . import pdf_templates as pdf, mailer, importer
from .auth import authenticated, requires_admin, hash_password, check_password, new_login, hash_token, now, naive_utc, COOKIE, COOKIE_SECURE
from .db import SessionLocal, init_db, Nurse, LoginSession, Student, Attention, Referral, Inventory, Contact, MailLog, Audit, DownloadToken, audit, EmailOTP

STATIC=Path(__file__).resolve().parent/'static'
PROD=os.getenv('APP_ENV','development')=='production'
app=FastAPI(title='SAMU UTGZ API',version='2.0.0',docs_url=None if PROD else '/docs',redoc_url=None)
app.mount('/static',StaticFiles(directory=STATIC),name='static')

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '').strip()
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '').strip()
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://127.0.0.1:8000/api/auth/google/callback').strip()
OAUTH_STATES: dict[str, dict] = {}

def cleanup_oauth_states():
    t_now = now()
    expired = [k for k, v in list(OAUTH_STATES.items()) if v.get('expires', t_now) < t_now]
    for k in expired:
        OAUTH_STATES.pop(k, None)

@app.on_event('startup')
def startup(): init_db()

@app.middleware('http')
async def security_headers(request:Request,call_next):
    if request.headers.get('content-length') and int(request.headers['content-length'])>3_000_000:
        return JSONResponse({'detail':'La solicitud supera 3 MB.'},status_code=413)
    response=await call_next(request)
    response.headers['X-Debug-Path'] = request.url.path
    response.headers['X-Debug-Matched'] = request.headers.get('x-matched-path', '')
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Permissions-Policy']='camera=(self), microphone=(), geolocation=()'
    response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data: blob: https://*.googleusercontent.com; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self' https://accounts.google.com https://oauth2.googleapis.com https://openidconnect.googleapis.com; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    if PROD: response.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
    if request.url.path.startswith('/api/') or request.url.path.startswith('/descargar/'):
        response.headers['Cache-Control']='no-store, private'
    return response

@app.get('/api/debug-headers')
def debug_headers(request: Request):
    return {
        'path': request.url.path,
        'headers': dict(request.headers),
        'scope_path': request.scope.get('path')
    }

@app.get('/healthz')
def health(): return {'ok':True, 'servicio':'SAMU UTGZ'}

@app.get('/manifest.webmanifest')
def manifest():return FileResponse(STATIC/'manifest.webmanifest',media_type='application/manifest+json')
@app.get('/service-worker.js')
def service_worker():return FileResponse(STATIC/'service-worker.js',media_type='application/javascript',headers={'Cache-Control':'no-cache, no-store, must-revalidate'})
@app.get('/favicon.ico')
def favicon():return FileResponse(STATIC/'assets/icon-192.png',media_type='image/png')
@app.get('/')
@app.get('/login')
@app.get('/alumno')
@app.get('/enfermeria')
@app.get('/importar')
@app.get('/dashboard')
@app.get('/fichas')
@app.get('/bitacora')
@app.get('/canalizaciones')
@app.get('/inventario')
@app.get('/contactos')
def index():return FileResponse(STATIC/'index.html',headers={'Cache-Control':'no-cache, no-store, must-revalidate'})

def db_session():
    db=SessionLocal()
    try: yield db
    finally: db.close()

def bad(text,status=400): raise HTTPException(status_code=status,detail=text)

def clean(d,key,required=False,maxlen=500):
    v=d.get(key,'')
    if v is None: v=''
    if not isinstance(v,(str,int,float)): bad('Dato inválido: '+key)
    v=str(v).strip()
    if required and not v: bad('Campo obligatorio: '+key)
    if len(v)>maxlen: bad(f'El campo {key} excede {maxlen} caracteres.')
    return v

def int_val(d,key,maximum=100000):
    try: value=int(d.get(key,0))
    except (ValueError,TypeError):bad('Número inválido: '+key)
    if value<0 or value>maximum:bad('Cantidad fuera de rango: '+key)
    return value

def valid_date(s):
    try: datetime.strptime(s,'%Y-%m-%d')
    except ValueError: bad('La fecha debe ser válida (AAAA-MM-DD).')
    return s

def valid_time(s):
    try: datetime.strptime(s,'%H:%M')
    except ValueError: bad('La hora debe ser válida (HH:MM).')
    return s

def valid_email(email):
    email=email.strip().lower()
    if len(email)>254 or not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[A-Za-z]{2,}',email): bad('Correo electrónico inválido.')
    return email

def signature(d,key,required=True):
    data=clean(d,key,required,400_000)
    if not data: return ''
    if not data.startswith('data:image/png;base64,'): bad('Firma inválida: debe ser PNG.')
    try:
        binary=base64.b64decode(data.split(',',1)[1],validate=True)
        if len(binary)>250_000: bad('Firma demasiado pesada (máximo 250 KB).')
        im=Image.open(io.BytesIO(binary));im.verify()
        im=Image.open(io.BytesIO(binary))
        if im.format!='PNG' or not (im.width>20 and im.height>10 and im.width<=2400 and im.height<=1000):
            bad('Tamaño de firma inválido.')
    except HTTPException: raise
    except Exception: bad('No se pudo leer la firma.')
    return data

def photograph(data):
    if not data:return None
    data=clean({'photo':data},'photo',False,1_200_000)
    if not data.startswith(('data:image/png;base64,','data:image/jpeg;base64,')):bad('La fotografía debe ser JPG o PNG.')
    try:
        raw=base64.b64decode(data.split(',',1)[1],validate=True)
        if len(raw)>800_000: bad('La foto debe pesar menos de 800 KB.')
        im=Image.open(io.BytesIO(raw));im.verify()
        im=Image.open(io.BytesIO(raw))
        if im.width>3000 or im.height>3000:bad('La foto excede 3000px.')
    except HTTPException:raise
    except Exception:bad('Fotografía inválida.')
    return {'data':data}

def db_audit(db,user,verb,table,ident):audit(db,user.id if user else None,verb,table,ident)

class LoginRequest(BaseModel): email:str; password:str
@app.post('/api/session/login')
def login(body:LoginRequest,response:Response,request:Request,db=Depends(db_session)):
    # Limite persistente por IP/correo en ventana temporal (se refuerza en proxy inverso).
    email=valid_email(body.email)
    attempts=db.scalar(select(func.count(Audit.id)).where(Audit.accion=='login_fallido',Audit.entidad==hashlib.sha256(email.encode()).hexdigest(),Audit.created>now()-timedelta(minutes=15))) or 0
    if attempts>=10:bad('Demasiados intentos. Intenta en 15 minutos.',429)
    user=db.scalar(select(Nurse).where(Nurse.email==email,Nurse.active==True))
    if not user or not check_password(user.password_hash,body.password):
        audit(db,None,'login_fallido',hashlib.sha256(email.encode()).hexdigest(),None);db.commit()
        bad('Credenciales incorrectas.',401)
    session=new_login(user,response)
    audit(db,user.id,'iniciar_sesion','personal',user.id);db.commit()
    return {'user':{'name':user.name,'email':user.email,'role':user.role},'csrf':session.csrf}

@app.get('/api/session')
def session_info(current=Depends(authenticated)):
    user,s=current
    return {'user':{'name':user.name,'email':user.email,'role':user.role},'csrf':s.csrf}

@app.post('/api/session/logout')
def logout(response:Response,current=Depends(authenticated),db=Depends(db_session)):
    user,s=current; db.execute(__import__('sqlalchemy').delete(LoginSession).where(LoginSession.id==s.id));db.commit()
    response.delete_cookie(COOKIE,path='/');return {'ok':True}

def render_oauth_success(name: str, token: str) -> str:
    from html import escape
    safe_name = escape(name)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Acceso Autorizado · SAMU UTGZ</title>
  <style>
    body {{ margin:0; padding:24px; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,sans-serif; background:#f3f6f2; color:#17382b; display:flex; align-items:center; justify-content:center; min-height:85vh; }}
    .card {{ max-width:440px; width:100%; background:#fff; border-radius:18px; padding:36px 28px; text-align:center; box-shadow:0 10px 30px rgba(40,104,79,0.08); border:1px solid #dce5dc; }}
    .icon {{ width:64px; height:64px; border-radius:50%; background:#e8f4ed; color:#28684F; display:inline-flex; align-items:center; justify-content:center; margin-bottom:18px; }}
    h1 {{ font-size:1.35rem; margin:0 0 8px; color:#123424; }}
    p {{ font-size:0.95rem; color:#4a6356; line-height:1.5; margin:0 0 18px; }}
    .btn {{ display:inline-block; padding:12px 24px; background:#28684F; color:#fff; text-decoration:none; font-weight:600; border-radius:8px; transition:opacity .2s; }}
    .btn:hover {{ opacity:0.9; }}
    .hint {{ font-size:0.85rem; color:#789083; margin-top:20px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">
      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
    </div>
    <h1>¡Autenticación exitosa!</h1>
    <p>Bienvenida(o), <strong>{safe_name}</strong>. Tu cuenta de Google ha sido verificada.</p>
    <a href="/enfermeria" class="btn" id="btn-continue">Entrar al Panel de Enfermería</a>
    <p class="hint">Si abriste el inicio de sesión desde la aplicación móvil SAMU en tu celular, puedes regresar a ella; tu acceso se activó automáticamente.</p>
  </div>
  <script>
    setTimeout(function() {{
      window.location.href = '/enfermeria';
    }}, 900);
  </script>
</body>
</html>"""

def render_oauth_unauthorized(email: str) -> str:
    from html import escape
    safe_email = escape(email)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Acceso Denegado · SAMU UTGZ</title>
  <style>
    body {{ margin:0; padding:24px; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,sans-serif; background:#fcf7f7; color:#4d1818; display:flex; align-items:center; justify-content:center; min-height:85vh; }}
    .card {{ max-width:440px; width:100%; background:#fff; border-radius:18px; padding:36px 28px; text-align:center; box-shadow:0 10px 30px rgba(180,40,40,0.08); border:1px solid #f3d4d4; }}
    .icon {{ width:64px; height:64px; border-radius:50%; background:#fce8e8; color:#b02828; display:inline-flex; align-items:center; justify-content:center; margin-bottom:18px; }}
    h1 {{ font-size:1.35rem; margin:0 0 8px; color:#6b1515; }}
    p {{ font-size:0.95rem; color:#6b3b3b; line-height:1.5; margin:0 0 20px; }}
    .btn {{ display:inline-block; padding:12px 24px; background:#b02828; color:#fff; text-decoration:none; font-weight:600; border-radius:8px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">
      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
    </div>
    <h1>Acceso No Autorizado</h1>
    <p>La cuenta <strong>{safe_email}</strong> no está registrada como personal de enfermería autorizado en SAMU.</p>
    <p style="font-size:0.85rem;color:#855050;">Por seguridad y confidencialidad médica, únicamente el personal facultado por la UTGZ puede consultar este panel.</p>
    <a href="/login" class="btn">Volver a intentar</a>
  </div>
</body>
</html>"""

def render_oauth_error(title: str, detail: str) -> str:
    from html import escape
    safe_title = escape(title)
    safe_detail = escape(detail)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Error de Autenticación · SAMU UTGZ</title>
  <style>
    body {{ margin:0; padding:24px; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,sans-serif; background:#f9f9f9; color:#333; display:flex; align-items:center; justify-content:center; min-height:85vh; }}
    .card {{ max-width:440px; width:100%; background:#fff; border-radius:18px; padding:36px 28px; text-align:center; box-shadow:0 8px 24px rgba(0,0,0,0.06); border:1px solid #e0e0e0; }}
    h1 {{ font-size:1.3rem; margin:0 0 10px; color:#222; }}
    p {{ font-size:0.95rem; color:#666; margin:0 0 20px; }}
    .btn {{ display:inline-block; padding:10px 20px; background:#444; color:#fff; text-decoration:none; font-weight:600; border-radius:6px; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>{safe_title}</h1>
    <p>{safe_detail}</p>
    <a href="/login" class="btn">Regresar al inicio de sesión</a>
  </div>
</body>
</html>"""

@app.get('/api/auth/google/config')
def google_auth_config():
    return {'enabled': bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)}

@app.get('/api/auth/google/url')
def google_auth_url(response: Response):
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
        bad('Google OAuth 2.0 no está configurado en las variables de entorno del servidor (.env).', 400)
    cleanup_oauth_states()
    state = secrets.token_urlsafe(32)
    OAUTH_STATES[state] = {
        'created': now(),
        'expires': now() + timedelta(minutes=10),
        'status': 'pending',
        'exchange_token': None,
        'user_id': None,
        'error_msg': ''
    }
    response.set_cookie(
        key='samu_oauth_state',
        value=state,
        max_age=600,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite='lax',
        path='/'
    )
    import urllib.parse
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'online',
        'prompt': 'select_account'
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return {'enabled': True, 'url': auth_url, 'state': state}

@app.get('/api/auth/google/callback')
async def google_auth_callback(code: str = None, state: str = None, error: str = None, request: Request = None, response: Response = None, db = Depends(db_session)):
    cleanup_oauth_states()
    if error:
        if state and state in OAUTH_STATES:
            OAUTH_STATES[state]['status'] = 'error'
            OAUTH_STATES[state]['error_msg'] = f'Google devolvió error: {error}'
        return Response(content=render_oauth_error('Inicio de sesión cancelado o denegado por Google.', error), media_type='text/html')
        
    if not state or state not in OAUTH_STATES:
        return Response(content=render_oauth_error('Estado de seguridad inválido o solicitud expirada.', 'INVALID_STATE'), media_type='text/html', status_code=400)

    state_data = OAUTH_STATES[state]
    if now() > state_data['expires']:
        OAUTH_STATES.pop(state, None)
        return Response(content=render_oauth_error('La solicitud de inicio de sesión ha expirado. Vuelve a intentarlo.', 'EXPIRED_STATE'), media_type='text/html', status_code=400)

    if not code:
        state_data['status'] = 'error'
        return Response(content=render_oauth_error('Código de autorización no proporcionado por Google.', 'NO_CODE'), media_type='text/html', status_code=400)

    import httpx
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_resp = await client.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'code': code,
                    'client_id': GOOGLE_CLIENT_ID,
                    'client_secret': GOOGLE_CLIENT_SECRET,
                    'redirect_uri': GOOGLE_REDIRECT_URI,
                    'grant_type': 'authorization_code'
                }
            )
            if token_resp.status_code != 200:
                state_data['status'] = 'error'
                state_data['error_msg'] = 'No fue posible validar el código con Google.'
                return Response(content=render_oauth_error('Error al validar con Google.', token_resp.text), media_type='text/html', status_code=400)
            
            token_json = token_resp.json()
            access_token = token_json.get('access_token')
            if not access_token:
                state_data['status'] = 'error'
                return Response(content=render_oauth_error('No se recibió token de acceso de Google.', 'NO_ACCESS_TOKEN'), media_type='text/html', status_code=400)
            
            userinfo_resp = await client.get(
                'https://openidconnect.googleapis.com/v1/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            if userinfo_resp.status_code != 200:
                state_data['status'] = 'error'
                return Response(content=render_oauth_error('No se pudo consultar el perfil verificado en Google.', userinfo_resp.text), media_type='text/html', status_code=400)
            
            userinfo = userinfo_resp.json()
    except Exception as e:
        state_data['status'] = 'error'
        state_data['error_msg'] = str(e)
        return Response(content=render_oauth_error('Error de comunicación con el servicio de Google.', str(e)), media_type='text/html', status_code=500)

    sub = str(userinfo.get('sub', '')).strip()
    email = str(userinfo.get('email', '')).strip().lower()
    email_verified = bool(userinfo.get('email_verified', False))
    user_name = userinfo.get('name', 'Personal de Enfermería')

    if not sub or not email:
        state_data['status'] = 'error'
        return Response(content=render_oauth_error('Google no entregó identificador o correo del usuario.', 'MISSING_DATA'), media_type='text/html', status_code=400)

    if not email_verified:
        state_data['status'] = 'error'
        state_data['error_msg'] = 'El correo electrónico no está verificado en Google.'
        return Response(content=render_oauth_error('Tu cuenta de Google no tiene el correo electrónico verificado.', 'EMAIL_NOT_VERIFIED'), media_type='text/html', status_code=403)

    # REGLA: Acceso exclusivo a personal de enfermería autorizado en SAMU
    nurse = db.scalar(select(Nurse).where((Nurse.google_sub == sub) | (Nurse.email == email)))
    if not nurse or not nurse.active:
        audit(db, None, 'oauth_login_rechazado', hashlib.sha256(email.encode()).hexdigest(), None)
        db.commit()
        state_data['status'] = 'unauthorized'
        state_data['error_msg'] = f'La cuenta {email} no está autorizada como personal de enfermería en SAMU.'
        return Response(content=render_oauth_unauthorized(email), media_type='text/html', status_code=403)

    if not nurse.google_sub:
        nurse.google_sub = sub
        audit(db, nurse.id, 'vincular_google_sub', 'personal', nurse.id)
        db.commit()

    exchange_token = secrets.token_urlsafe(36)
    state_data['status'] = 'authenticated'
    state_data['exchange_token'] = exchange_token
    state_data['user_id'] = nurse.id
    state_data['expires'] = now() + timedelta(seconds=90)

    session = new_login(nurse, response)
    audit(db, nurse.id, 'login_google_exitoso', 'personal', nurse.id)
    db.commit()

    return Response(content=render_oauth_success(nurse.name or user_name, exchange_token), media_type='text/html')

@app.get('/api/auth/google/poll-session')
def poll_oauth_session(state: str):
    cleanup_oauth_states()
    if not state or state not in OAUTH_STATES:
        return {'status': 'not_found'}
    data = OAUTH_STATES[state]
    if data['status'] == 'authenticated':
        return {
            'status': 'authenticated',
            'exchange_token': data['exchange_token']
        }
    if data['status'] == 'unauthorized':
        return {
            'status': 'unauthorized',
            'detail': data.get('error_msg') or 'La cuenta seleccionada no tiene permisos de enfermería en SAMU.'
        }
    if data['status'] == 'error':
        return {
            'status': 'error',
            'detail': data.get('error_msg') or 'Ocurrió un error en la autenticación con Google.'
        }
    return {'status': 'pending'}

class FinalizeSessionRequest(BaseModel):
    state: str
    exchange_token: str

@app.post('/api/auth/google/finalize-session')
def finalize_oauth_session(body: FinalizeSessionRequest, response: Response, db = Depends(db_session)):
    cleanup_oauth_states()
    state_data = OAUTH_STATES.get(body.state)
    if not state_data or state_data.get('status') != 'authenticated':
        bad('Sesión no encontrada o no autenticada.', 401)
    if not secrets.compare_digest(state_data.get('exchange_token', ''), body.exchange_token):
        bad('Token de intercambio no válido.', 403)
    if now() > state_data.get('expires', now()):
        OAUTH_STATES.pop(body.state, None)
        bad('El token de intercambio ha expirado.', 401)
    
    user_id = state_data.get('user_id')
    OAUTH_STATES.pop(body.state, None)
    nurse = db.get(Nurse, user_id)
    if not nurse or not nurse.active:
        bad('Cuenta de enfermería deshabilitada.', 403)
    
    session = new_login(nurse, response)
    audit(db, nurse.id, 'login_google_finalizado', 'personal', nurse.id)
    db.commit()
    return {
        'user': {'name': nurse.name, 'email': nurse.email, 'role': nurse.role},
        'csrf': session.csrf
    }

@app.get('/api/catalogos/ficha')
def ficha_catalogs():return {'antecedentes_familiares':pdf.FAMILIARES,'antecedentes_personales':pdf.PERSONALES}

@app.get('/api/catalogos')
def catalogs():return {'programas':PROGRAMAS_UTGZ,'generos':sorted(GENERO_OPCIONES),'tipos_sangre':sorted(TIPOS_SANGRE),'estados_civiles':sorted(ESTADOS_CIVILES),'programa_otro':PROGRAMA_OTRO}

GENERO_OPCIONES={'Hombre','Mujer','Otro','Prefiero no especificar'}
TIPOS_SANGRE={'A+','A-','B+','B-','AB+','AB-','O+','O-','No lo sé'}
ESTADOS_CIVILES={'Soltero(a)','Casado(a)','Unión libre','Divorciado(a)','Separado(a)','Viudo(a)','Prefiero no especificar'}
PROGRAMAS_UTGZ=[
    'TSU en Administración, área Capital Humano',
    'TSU en Administración, área Formulación y Evaluación de Proyectos',
    'TSU en Agricultura Sustentable y Protegida',
    'TSU en Contaduría',
    'TSU en Energías Renovables',
    'TSU en Gastronomía',
    'TSU en Mantenimiento, área Industrial',
    'TSU en Mecatrónica, área Automatización',
    'TSU en Procesos Alimentarios',
    'TSU en Tecnologías de la Información, área Desarrollo de Software Multiplataforma',
    'TSU en Tecnologías de la Información, área Infraestructura de Redes Digitales',
    'TSU en Turismo, área Hotelería',
    'Ingeniería en Agricultura Sustentable y Protegida',
    'Ingeniería en Energías Renovables',
    'Ingeniería en Mantenimiento Industrial',
    'Ingeniería en Mecatrónica',
    'Ingeniería en Procesos Bioalimentarios',
    'Ingeniería en Redes Inteligentes y Ciberseguridad',
    'Ingeniería en Desarrollo y Gestión de Software',
    'Licenciatura en Gestión del Capital Humano',
    'Licenciatura en Innovación de Negocios y Mercadotecnia',
    'Licenciatura en Gestión y Desarrollo Turístico',
]
PROGRAMA_OTRO='Personal UTGZ / externo'

def edad_a_partir_de_fecha(fecha_nacimiento: str) -> int:
    if not isinstance(fecha_nacimiento,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',fecha_nacimiento):
        bad('Fecha de nacimiento inválida.',422)
    try: nacimiento=date.fromisoformat(fecha_nacimiento)
    except (ValueError,TypeError): bad('Fecha de nacimiento inválida.',422)
    hoy=date.today()
    edad=hoy.year-nacimiento.year-((hoy.month,hoy.day)<(nacimiento.month,nacimiento.day))
    if edad<0 or edad>120: bad('Fecha de nacimiento fuera de rango.',422)
    return edad

def normalizar_genero(valor):
    return {'Femenino':'Mujer','Masculino':'Hombre','No binario':'Otro'}.get(valor,valor if valor in GENERO_OPCIONES else '')

FICHA_TEXT=[('nombre_aspirante',True,200),('nss',False,11),('tipo_sangre',True,20),('programa_educativo',False,180),('otro_personal',False,200),('intervenciones_quirurgicas',False,220),('traumatismos',False,180),('alergia_medicamentos',False,140),('alergia_alimentos',False,140),('alergia_plantas',False,140),('alergia_ambientales',False,140),('alergia_otros',False,140),('padecimientos',False,180),('tratamiento_medico',False,180),('control_preventivo',False,180),('medicamentos_no_administrar',False,200),('nombre_medico',False,160),('telefono_medico',False,30),('hospital_preferencia',False,170),('nombre_padre_tutor',True,200),('telefono_padre_tutor',True,30)]

@app.get('/api/csrf-public')
def csrf_public():
    token = secrets.token_urlsafe(32)
    return {'csrf': token}

class OtpRequest(BaseModel):
    email: str = ''
    correo: str = ''
    nombre_aspirante: str = ''
    nombre: str = ''
    matricula: str | None = None
    sitio_web: str = ''

@app.post('/api/alumnos/verificar-correo/solicitar')
def request_email_otp(body: OtpRequest, request: Request, db=Depends(db_session)):
    # 1. Control contra automatización: trampa honeypot
    if body.sitio_web:
        bad('Solicitud inválida.', 422)

    # 2. Límite de solicitudes por IP (máximo 6 cada 15 minutos)
    client_ip = request.client.host if request.client else 'unknown'
    ip_hash = hashlib.sha256((client_ip + os.getenv('OTP_PEPPER', 'SAMU')).encode()).hexdigest()
    since = now() - timedelta(minutes=15)
    ip_reqs = db.scalar(select(func.count(Audit.id)).where(
        Audit.accion == 'solicitar_otp_correo',
        Audit.entidad == ip_hash,
        Audit.created > since
    )) or 0
    if ip_reqs >= 6:
        bad('Límite de solicitudes alcanzado. Espera 15 minutos para volver a intentar.', 429)

    # 3. Validación estricta de formato de correo
    target_email = (body.correo or body.email or '').strip()
    if not target_email:
        bad('El correo electrónico es obligatorio.', 422)
    email = valid_email(target_email)

    # 4. Protección contra duplicados SIN revelar datos personales
    mat = (body.matricula or '').strip()
    if mat:
        exist_mat = db.scalar(select(Student).where(Student.matricula == mat))
        if exist_mat:
            audit(db, None, 'intento_duplicado_matricula', ip_hash, None)
            db.commit()
            bad('Ya existe una ficha registrada con esta matrícula o correo. Si necesitas actualizar tu expediente, acude personalmente al área de Enfermería de la UTGZ.', 409)

    exist_email = db.scalar(select(Student).where(Student.email_verificacion == email))
    if exist_email:
        audit(db, None, 'intento_duplicado_correo', ip_hash, None)
        db.commit()
        bad('Ya existe una ficha registrada con esta matrícula o correo. Si necesitas actualizar tu expediente, acude personalmente al área de Enfermería de la UTGZ.', 409)

    # 5. Generar código OTP seguro de 6 dígitos
    code = f"{secrets.randbelow(900000) + 100000}"
    code_hash = hashlib.sha256(code.encode()).hexdigest()

    # Invalidar códigos previos no consumidos para este correo
    prev_otps = db.scalars(select(EmailOTP).where(EmailOTP.email == email, EmailOTP.consumed == False)).all()
    for o in prev_otps:
        o.consumed = True

    otp_record = EmailOTP(
        email=email,
        code_hash=code_hash,
        created=now(),
        expires=now() + timedelta(minutes=15),
        attempts=0,
        consumed=False
    )
    db.add(otp_record)
    audit(db, None, 'solicitar_otp_correo', ip_hash, None)
    db.commit()

    # 6. Enviar código mediante mailer.send_mail existente
    nombre = (body.nombre_aspirante or body.nombre or '').strip() or 'Estudiante'
    cuerpo = (
        f"Hola, {nombre}.\n\n"
        f"Tu código de verificación para completar el registro de tu ficha médica en SAMU UTGZ es:\n\n"
        f"    {code}\n\n"
        f"Este código es de un solo uso y tiene una vigencia de 15 minutos.\n"
        f"Al completar tu registro, tus datos serán protegidos conforme al Aviso de Privacidad Institucional.\n\n"
        f"Si no solicitaste este código, puedes hacer caso omiso de este mensaje.\n\n"
        f"Servicio de Enfermería · Universidad Tecnológica de Gutiérrez Zamora"
    )
    try:
        mailer.send_mail(to=email, subject='SAMU UTGZ · Código de verificación para ficha médica', body=cuerpo)
    except Exception as e:
        if not mailer.has_smtp():
            bad('El servidor de correo institucional no está disponible temporalmente.', 503)
        if PROD:
            bad('No se pudo enviar el correo de verificación. Verifica que esté escrito correctamente.', 500)

    res = {
        'ok': True,
        'mensaje': 'Código de verificación enviado a tu correo. Revisa tu bandeja de entrada o carpeta de spam.',
        'expira_en_minutos': 15
    }
    if not PROD:
        res['test_code'] = code
    return res

@app.post('/api/alumnos/ficha')
def post_ficha(d:dict,request:Request,db=Depends(db_session)):
    # 1. Señal anti-bot (honeypot)
    if clean(d,'sitio_web',False,150):bad('Solicitud inválida.',422)

    # 2. Límite de envíos por IP para prevenir abusos
    client_ip=request.client.host if request.client else 'unknown'
    ident=hashlib.sha256((client_ip+os.getenv('OTP_PEPPER','SAMU')).encode()).hexdigest()
    since=now()-timedelta(minutes=15)
    count=db.scalar(select(func.count(Audit.id)).where(Audit.accion=='crear_ficha_publica',Audit.entidad==ident,Audit.created>since)) or 0
    if count>=15:bad('Se alcanzó el límite temporal de envíos desde este dispositivo. Intenta más tarde.',429)

    # 3. Validación obligatoria de correo y código de verificación OTP
    correo = valid_email(clean(d, 'correo', True, 254))
    codigo_verif = clean(d, 'codigo_verificacion', True, 10).strip()

    otp = db.scalar(select(EmailOTP).where(
        EmailOTP.email == correo,
        EmailOTP.consumed == False
    ).order_by(desc(EmailOTP.created)))

    if not otp or naive_utc(otp.expires) < now():
        bad('El código de verificación ha expirado o no es válido. Solicita un nuevo código en el paso de confirmación.', 400)

    if otp.attempts >= 5:
        bad('Demasiados intentos fallidos con este código. Solicita uno nuevo.', 429)

    expected_hash = hashlib.sha256(codigo_verif.encode()).hexdigest()
    if not secrets.compare_digest(otp.code_hash, expected_hash):
        otp.attempts += 1
        db.commit()
        bad('Código de verificación incorrecto. Revisa el correo electrónico proporcionado.', 400)

    otp.consumed = True

    # 4. Matrícula opcional (para nuevo ingreso) y protección contra duplicados
    matricula_input = clean(d, 'matricula', False, 40).strip()
    matricula_val = matricula_input if matricula_input else None
    if matricula_val:
        exist_mat = db.scalar(select(Student).where(Student.matricula == matricula_val))
        if exist_mat:
            bad('Ya existe una ficha registrada con esta matrícula. Si requieres actualizar tu expediente, acude a Enfermería.', 409)

    exist_correo = db.scalar(select(Student).where(Student.email_verificacion == correo))
    if exist_correo:
        bad('Ya existe una ficha registrada con este correo electrónico. Si requieres actualizar tu expediente, acude a Enfermería.', 409)

    # 5. Validación de datos clínicos y personales
    clinical={}
    for k,req,m in FICHA_TEXT:clinical[k]=clean(d,k,req,m)
    if clinical['nss'] and not re.fullmatch(r'\d{11}',clinical['nss']):bad('El NSS debe contener 11 dígitos.',422)
    if clinical['tipo_sangre'] not in TIPOS_SANGRE:bad('Selecciona un tipo de sangre válido.',422)
    if clinical['programa_educativo'] and clinical['programa_educativo'] not in PROGRAMAS_UTGZ:bad('Selecciona una carrera o programa UTGZ válido.',422)
    nacimiento=clean(d,'fecha_nacimiento',True,10)
    edad_a_partir_de_fecha(nacimiento)
    genero=clean(d,'sexo',True,30)
    if genero not in GENERO_OPCIONES:bad('Selecciona una opción válida de sexo/género.',422)
    clinical['fecha_nacimiento']=nacimiento
    clinical['sexo']=genero
    for key,catalogue in [('antecedentes_familiares',pdf.FAMILIARES),('antecedentes_personales',pdf.PERSONALES)]:
        items=d.get(key,[])
        if not isinstance(items,list) or len(items)>len(catalogue) or not all(isinstance(v,str) and v in catalogue for v in items):bad('Antecedente fuera de la lista original.')
        clinical[key]=sorted(set(items))
    clinical['autoriza_traslado']=d.get('autoriza_traslado') is True
    if not clinical['autoriza_traslado']:bad('Se requiere autorización expresa en este formato.',422)
    clinical['firma_padre_tutor']=signature(d,'firma_padre_tutor',required=False)
    clinical['firma_aspirante']=signature(d,'firma_aspirante',required=True)
    if matricula_val:
        clinical['matricula']=matricula_val
    clinical['correo']=correo

    # 6. Registro del estudiante (matrícula opcional para nuevo ingreso)
    rec=Student(folio='PENDIENTE',nombre_aspirante=clinical['nombre_aspirante'],email_verificacion=correo,matricula=matricula_val,datos=clinical,estado='pendiente')
    db.add(rec);db.flush();rec.folio=f'FIC-{datetime.now().year}-{rec.id:05d}'
    audit(db,None,'crear_ficha','fichas_medicas',rec.id)
    audit(db,None,'crear_ficha_publica',ident,rec.id)
    db.commit()

    # Confirmación sin exponer datos médicos confidenciales
    return {'ok':True,'folio':rec.folio,'mensaje':'Ficha médica enviada a revisión de enfermería exitosamente.'}

def compute_medical_alerts(datos: dict) -> dict:
    if not datos:
        return {
            'estado': 'no_proporcionado',
            'mensaje': 'Información médica no proporcionada (pendiente de llenado de ficha médica por el estudiante).',
            'alergias': [],
            'cronicos': [],
            'contraindicados': [],
            'critico': False
        }

    # Estudiante importado que aún no llena ficha médica
    if datos.get('pre_importado') and not any(datos.get(k) for k in ['alergia_medicamentos', 'alergia_alimentos', 'padecimientos', 'antecedentes_personales', 'fecha_nacimiento']):
        return {
            'estado': 'no_proporcionado',
            'mensaje': 'Información médica no proporcionada (estudiante registrado institucionalmente, pendiente de cuestionario de salud).',
            'alergias': [],
            'cronicos': [],
            'contraindicados': [],
            'critico': False
        }

    alergias = []
    for tipo, label in [
        ('alergia_medicamentos', 'Medicamentos'),
        ('alergia_alimentos', 'Alimentos'),
        ('alergia_plantas', 'Plantas'),
        ('alergia_ambientales', 'Ambientales'),
        ('alergia_otros', 'Otros')
    ]:
        val = (datos.get(tipo) or '').strip()
        if val and val.upper() not in ('N/A', 'NA', 'NINGUNA', 'NINGUNO', 'NO', 'NO REFIERE', 'NINGUNO.', 'NINGUNA.', '-'):
            alergias.append({'tipo': label, 'detalle': val})

    cronicos = []
    for item in (datos.get('antecedentes_personales') or []):
        if isinstance(item, str) and item.strip() and item.upper() not in ('N/A', 'NA', 'NINGUNO', 'NINGUNA'):
            cronicos.append({'tipo': 'Antecedente personal', 'detalle': item.strip()})

    otro_p = (datos.get('otro_personal') or '').strip()
    if otro_p and otro_p.upper() not in ('N/A', 'NA', 'NINGUNO', 'NINGUNA', 'NO', '-'):
        cronicos.append({'tipo': 'Otro personal', 'detalle': otro_p})

    pad = (datos.get('padecimientos') or '').strip()
    if pad and pad.upper() not in ('N/A', 'NA', 'NINGUNO', 'NINGUNA', 'NO', '-'):
        cronicos.append({'tipo': 'Padecimiento actual', 'detalle': pad})

    trat = (datos.get('tratamiento_medico') or '').strip()
    if trat and trat.upper() not in ('N/A', 'NA', 'NINGUNO', 'NINGUNA', 'NO', '-'):
        cronicos.append({'tipo': 'Tratamiento activo', 'detalle': trat})

    contra = (datos.get('medicamentos_no_administrar') or '').strip()
    contraindicados = []
    if contra and contra.upper() not in ('N/A', 'NA', 'NINGUNO', 'NINGUNA', 'NO', '-'):
        contraindicados.append(contra)

    if not alergias and not cronicos and not contraindicados:
        return {
            'estado': 'sin_condiciones',
            'mensaje': 'Sin alergias, enfermedades crónicas ni restricciones médicas declaradas.',
            'alergias': [],
            'cronicos': [],
            'contraindicados': [],
            'critico': False
        }

    return {
        'estado': 'con_alertas',
        'mensaje': f'Atención: {len(alergias)} alergia(s), {len(cronicos)} antecedente(s) y {len(contraindicados)} restricción(es) registradas.',
        'alergias': alergias,
        'cronicos': cronicos,
        'contraindicados': contraindicados,
        'critico': len(alergias) > 0 or len(contraindicados) > 0
    }

@app.get('/api/resumen')
def dashboard(current=Depends(authenticated),db=Depends(db_session)):
    today_str = datetime.now().strftime('%Y-%m-%d')
    this_month_str = datetime.now().strftime('%Y-%m')

    pendientes = db.scalar(select(func.count(Student.id)).where(Student.estado=='pendiente')) or 0
    validadas = db.scalar(select(func.count(Student.id)).where(Student.estado=='validada')) or 0
    total_atenciones = db.scalar(select(func.count(Attention.id))) or 0
    total_canalizaciones = db.scalar(select(func.count(Referral.id))) or 0

    atenciones_hoy = db.scalar(select(func.count(Attention.id)).where(Attention.fecha == today_str)) or 0
    atenciones_mes = db.scalar(select(func.count(Attention.id)).where(Attention.fecha.like(f"{this_month_str}-%"))) or 0

    alumnos_atendidos_total = db.scalar(select(func.count(func.distinct(Attention.matricula)))) or 0
    alumnos_atendidos_mes = db.scalar(select(func.count(func.distinct(Attention.matricula))).where(Attention.fecha.like(f"{this_month_str}-%"))) or 0
    canalizaciones_mes = db.scalar(select(func.count(Referral.id)).where(Referral.fecha.like(f"{this_month_str}-%"))) or 0

    all_inventory = db.scalars(select(Inventory)).all()
    total_insumos = len(all_inventory)

    agotados_count = 0
    stock_bajo_count = 0
    por_caducar_count = 0
    caducados_count = 0
    today_date = datetime.now().date()

    for item in all_inventory:
        stock_min = getattr(item, 'stock_minimo', 3)
        if stock_min is None: stock_min = 3
        if item.cantidad_fin <= 0:
            agotados_count += 1
        elif item.cantidad_fin <= stock_min:
            stock_bajo_count += 1

        try:
            exp_date = datetime.strptime(item.fecha_caducidad, '%Y-%m-%d').date()
            diff = (exp_date - today_date).days
            if diff < 0:
                caducados_count += 1
            elif diff <= 60:
                por_caducar_count += 1
        except Exception:
            pass

    ultimas_atenciones = [
        {
            'id': a.id,
            'fecha': a.fecha,
            'hora': a.hora,
            'nombre': a.nombre,
            'matricula': a.matricula,
            'motivo': (a.datos or {}).get('motivo_consulta', 'Consulta general')
        }
        for a in db.scalars(select(Attention).order_by(desc(Attention.fecha), desc(Attention.hora), desc(Attention.id)).limit(6)).all()
    ]

    grafica_meses = []
    meses_nombres = {'01':'Ene','02':'Feb','03':'Mar','04':'Abr','05':'May','06':'Jun','07':'Jul','08':'Ago','09':'Sep','10':'Oct','11':'Nov','12':'Dic'}
    cur_year = datetime.now().year
    cur_month = datetime.now().month
    for i in range(5, -1, -1):
        m = cur_month - i
        y = cur_year
        while m <= 0:
            m += 12
            y -= 1
        ym_str = f"{y:04d}-{m:02d}"
        count = db.scalar(select(func.count(Attention.id)).where(Attention.fecha.like(f"{ym_str}-%"))) or 0
        grafica_meses.append({
            'periodo': ym_str,
            'label': f"{meses_nombres.get(f'{m:02d}', '')} {str(y)[2:]}",
            'total': count
        })

    return {
        'pendientes': pendientes,
        'validadas': validadas,
        'atenciones': total_atenciones,
        'canalizaciones': total_canalizaciones,
        'insumos': total_insumos,
        'stock_bajo': stock_bajo_count,
        'atenciones_hoy': atenciones_hoy,
        'atenciones_mes': atenciones_mes,
        'alumnos_atendidos_total': alumnos_atendidos_total,
        'alumnos_atendidos_mes': alumnos_atendidos_mes,
        'canalizaciones_mes': canalizaciones_mes,
        'inventario_alertas': {
            'agotados': agotados_count,
            'stock_bajo': stock_bajo_count,
            'por_caducar': por_caducar_count,
            'caducados': caducados_count,
            'total_alertas': agotados_count + stock_bajo_count + por_caducar_count + caducados_count
        },
        'ultimas_atenciones': ultimas_atenciones,
        'grafica_mensual': grafica_meses
    }

def student_summary(a):
    return {'id':a.id,'folio':a.folio,'nombre_aspirante':a.nombre_aspirante,'email_verificacion':a.email_verificacion,'estado':a.estado,'matricula':a.matricula,'created':a.created.isoformat() if a.created else None}

@app.get('/api/fichas')
def list_fichas(estado:str='',q:str='',current=Depends(authenticated),db=Depends(db_session)):
    query=select(Student).order_by(desc(Student.id)).limit(200)
    if estado in ('pendiente','validada'):query=query.where(Student.estado==estado)
    if q.strip():
        term='%'+q.strip()[:80]+'%';query=query.where(or_(Student.nombre_aspirante.ilike(term),Student.matricula.ilike(term),Student.folio.ilike(term)))
    return [student_summary(a) for a in db.scalars(query)]

@app.get('/api/fichas/{ident}')
def get_ficha(ident:int,current=Depends(authenticated),db=Depends(db_session)):
    a=db.get(Student,ident)
    if not a:bad('Ficha inexistente.',404)
    audit(db,current[0].id,'consultar_ficha','fichas_medicas',ident);db.commit()
    datos=a.datos or {}
    edad=edad_a_partir_de_fecha(datos['fecha_nacimiento']) if datos.get('fecha_nacimiento') else None
    alerts=compute_medical_alerts(datos)
    return {**student_summary(a),'edad_actual':edad,'datos':datos,'foto':(a.foto or {}).get('data',''),'alertas_medicas':alerts}

@app.get('/api/fichas/{ident}/historial')
def student_history(ident:int,anio:str='',mes:str='',current=Depends(authenticated),db=Depends(db_session)):
    a=db.get(Student,ident)
    if not a:bad('Ficha inexistente.',404)

    cond_att = [Attention.student_id == a.id]
    if a.matricula:
        cond_att.append(Attention.matricula == a.matricula)
    att_query = select(Attention).where(or_(*cond_att))
    if anio:
        att_query = att_query.where(Attention.fecha.like(f"{anio}-%"))
    if mes:
        att_query = att_query.where(Attention.fecha.like(f"{mes}-%"))
    attentions = db.scalars(att_query.order_by(desc(Attention.fecha), desc(Attention.hora))).all()

    cond_ref = [Referral.student_id == a.id]
    if a.nombre_aspirante:
        cond_ref.append(Referral.nombre == a.nombre_aspirante)
    ref_query = select(Referral).where(or_(*cond_ref))
    if anio:
        ref_query = ref_query.where(Referral.fecha.like(f"{anio}-%"))
    if mes:
        ref_query = ref_query.where(Referral.fecha.like(f"{mes}-%"))
    referrals_all = db.scalars(ref_query.order_by(desc(Referral.fecha), desc(Referral.created))).all()
    referrals = [r for r in referrals_all if r.student_id == a.id or (r.datos or {}).get('matricula_empleado') == a.matricula or r.nombre == a.nombre_aspirante]

    items = []
    for att in attentions:
        d = att.datos or {}
        items.append({
            'tipo': 'atencion',
            'id': att.id,
            'fecha': att.fecha,
            'hora': att.hora,
            'motivo': d.get('motivo_consulta', 'Atención médica en enfermería'),
            'detalles': {
                'toma_ta': d.get('toma_ta', ''),
                'otro_procedimiento': d.get('otro_procedimiento', ''),
                'suministro_medicamento': d.get('suministro_medicamento', ''),
                'material_curacion': d.get('material_curacion', ''),
                'programa_educativo': d.get('programa_educativo', ''),
                'grupo': d.get('grupo', '')
            }
        })

    for ref in referrals:
        d = ref.datos or {}
        items.append({
            'tipo': 'canalizacion',
            'id': ref.id,
            'fecha': ref.fecha,
            'hora': d.get('hora', ''),
            'motivo': d.get('motivo_canalizacion', 'Canalización externa a servicios de salud'),
            'detalles': {
                'ta': d.get('ta', ''),
                'fc': d.get('fc', ''),
                'sato2': d.get('sato2', ''),
                'fr': d.get('fr', ''),
                'temperatura': d.get('temperatura', ''),
                'elaboro': d.get('elaboro', ''),
                'domicilio': d.get('domicilio', '')
            }
        })

    items.sort(key=lambda x: (x.get('fecha', ''), x.get('hora', '')), reverse=True)

    return {
        'student': {
            'id': a.id,
            'nombre': a.nombre_aspirante,
            'matricula': a.matricula or '',
            'folio': a.folio,
            'programa_educativo': (a.datos or {}).get('programa_educativo', ''),
            'grupo': (a.datos or {}).get('grupo', '')
        },
        'total_atenciones': len(attentions),
        'total_canalizaciones': len(referrals),
        'total_eventos': len(items),
        'items': items
    }

@app.post('/api/fichas/{ident}/validar')
def validate_ficha(ident:int,d:dict,current=Depends(authenticated),db=Depends(db_session)):
    a=db.get(Student,ident)
    if not a:bad('Ficha inexistente.',404)
    matricula=clean(d,'matricula',True,40)
    correo=valid_email(clean(d,'correo',True,254))
    if a.estado=='validada':bad('La ficha ya está validada.',409)
    a.matricula=matricula
    a.email_verificacion=correo
    a.foto=photograph(d.get('foto',''))
    a.estado='validada';a.validated=now();a.validated_by=current[0].id
    audit(db,current[0].id,'validar_ficha','fichas_medicas',a.id)
    try:db.commit()
    except IntegrityError:db.rollback();bad('Matrícula ya utilizada en otra ficha.',409)
    return {'ok':True}

@app.put('/api/fichas/{ident}/correo')
def update_student_email(ident:int,d:dict,current=Depends(authenticated),db=Depends(db_session)):
    a=db.get(Student,ident)
    if not a:bad('Ficha inexistente.',404)
    a.email_verificacion=valid_email(clean(d,'correo',True,254))
    audit(db,current[0].id,'actualizar_correo_alumno','fichas_medicas',ident)
    db.commit()
    return {'ok':True}

@app.put('/api/fichas/{ident}')
def update_ficha_completa(ident:int,d:dict,current=Depends(authenticated),db=Depends(db_session)):
    a=db.get(Student,ident)
    if not a:bad('Ficha inexistente.',404)

    # 1. Nombre completo
    if 'nombre_aspirante' in d and str(d['nombre_aspirante']).strip():
        a.nombre_aspirante=clean(d,'nombre_aspirante',True,200)

    # 2. Matrícula
    if 'matricula' in d:
        nueva_mat=(d.get('matricula') or '').strip()
        if nueva_mat:
            nueva_mat=nueva_mat[:40]
            otro=db.scalar(select(Student).where(Student.matricula==nueva_mat,Student.id!=a.id))
            if otro:bad(f'La matrícula {nueva_mat} ya está registrada en otra ficha.',409)
            a.matricula=nueva_mat
        else:
            if a.estado=='validada':bad('Un expediente validado debe conservar su matrícula.',400)
            a.matricula=None

    # 3. Correo institucional
    if 'correo' in d and d.get('correo'):
        a.email_verificacion=valid_email(clean(d,'correo',True,254))
    elif 'email_verificacion' in d and d.get('email_verificacion'):
        a.email_verificacion=valid_email(clean(d,'email_verificacion',True,254))

    # 4. Fotografía
    if 'foto' in d and d.get('foto'):
        a.foto=photograph(d['foto'])

    # 5. Estado
    if d.get('validar_ahora') and a.matricula and a.email_verificacion:
        a.estado='validada'
        if not a.validated:
            a.validated=now()
            a.validated_by=current[0].id

    # 6. Datos clínicos, académicos y personales
    curr_datos=dict(a.datos or {})
    campos_texto=[
        'fecha_nacimiento','sexo','nss','tipo_sangre','programa_educativo','grupo',
        'otro_personal','intervenciones_quirurgicas','traumatismos',
        'alergia_medicamentos','alergia_alimentos','alergia_plantas','alergia_ambientales','alergia_otros',
        'padecimientos','tratamiento_medico','control_preventivo','medicamentos_no_administrar',
        'nombre_medico','telefono_medico','hospital_preferencia',
        'nombre_padre_tutor','telefono_padre_tutor'
    ]
    for k in campos_texto:
        if k in d:
            val=d.get(k)
            curr_datos[k]=(str(val).strip() if val is not None else '')

    if 'autoriza_traslado' in d:
        curr_datos['autoriza_traslado']=bool(d.get('autoriza_traslado'))

    for k in ['antecedentes_familiares','antecedentes_personales']:
        if k in d:
            val=d.get(k)
            if isinstance(val,list):
                curr_datos[k]=[str(x).strip() for x in val if str(x).strip()]
            elif isinstance(val,str) and val.strip():
                curr_datos[k]=[x.strip() for x in val.split(',') if x.strip()]
            else:
                curr_datos[k]=[]

    curr_datos['nombre_aspirante']=a.nombre_aspirante
    if a.matricula:curr_datos['matricula']=a.matricula
    if a.email_verificacion:curr_datos['email_verificacion']=a.email_verificacion
    if 'pre_importado' in curr_datos:curr_datos['pre_importado']=False

    a.datos=curr_datos
    audit(db,current[0].id,'editar_ficha_medica','fichas_medicas',a.id)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        bad('Error de integridad: matrícula duplicada.',409)

    return {'ok':True,'mensaje':'Expediente actualizado exitosamente'}

@app.get('/api/estudiantes/plantilla')
def download_student_template(formato:str='csv',current=Depends(authenticated)):
    if formato == 'xlsx':
        content = importer.generate_template_excel()
        return Response(
            content=content,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename="plantilla_estudiantes_utgz.xlsx"'}
        )
    content = importer.generate_template_csv()
    return Response(
        content=content,
        media_type='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename="plantilla_estudiantes_utgz.csv"'}
    )

@app.post('/api/estudiantes/importar/preview')
async def preview_import_students(file:UploadFile=File(...),current=Depends(authenticated),db=Depends(db_session)):
    content = await file.read()
    if len(content) > 10_000_000:
        bad('El archivo supera el límite de 10 MB.', 413)
    rows = importer.parse_student_file(content, file.filename or '')
    if not rows:
        bad('No se encontraron registros en el archivo o el formato no es compatible.', 400)

    # Detect duplicates by matricula in DB
    matriculas = [r['matricula'] for r in rows if r.get('matricula')]
    existing_students = {}
    if matriculas:
        found = db.scalars(select(Student).where(Student.matricula.in_(matriculas))).all()
        for s in found:
            existing_students[s.matricula] = s

    nuevos = []
    duplicados = []
    errores = []

    seen_mats = set()
    for r in rows:
        if r.get('error'):
            errores.append(r)
            continue

        mat = r['matricula']
        if mat in seen_mats:
            errores.append({**r, 'error': f"Matrícula duplicada en el archivo: {mat}"})
            continue
        seen_mats.add(mat)

        if mat in existing_students:
            curr = existing_students[mat]
            curr_datos = curr.datos or {}
            duplicados.append({
                'fila': r['fila'],
                'matricula': mat,
                'nombre_archivo': r['nombre_completo'],
                'nombre_actual': curr.nombre_aspirante,
                'carrera_archivo': r['carrera'],
                'carrera_actual': curr_datos.get('programa_educativo', ''),
                'grupo_archivo': r['grupo'],
                'grupo_actual': curr_datos.get('grupo', ''),
                'correo_archivo': r['correo'],
                'correo_actual': curr.email_verificacion or '',
                'accion': 'actualizar'
            })
        else:
            nuevos.append({
                'fila': r['fila'],
                'matricula': mat,
                'nombre_completo': r['nombre_completo'],
                'carrera': r['carrera'],
                'grupo': r['grupo'],
                'correo': r['correo'],
                'accion': 'crear'
            })

    return {
        'ok': True,
        'total': len(rows),
        'nuevos_count': len(nuevos),
        'duplicados_count': len(duplicados),
        'errores_count': len(errores),
        'nuevos': nuevos,
        'duplicados': duplicados,
        'errores': errores
    }

@app.post('/api/estudiantes/importar')
async def execute_import_students(file:UploadFile=File(...),actualizar_duplicados:bool=Form(True),current=Depends(authenticated),db=Depends(db_session)):
    content = await file.read()
    rows = importer.parse_student_file(content, file.filename or '')
    if not rows:
        bad('No se encontraron registros para importar.', 400)

    creados = 0
    actualizados = 0
    errores = []

    seen_mats = set()
    cur_year = datetime.now().year

    for r in rows:
        if r.get('error'):
            errores.append(r)
            continue

        mat = r['matricula']
        if mat in seen_mats:
            errores.append({**r, 'error': f"Matrícula duplicada dentro del archivo ({mat})"})
            continue
        seen_mats.add(mat)

        existing = db.scalar(select(Student).where(Student.matricula == mat))
        if existing:
            if actualizar_duplicados:
                existing.nombre_aspirante = r['nombre_completo']
                if r.get('correo'):
                    existing.email_verificacion = r['correo']
                curr_datos = dict(existing.datos or {})
                if r.get('carrera'):
                    curr_datos['programa_educativo'] = r['carrera']
                if r.get('grupo'):
                    curr_datos['grupo'] = r['grupo']
                # Preservar datos médicos originales intactos
                existing.datos = curr_datos
                actualizados += 1
        else:
            new_student = Student(
                folio='PENDIENTE',
                nombre_aspirante=r['nombre_completo'],
                email_verificacion=r.get('correo', ''),
                estado='validada',
                matricula=mat,
                datos={
                    'nombre_aspirante': r['nombre_completo'],
                    'programa_educativo': r.get('carrera', ''),
                    'grupo': r.get('grupo', ''),
                    'nss': '',
                    'tipo_sangre': '',
                    'fecha_nacimiento': '',
                    'sexo': '',
                    'antecedentes_familiares': [],
                    'antecedentes_personales': [],
                    'pre_importado': True
                }
            )
            db.add(new_student)
            db.flush()
            new_student.folio = f'FIC-{cur_year}-{new_student.id:05d}'
            creados += 1

    audit(db, current[0].id, 'importar_estudiantes', 'fichas_medicas')
    db.commit()

    return {
        'ok': True,
        'creados': creados,
        'actualizados': actualizados,
        'errores_count': len(errores),
        'errores': errores
    }

@app.get('/api/estudiantes')
def students_for_select(current=Depends(authenticated),db=Depends(db_session)):
    result=[]
    for a in db.scalars(select(Student).where(Student.estado=='validada').order_by(Student.nombre_aspirante).limit(500)):
        d=a.datos or {}
        alerts = compute_medical_alerts(d)
        result.append({'id':a.id,'nombre':a.nombre_aspirante,'matricula':a.matricula,'correo':a.email_verificacion,
            'edad':edad_a_partir_de_fecha(d['fecha_nacimiento']) if d.get('fecha_nacimiento') else None,
            'sexo':normalizar_genero(d.get('sexo','')),'nss':d.get('nss',''),'tipo_sangre':d.get('tipo_sangre',''),
            'programa_educativo':d.get('programa_educativo',''),'grupo':d.get('grupo',''),
            'contacto_emergencia':d.get('nombre_padre_tutor',''),
            'telefono_emergencia':d.get('telefono_padre_tutor',''),
            'alertas_medicas': alerts})
    return result

ATTENTION_FIELDS=[('fecha',True,10),('hora',True,5),('nombre',True,200),('matricula',True,60),('edad',False,3),('sexo',False,30),('programa_educativo',False,160),('grupo',False,40),('motivo_consulta',True,450),('toma_ta',False,70),('otro_procedimiento',False,450),('suministro_medicamento',False,220),('material_curacion',False,220)]
@app.post('/api/bitacora')
def post_attention(d:dict,current=Depends(authenticated),db=Depends(db_session)):
    values={k:clean(d,k,required,n) for k,required,n in ATTENTION_FIELDS}
    if values['sexo'] and values['sexo'] not in GENERO_OPCIONES:bad('Selecciona una opción válida de sexo/género.',422)
    if values['programa_educativo'] and values['programa_educativo'] not in PROGRAMAS_UTGZ:bad('Selecciona una carrera o programa UTGZ válido.',422)
    valid_date(values['fecha']);valid_time(values['hora'])
    values['firma_usuario']=signature(d,'firma_usuario')
    values['firma_enfermeria']=signature(d,'firma_enfermeria')
    student_id=d.get('student_id') or None
    if student_id:
        a=db.get(Student,int(student_id))
        if not a or a.estado!='validada':bad('La ficha del alumno no está validada.',422)
        if a.matricula!=values['matricula']:bad('La matrícula no coincide con el alumno.',422)
    a=Attention(student_id=student_id,nombre=values['nombre'],matricula=values['matricula'],fecha=values['fecha'],hora=values['hora'],datos=values,creator_id=current[0].id)
    db.add(a);db.flush();audit(db,current[0].id,'crear_atencion','bitacora',a.id);db.commit()
    return {'ok':True,'id':a.id}

@app.get('/api/bitacora')
def list_attention(mes:str='',current=Depends(authenticated),db=Depends(db_session)):
    query=select(Attention).order_by(desc(Attention.fecha),desc(Attention.hora),desc(Attention.id)).limit(1000 if mes else 200)
    if mes:
        if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])',mes):bad('El mes debe tener formato AAAA-MM.')
        query=query.where(Attention.fecha.like(mes+'-%'))
    items=db.scalars(query).all()
    return [{'id':a.id,'fecha':a.fecha,'hora':a.hora,'nombre':a.nombre,'matricula':a.matricula,'datos':a.datos} for a in items]

REFERRAL_FIELDS=[('nombre_completo',True,200),('nss',False,25),('sexo',True,30),('edad',True,3),('estado_civil',True,60),('programa_puesto',True,180),('matricula_empleado',True,60),('telefono_celular',True,40),('contacto_emergencia',True,200),('telefono_emergencia',True,40),('domicilio',True,260),('correo_electronico',True,254),('motivo_canalizacion',True,800),('ta',False,30),('fc',False,30),('sato2',False,30),('fr',False,30),('temperatura',False,30),('fecha',True,10),('hora',True,5),('elaboro',True,200)]
@app.post('/api/canalizaciones')
def post_referral(d:dict,current=Depends(authenticated),db=Depends(db_session)):
    values={k:clean(d,k,req,m) for k,req,m in REFERRAL_FIELDS}
    valid_date(values['fecha']);valid_time(values['hora']);valid_email(values['correo_electronico'])
    if values['sexo'] not in GENERO_OPCIONES:bad('Selecciona una opción válida de sexo/género.',422)
    if values['estado_civil'] not in ESTADOS_CIVILES:bad('Selecciona un estado civil válido.',422)
    if values['programa_puesto'] not in (*PROGRAMAS_UTGZ,PROGRAMA_OTRO):bad('Selecciona una carrera, programa o puesto válido.',422)
    if values['nss'] and not re.fullmatch(r'\d{11}',values['nss']):bad('El NSS debe contener 11 dígitos.',422)
    values['consentimiento_informado']=d.get('consentimiento_informado') is True
    if not values['consentimiento_informado']:bad('Debe constar el consentimiento antes de generar la canalización.',422)
    values['firma_responsable']=signature(d,'firma_responsable')
    values['firma_consentimiento']=signature(d,'firma_consentimiento')
    student_id=d.get('student_id') or None
    if student_id:
        a=db.get(Student,int(student_id))
        if not a or a.estado!='validada':bad('Selecciona una ficha validada.',422)
        if values['nombre_completo']!=a.nombre_aspirante:bad('El nombre no coincide con la ficha seleccionada.',422)
    r=Referral(student_id=student_id,nombre=values['nombre_completo'],fecha=values['fecha'],datos=values,creator_id=current[0].id)
    db.add(r);db.flush();audit(db,current[0].id,'crear_canalizacion','canalizaciones',r.id);db.commit()
    return {'ok':True,'id':r.id}

@app.get('/api/canalizaciones')
def list_referrals(current=Depends(authenticated),db=Depends(db_session)):
    items=db.scalars(select(Referral).order_by(desc(Referral.id)).limit(200)).all()
    return [{'id':a.id,'fecha':a.fecha,'nombre':a.nombre,'datos':a.datos} for a in items]

def inventory_status(fecha_caducidad: str, cantidad_fin: int, stock_minimo: int):
    dias_restantes = None
    try:
        exp_date = datetime.strptime(fecha_caducidad, '%Y-%m-%d').date()
        today_date = datetime.now().date()
        dias_restantes = (exp_date - today_date).days
    except Exception:
        pass

    if cantidad_fin <= 0:
        return {'estado': 'agotado', 'color': 'rojo', 'nivel': 3, 'etiqueta': 'Agotado (0 existencias)', 'dias_caducidad': dias_restantes}
    if dias_restantes is not None and dias_restantes < 0:
        return {'estado': 'caducado', 'color': 'rojo', 'nivel': 3, 'etiqueta': f'Caducado hace {abs(dias_restantes)} días', 'dias_caducidad': dias_restantes}
    if cantidad_fin <= stock_minimo:
        return {'estado': 'stock_bajo', 'color': 'amarillo', 'nivel': 2, 'etiqueta': f'Stock bajo ({cantidad_fin} de {stock_minimo} mín.)', 'dias_caducidad': dias_restantes}
    if dias_restantes is not None and dias_restantes <= 60:
        return {'estado': 'por_caducar', 'color': 'amarillo', 'nivel': 2, 'etiqueta': f'Por caducar en {dias_restantes} días', 'dias_caducidad': dias_restantes}
    return {'estado': 'optimo', 'color': 'verde', 'nivel': 1, 'etiqueta': 'Existencias óptimas', 'dias_caducidad': dias_restantes}

def inventory_dict(a):
    stock_min = getattr(a, 'stock_minimo', 3)
    if stock_min is None: stock_min = 3
    status = inventory_status(a.fecha_caducidad, a.cantidad_fin, stock_min)
    return {
        'id': a.id,
        'medicamento_material': a.medicamento_material,
        'descripcion': a.descripcion,
        'fecha_caducidad': a.fecha_caducidad,
        'cantidad_inicio': a.cantidad_inicio,
        'cantidad_fin': a.cantidad_fin,
        'stock_minimo': stock_min,
        'cuatrimestre': a.cuatrimestre,
        'estado_stock': status
    }

@app.get('/api/inventario')
def list_inventory(cuatrimestre:str='',filtro_estado:str='',current=Depends(authenticated),db=Depends(db_session)):
    query=select(Inventory).order_by(Inventory.medicamento_material)
    if cuatrimestre:query=query.where(Inventory.cuatrimestre==cuatrimestre)
    items = [inventory_dict(a) for a in db.scalars(query)]
    if filtro_estado == 'agotados':
        items = [i for i in items if i['estado_stock']['estado'] in ('agotado', 'caducado')]
    elif filtro_estado == 'stock_bajo':
        items = [i for i in items if i['estado_stock']['estado'] == 'stock_bajo']
    elif filtro_estado == 'por_caducar':
        items = [i for i in items if i['estado_stock']['estado'] in ('por_caducar', 'caducado')]
    elif filtro_estado == 'optimo':
        items = [i for i in items if i['estado_stock']['estado'] == 'optimo']
    elif filtro_estado == 'criticos':
        items = [i for i in items if i['estado_stock']['estado'] != 'optimo']
    return items

@app.post('/api/inventario')
def post_inventory(d:dict,current=Depends(authenticated),db=Depends(db_session)):
    values={k:clean(d,k,req,m) for k,req,m in [('medicamento_material',True,240),('descripcion',False,500),('fecha_caducidad',True,10),('cuatrimestre',True,120)]}
    valid_date(values['fecha_caducidad'])
    values['cantidad_inicio']=int_val(d,'cantidad_inicio');values['cantidad_fin']=int_val(d,'cantidad_fin')
    stock_min = int_val(d, 'stock_minimo') if 'stock_minimo' in d and str(d.get('stock_minimo')).strip() else 3
    if stock_min < 0: stock_min = 0
    values['stock_minimo'] = stock_min
    a=Inventory(**values);db.add(a);db.flush();audit(db,current[0].id,'crear_insumo','inventario',a.id);db.commit()
    return {'ok':True,'id':a.id}

@app.put('/api/inventario/{ident}')
def update_inventory(ident:int,d:dict,current=Depends(authenticated),db=Depends(db_session)):
    a=db.get(Inventory,ident)
    if not a:bad('Insumo inexistente.',404)
    for k,req,m in [('medicamento_material',True,240),('descripcion',False,500),('fecha_caducidad',True,10),('cuatrimestre',True,120)]:setattr(a,k,clean(d,k,req,m))
    valid_date(a.fecha_caducidad)
    a.cantidad_inicio=int_val(d,'cantidad_inicio');a.cantidad_fin=int_val(d,'cantidad_fin')
    if 'stock_minimo' in d and str(d.get('stock_minimo')).strip():
        a.stock_minimo = max(0, int_val(d, 'stock_minimo'))
    a.updated=now()
    audit(db,current[0].id,'editar_insumo','inventario',a.id);db.commit()
    return {'ok':True}

@app.get('/api/contactos')
def list_contacts(current=Depends(authenticated),db=Depends(db_session)):
    return [{'id':a.id,'nombre':a.nombre,'correo':a.correo,'area':a.area,'activo':a.activo} for a in db.scalars(select(Contact).order_by(Contact.nombre))]

@app.post('/api/contactos')
def post_contact(d:dict,current=Depends(requires_admin),db=Depends(db_session)):
    c=Contact(nombre=clean(d,'nombre',True,200),correo=valid_email(clean(d,'correo',True,254)),area=clean(d,'area',False,200))
    db.add(c)
    try:db.flush()
    except IntegrityError:db.rollback();bad('Ese correo ya está registrado.',409)
    audit(db,current[0].id,'agregar_contacto','destinatarios',c.id);db.commit()
    return {'ok':True,'id':c.id}

@app.put('/api/contactos/{ident}')
def put_contact(ident:int,d:dict,current=Depends(requires_admin),db=Depends(db_session)):
    a=db.get(Contact,ident)
    if not a:bad('Contacto no encontrado.',404)
    a.nombre=clean(d,'nombre',True,200);a.correo=valid_email(clean(d,'correo',True,254));a.area=clean(d,'area',False,200)
    a.activo=bool(d.get('activo',True));audit(db,current[0].id,'editar_contacto','destinatarios',a.id)
    try:db.commit()
    except IntegrityError:db.rollback();bad('El correo ya pertenece a otro contacto.',409)
    return {'ok':True}

@app.delete('/api/contactos/{ident}')
def delete_contact(ident:int,current=Depends(requires_admin),db=Depends(db_session)):
    a=db.get(Contact,ident)
    if not a:bad('Contacto no encontrado.',404)
    # Si tiene registros vinculados en bitácora de envíos, lo desactivamos para preservar integridad
    has_logs = db.scalars(select(MailLog).where(MailLog.contact_id==ident)).first()
    if has_logs:
        a.activo = False
        audit(db,current[0].id,'desactivar_contacto','destinatarios',a.id)
        db.commit()
        return {'ok':True,'message':'El contacto cuenta con historial de envíos de canalizaciones y fue desactivado para preservar la bitácora.'}
    db.delete(a)
    audit(db,current[0].id,'eliminar_contacto','destinatarios',ident)
    db.commit()
    return {'ok':True}

@app.post('/api/canalizaciones/{ident}/enviar')
def send_referral(ident:int,d:dict,current=Depends(authenticated),db=Depends(db_session)):
    if not mailer.has_smtp():bad('Configura SMTP_HOST y SMTP_FROM para enviar correos reales.',503)
    ref=db.get(Referral,ident)
    if not ref:bad('Canalización inexistente.',404)
    ids=d.get('contact_ids',[])
    if not isinstance(ids,list) or not ids or len(ids)>15 or any(not isinstance(n,int) for n in ids):bad('Selecciona de 1 a 15 destinatarios guardados.')
    ids=list(dict.fromkeys(ids))
    contacts=db.scalars(select(Contact).where(Contact.id.in_(ids),Contact.activo==True)).all()
    if len(contacts)!=len(ids):bad('Algún correo no está registrado o está desactivado.',422)
    attachment=pdf.referral_pdf(ref)
    sent=[];failed=[]
    for contact in contacts:
        try:
            mailer.send_mail(contact.correo,'Canalización externa - Enfermería UTGZ',
                'Se adjunta canalización externa emitida por el área de Enfermería de la UTGZ.\nEste documento contiene información personal sensible. Trátelo de forma confidencial.\n',
                attachment,f'canalizacion_{ident}.pdf')
            status='enviado';reason='';sent.append(contact.correo)
        except Exception:
            status='error';reason='Error de entrega SMTP. Revisa las credenciales y el servicio.';failed.append(contact.correo)
        db.add(MailLog(referral_id=ident,contact_id=contact.id,sent_by=current[0].id,estado=status,error=reason))
    audit(db,current[0].id,'enviar_canalizacion','canalizaciones',ident);db.commit()
    return {'ok':not failed,'enviados':sent,'fallidos':failed,'mensaje':'SMTP aceptó el envío; no implica lectura ni entrega final al buzón.'}

@app.get('/api/canalizaciones/{ident}/envios')
def referral_logs(ident:int,current=Depends(authenticated),db=Depends(db_session)):
    records=db.scalars(select(MailLog).where(MailLog.referral_id==ident).order_by(desc(MailLog.id))).all()
    return [{'id':r.id,'contact_id':r.contact_id,'estado':r.estado,'fecha':r.sent_at.isoformat()} for r in records]

# Descargas de un único uso: así el APK Flutter puede abrir PDF en el navegador del sistema
# sin compartir cookies de sesión ni exponer archivos públicos.
@app.post('/api/descargas')
def prepare_download(d:dict,current=Depends(authenticated),db=Depends(db_session)):
    tipo=clean(d,'tipo',True,30)
    if tipo not in ('ficha','canalizacion','bitacora','inventario'):bad('Tipo de documento no permitido.')
    ident=d.get('id') or None
    if tipo in ('ficha','canalizacion'):
        try: ident=int(ident)
        except (ValueError,TypeError):bad('ID de documento inválido.')
        entity=Student if tipo=='ficha' else Referral
        if not db.get(entity,ident):bad('Documento inexistente.',404)
    else:ident=None
    filtro=clean(d,'cuatrimestre',False,120) if tipo=='inventario' else ''
    if tipo=='bitacora':
        filtro=clean(d,'mes',False,7)
        if filtro and not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])',filtro):bad('El mes debe tener formato AAAA-MM.')
    raw=secrets.token_urlsafe(40)
    db.add(DownloadToken(token_hash=hash_token(raw),user_id=current[0].id,tipo=tipo,entidad_id=ident,filtro=filtro,expires=now()+timedelta(seconds=90)))
    db.commit()
    return {'url':f'/descargar/{raw}','vence_en_segundos':90}

@app.get('/descargar/{token}')
def download(token:str,db=Depends(db_session)):
    if len(token)>100:bad('Enlace inválido.',404)
    row=db.scalar(select(DownloadToken).where(DownloadToken.token_hash==hash_token(token)))
    if not row or row.used or naive_utc(row.expires)<now():bad('Enlace vencido o utilizado.',410)
    user=db.get(Nurse,row.user_id)
    if not user or not user.active:bad('Acceso revocado.',403)
    row.used=True
    kind,ident,filtro=row.tipo,row.entidad_id,row.filtro
    if kind=='ficha':
        rec=db.get(Student,ident);payload=pdf.ficha_pdf(rec);name=f'ficha_{rec.folio}.pdf'
    elif kind=='canalizacion':
        rec=db.get(Referral,ident);payload=pdf.referral_pdf(rec);name=f'canalizacion_{ident}.pdf'
    elif kind=='bitacora':
        q=select(Attention).order_by(Attention.fecha,Attention.hora,Attention.id).limit(1000)
        if filtro:q=q.where(Attention.fecha.like(filtro+'-%'))
        rec=db.scalars(q).all();payload=pdf.bitacora_pdf(rec,filtro);name=f'bitacora_{filtro}.pdf' if filtro else 'bitacora_enfermeria.pdf'
    else:
        q=select(Inventory).order_by(Inventory.medicamento_material).limit(1000)
        if filtro:q=q.where(Inventory.cuatrimestre==filtro)
        rec=db.scalars(q).all();payload=pdf.inventory_pdf(rec,filtro);name='inventario_enfermeria.pdf'
    audit(db,user.id,'descargar_pdf',kind,ident);db.commit()
    return Response(payload,media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="{name}"','Cache-Control':'no-store, private','X-Content-Type-Options':'nosniff'})
