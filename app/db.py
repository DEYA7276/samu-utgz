"""Persistencia con campos clínicos cifrados y sesiones en servidor."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, Integer, String, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, sessionmaker
from sqlalchemy.types import TypeDecorator

ROOT = Path(__file__).resolve().parent.parent
default_private = '/tmp/private' if os.getenv('VERCEL') else str(ROOT / 'private')
PRIVATE = Path(os.getenv('SAMU_PRIVATE_DIR', default_private))
try:
    PRIVATE.mkdir(parents=True, exist_ok=True)
except Exception:
    pass
DB_URL = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL') or os.getenv('STORAGE_URL') or os.getenv('POSTGRES_URL_NON_POOLING') or os.getenv('POSTGRES_PRISMA_URL') or f'sqlite:///{PRIVATE / "samu.sqlite3"}'
if DB_URL.startswith('postgres://'):
    DB_URL = DB_URL.replace('postgres://', 'postgresql+psycopg://', 1)
elif DB_URL.startswith('postgresql://'):
    DB_URL = DB_URL.replace('postgresql://', 'postgresql+psycopg://', 1)

if 'pgbouncer=true' in DB_URL:
    DB_URL = DB_URL.replace('&pgbouncer=true', '').replace('?pgbouncer=true&', '?').replace('?pgbouncer=true', '')
from cryptography.fernet import Fernet, MultiFernet
FERNET_KEY = os.getenv('DATA_ENCRYPTION_KEY', '')
ciphers = []
if FERNET_KEY:
    ciphers.append(Fernet(FERNET_KEY.encode('ascii')))
key_path = PRIVATE / 'development-fernet.key'
if key_path.exists():
    try:
        dev_k = key_path.read_text().strip()
        if dev_k and dev_k != FERNET_KEY:
            ciphers.append(Fernet(dev_k.encode('ascii')))
    except Exception:
        pass
if not ciphers:
    if os.getenv('APP_ENV') == 'production':
        raise RuntimeError('En producción debes definir DATA_ENCRYPTION_KEY y conservarla en lugar seguro.')
    if not key_path.exists():
        key_path.write_bytes(Fernet.generate_key())
        os.chmod(key_path, 0o600)
    ciphers.append(Fernet(key_path.read_text().strip().encode('ascii')))

CIPHER = MultiFernet(ciphers) if len(ciphers) > 1 else ciphers[0]

class EncryptedJSON(TypeDecorator):
    impl = Text
    cache_ok = True
    def process_bind_param(self, value, dialect):
        if value is None: return None
        return CIPHER.encrypt(json.dumps(value, ensure_ascii=False).encode('utf-8')).decode('ascii')
    def process_result_value(self, value, dialect):
        if value is None: return None
        return json.loads(CIPHER.decrypt(value.encode('ascii')).decode('utf-8'))

class Base(DeclarativeBase):
    pass

class Nurse(Base):
    __tablename__ = 'personal'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(180))
    email: Mapped[str] = mapped_column(String(250), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default='enfermeria')
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    google_sub: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)

class LoginSession(Base):
    __tablename__ = 'sesiones'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    csrf: Mapped[str] = mapped_column(String(90))
    user_id: Mapped[int] = mapped_column(ForeignKey('personal.id'))
    expires: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class Student(Base):
    __tablename__ = 'fichas_medicas'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    folio: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    nombre_aspirante: Mapped[str] = mapped_column(String(200), index=True)
    email_verificacion: Mapped[str] = mapped_column(String(250), index=True)
    datos: Mapped[dict] = mapped_column(EncryptedJSON)
    estado: Mapped[str] = mapped_column(String(30), default='pendiente_revision', index=True)
    observaciones_correccion: Mapped[str] = mapped_column(String(500), default='')
    qr_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    matricula: Mapped[str | None] = mapped_column(String(40), unique=True, nullable=True)
    foto: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validated_by: Mapped[int | None] = mapped_column(ForeignKey('personal.id'), nullable=True)

class EmailOTP(Base):
    __tablename__ = 'verificaciones_correo'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), index=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)

class Attention(Base):
    __tablename__ = 'bitacora_atencion'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int | None] = mapped_column(ForeignKey('fichas_medicas.id'), nullable=True)
    nombre: Mapped[str] = mapped_column(String(200), index=True)
    matricula: Mapped[str] = mapped_column(String(60), index=True)
    fecha: Mapped[str] = mapped_column(String(10), index=True)
    hora: Mapped[str] = mapped_column(String(5))
    datos: Mapped[dict] = mapped_column(EncryptedJSON)
    creator_id: Mapped[int] = mapped_column(ForeignKey('personal.id'))
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Referral(Base):
    __tablename__ = 'canalizaciones_externas'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int | None] = mapped_column(ForeignKey('fichas_medicas.id'), nullable=True)
    nombre: Mapped[str] = mapped_column(String(200), index=True)
    fecha: Mapped[str] = mapped_column(String(10), index=True)
    datos: Mapped[dict] = mapped_column(EncryptedJSON)
    creator_id: Mapped[int] = mapped_column(ForeignKey('personal.id'))
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Inventory(Base):
    __tablename__ = 'inventario_medicamentos_material'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    medicamento_material: Mapped[str] = mapped_column(String(240))
    descripcion: Mapped[str] = mapped_column(String(500), default='')
    fecha_caducidad: Mapped[str] = mapped_column(String(10), default='')
    cantidad_inicio: Mapped[int] = mapped_column(Integer, default=0)
    cantidad_fin: Mapped[int] = mapped_column(Integer, default=0)
    stock_minimo: Mapped[int] = mapped_column(Integer, default=3)
    cuatrimestre: Mapped[str] = mapped_column(String(120), index=True)
    updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Contact(Base):
    __tablename__ = 'destinatarios_correo'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    correo: Mapped[str] = mapped_column(String(250), unique=True)
    area: Mapped[str] = mapped_column(String(200), default='')
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

class MailLog(Base):
    __tablename__ = 'envios_canalizaciones'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    referral_id: Mapped[int] = mapped_column(ForeignKey('canalizaciones_externas.id'))
    contact_id: Mapped[int] = mapped_column(ForeignKey('destinatarios_correo.id'))
    sent_by: Mapped[int] = mapped_column(ForeignKey('personal.id'))
    estado: Mapped[str] = mapped_column(String(25))
    error: Mapped[str] = mapped_column(String(250), default='')
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Audit(Base):
    __tablename__ = 'auditoria'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accion: Mapped[str] = mapped_column(String(70))
    entidad: Mapped[str] = mapped_column(String(70))
    entidad_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class DownloadToken(Base):
    __tablename__ = 'enlaces_descarga'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('personal.id'))
    tipo: Mapped[str] = mapped_column(String(30))
    entidad_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    filtro: Mapped[str] = mapped_column(String(120), default='')
    expires: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(Boolean, default=False)

engine = create_engine(DB_URL, connect_args={'check_same_thread':False} if DB_URL.startswith('sqlite') else {}, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def init_db():
    Base.metadata.create_all(engine)
    from sqlalchemy import text
    if DB_URL.startswith('sqlite'):
        with engine.begin() as conn:
            conn.execute(text('PRAGMA journal_mode=WAL'))
            cols = [r[1] for r in conn.execute(text('PRAGMA table_info(inventario_medicamentos_material)')).fetchall()]
            if 'stock_minimo' not in cols:
                conn.execute(text('ALTER TABLE inventario_medicamentos_material ADD COLUMN stock_minimo INTEGER DEFAULT 3'))
            nurse_cols = [r[1] for r in conn.execute(text('PRAGMA table_info(personal)')).fetchall()]
            if 'google_sub' not in nurse_cols:
                conn.execute(text('ALTER TABLE personal ADD COLUMN google_sub VARCHAR(100)'))
    else:
        with engine.begin() as conn:
            try:
                conn.execute(text('ALTER TABLE inventario_medicamentos_material ADD COLUMN IF NOT EXISTS stock_minimo INTEGER DEFAULT 3'))
            except Exception:
                pass
            try:
                conn.execute(text('ALTER TABLE personal ADD COLUMN IF NOT EXISTS google_sub VARCHAR(100)'))
            except Exception:
                pass

    with SessionLocal() as s_db:
        from sqlalchemy import select, func
        nurse_count = s_db.scalar(select(func.count(Nurse.id)))
        if nurse_count == 0:
            from .auth import hash_password
            s_db.add(Nurse(
                name='Enfermería UTGZ',
                email='enfermeriautgz@gmail.com',
                password_hash=hash_password.hash(os.getenv('DEFAULT_ADMIN_PASSWORD', 'Enfermeria2026!')),
                role='admin',
                active=True
            ))
            s_db.commit()

def audit(db, user_id, action, entity, entity_id=None):
    db.add(Audit(user_id=user_id, accion=action, entidad=entity, entidad_id=entity_id))
