import httpx
import sqlite3
import hashlib
import io
import base64
import time
import os
import sys

# Asegurar raíz en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from PIL import Image
from starlette.testclient import TestClient
from app.main import app, OAUTH_STATES
import secrets

BASE_URL = "http://127.0.0.1:8000"
DB_PATH = "private/samu.sqlite3"

def make_test_signature():
    im = Image.new("RGBA", (120, 60), (255, 255, 255, 0))
    for x in range(20, 100):
        im.putpixel((x, 30), (40, 104, 79, 255))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"

def run_tests():
    print("=== INICIO DE PRUEBAS DE SEGURIDAD Y AUTENTICACIÓN SAMU ===")
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    email_test = "aspirante_prueba_2026@utgz.edu.mx"
    # Limpieza inicial por si quedó algún registro previo
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM fichas_medicas WHERE email_verificacion = ?", (email_test,))
    cur.execute("DELETE FROM verificaciones_correo WHERE email = ?", (email_test,))
    conn.commit()

    # 1. Verificar obtención de CSRF público
    print("\n--- 1. Token CSRF Público ---")
    r = client.get("/api/csrf-public")
    assert r.status_code == 200, f"Error obteniendo CSRF público: {r.status_code}"
    csrf_token = r.json().get("csrf")
    assert csrf_token and len(csrf_token) > 20, "Token CSRF inválido"
    print(f"✓ Token CSRF público obtenido: {csrf_token[:10]}...")

    # 2. Solicitar OTP de verificación para estudiante de nuevo ingreso (sin matrícula)
    print("\n--- 2. Solicitud de Código OTP por Correo ---")
    req_body = {
        "correo": email_test,
        "nombre": "Aspirante de Prueba Sin Matrícula",
        "matricula": None,
        "sitio_web": "" # Honeypot limpio
    }
    r = client.post(
        "/api/alumnos/verificar-correo/solicitar",
        json=req_body,
        headers={"X-CSRF-Token": csrf_token}
    )
    assert r.status_code == 200, f"Error solicitando OTP: {r.text}"
    resp_otp = r.json()
    print(f"✓ Solicitud aceptada: {resp_otp}")

    otp_code = resp_otp.get("test_code")
    assert otp_code and len(otp_code) == 6, f"Código devuelto inválido: {otp_code}"

    # Consultar el OTP generado en la base de datos local
    cur.execute(
        "SELECT code_hash, expires, consumed FROM verificaciones_correo WHERE email = ? ORDER BY id DESC LIMIT 1",
        (email_test,)
    )
    row = cur.fetchone()
    assert row is not None, "No se encontró registro de OTP en la base de datos"
    code_hash, expires_at, consumed = row
    expected_hash = hashlib.sha256(otp_code.encode()).hexdigest()
    assert code_hash == expected_hash, "El hash del código no coincide con la BD"
    assert consumed == 0, "El código no debería estar consumido aún"
    print(f"✓ Registro verificado en BD: hash={code_hash[:12]}... (Expira: {expires_at}, Consumido: {consumed})")

    # 3. Probar envío de ficha con código INCORRECTO
    print("\n--- 3. Intento con Código OTP Incorrecto ---")
    firma_ejemplo = make_test_signature()
    ficha_payload = {
        "nombre_aspirante": "Aspirante de Prueba Sin Matrícula",
        "correo": email_test,
        "matricula": None, # Matrícula opcional para nuevo ingreso
        "programa_educativo": "TSU en Tecnologías de la Información, área Desarrollo de Software Multiplataforma",
        "tipo_sangre": "O+",
        "fecha_nacimiento": "2005-04-12",
        "sexo": "Mujer",
        "nombre_padre_tutor": "Tutor de Prueba Responsable",
        "telefono_padre_tutor": "7661234567",
        "codigo_verificacion": "999999", # Código deliberadamente erróneo
        "acepto_aviso": True,
        "antecedentes_familiares": ["DIABETES"],
        "antecedentes_personales": [],
        "autoriza_traslado": True,
        "firma_aspirante": firma_ejemplo,
        "firma_padre_tutor": firma_ejemplo
    }
    r = client.post(
        "/api/alumnos/ficha",
        json=ficha_payload,
        headers={"X-CSRF-Token": csrf_token}
    )
    assert r.status_code == 400, f"Se esperaba 400 con código erróneo, se obtuvo: {r.status_code}"
    print(f"✓ Rechazo seguro con código incorrecto: {r.json().get('detail')}")

    # 4. Envío exitoso con código OTP CORRECTO, Matrícula Opcional (None) y SIN firma del padre
    print("\n--- 4. Envío Exitoso de Ficha (Matrícula Opcional + OTP Válido + Sin Firma del Padre) ---")
    ficha_payload["codigo_verificacion"] = otp_code
    ficha_payload["firma_padre_tutor"] = "" # Confirmar que no se exige firma del padre
    r = client.post(
        "/api/alumnos/ficha",
        json=ficha_payload,
        headers={"X-CSRF-Token": csrf_token}
    )
    assert r.status_code == 200, f"Error enviando ficha válida: {r.text}"
    resp_data = r.json()
    assert resp_data.get("ok") is True, "Respuesta no indica ok: True"
    folio = resp_data.get("folio")
    assert folio and folio.startswith("FIC-"), f"Folio inválido: {folio}"
    # Verificar que NO se expone ningún dato médico ni personal en la respuesta pública
    assert "antecedentes" not in resp_data, "Fuga de datos médicos en la respuesta"
    assert "datos" not in resp_data, "Fuga de datos en la respuesta"
    print(f"✓ Ficha registrada exitosamente con folio: {folio}")
    print(f"✓ Respuesta limpia y sanitizada (sin datos clínicos): {resp_data}")

    # Verificar que el OTP quedó marcado como consumido
    cur.execute(
        "SELECT consumed FROM verificaciones_correo WHERE email = ? AND code_hash = ?",
        (email_test, expected_hash)
    )
    consumed_status = cur.fetchone()[0]
    assert consumed_status == 1, "El código OTP no fue marcado como consumido"
    print("✓ El código OTP quedó consumido y no puede ser reutilizado.")

    # 5. Detección de duplicados sin revelar datos médicos
    print("\n--- 5. Prevención de Duplicados ---")
    r_dup = client.post(
        "/api/alumnos/verificar-correo/solicitar",
        json=req_body,
        headers={"X-CSRF-Token": csrf_token}
    )
    assert r_dup.status_code == 409, f"Se esperaba 409 Duplicado, obtenido: {r_dup.status_code}"
    print(f"✓ Detección de duplicado por correo (409): {r_dup.json().get('detail')}")

    # 6. Protección de endpoints privados contra accesos sin autenticación
    print("\n--- 6. Protección de Endpoints Privados (Fichas Médicas) ---")
    anon_client = httpx.Client(base_url=BASE_URL, timeout=10.0)
    r_fichas = anon_client.get("/api/fichas")
    assert r_fichas.status_code == 401, f"Se esperaba 401 Unauthorized, obtenido: {r_fichas.status_code}"
    r_bitacora = anon_client.get("/api/bitacora")
    assert r_bitacora.status_code == 401, f"Se esperaba 401 Unauthorized, obtenido: {r_bitacora.status_code}"
    print("✓ Endpoints clínicos (/api/fichas, /api/bitacora) bloqueados a usuarios anónimos (401).")

    # 7. Inicio de sesión con contraseña de respaldo para enfermería
    print("\n--- 7. Inicio de Sesión de Respaldo (Enfermería) ---")
    r_login = client.post(
        "/api/session/login",
        json={"email": "enfermeriautgz@gmail.com", "password": "Enfermeria2026!"}
    )
    assert r_login.status_code == 200, f"Error en login tradicional: {r_login.text}"
    nurse_user = r_login.json().get("user")
    nurse_csrf = r_login.json().get("csrf")
    print(f"✓ Login de enfermería exitoso: {nurse_user.get('name')} ({nurse_user.get('email')})")

    # Consultar fichas como enfermera autorizada
    r_auth_fichas = client.get("/api/fichas")
    assert r_auth_fichas.status_code == 200, f"Error consultando fichas autenticado: {r_auth_fichas.status_code}"
    fichas_list = r_auth_fichas.json()
    print(f"✓ Fichas consultadas con éxito por enfermería (Total: {len(fichas_list)})")
    # Verificar que la ficha recién creada sin matrícula existe en estado pendiente para enfermería
    creada = [f for f in fichas_list if f.get("folio") == folio]
    assert len(creada) == 1, "La ficha creada no aparece en la vista de enfermería"
    assert creada[0].get("matricula") is None, "La matrícula debería ser None"
    assert creada[0].get("estado") == "pendiente", "El estado debería ser pendiente"
    print(f"✓ Expediente verificado en panel de enfermería: estado='{creada[0].get('estado')}', matricula={creada[0].get('matricula')}")

    # 8. Cierre de sesión seguro
    print("\n--- 8. Cierre de Sesión Seguro ---")
    r_logout = client.post("/api/session/logout", headers={"X-CSRF-Token": nurse_csrf})
    assert r_logout.status_code == 200, "Error cerrando sesión"
    r_check = client.get("/api/session")
    assert r_check.status_code == 401, "La sesión sigue activa después del logout"
    print("✓ Sesión cerrada y token destruido correctamente.")

    # 9. Configuración y endpoints de Google OAuth 2.0
    print("\n--- 9. Verificación de Endpoints Google OAuth 2.0 ---")
    r_google_cfg = client.get("/api/auth/google/config")
    assert r_google_cfg.status_code == 200, "Error consultando config OAuth"
    print(f"✓ Estado actual Google OAuth en servidor: {r_google_cfg.json()}")

    # Probar endpoint de polling con estado inexistente
    r_poll = client.get("/api/auth/google/poll-session?state=inexistente")
    assert r_poll.status_code == 200 and r_poll.json().get("status") == "not_found", "Polling inesperado"
    print("✓ Polling de OAuth responde correctamente 'not_found' ante estado desconocido.")

    # Simulación de sesión OAuth autorizada vs no autorizada usando TestClient
    tc = TestClient(app)
    sim_state = secrets.token_urlsafe(32)
    sim_exchange = secrets.token_urlsafe(36)
    
    # 9a. Probar intento de finalización con cuenta NO autorizada
    OAUTH_STATES[sim_state] = {
        'status': 'unauthorized',
        'error_msg': 'La cuenta intruso@gmail.com no está autorizada en SAMU.',
        'created': datetime.now(timezone.utc),
        'expires': datetime.now(timezone.utc) + timedelta(minutes=5)
    }
    r_poll_unauth = tc.get(f"/api/auth/google/poll-session?state={sim_state}")
    assert r_poll_unauth.json().get("status") == "unauthorized", "Fallo al reportar estado no autorizado"
    print("✓ Polling reporta correctamente estado 'unauthorized' para cuentas no autorizadas.")

    # 9b. Probar intento de finalización con cuenta AUTORIZADA
    OAUTH_STATES[sim_state] = {
        'status': 'authenticated',
        'exchange_token': sim_exchange,
        'user_id': 1, # Enfermera con ID 1 (enfermeriautgz@gmail.com)
        'created': datetime.now(timezone.utc),
        'expires': datetime.now(timezone.utc) + timedelta(minutes=5)
    }
    r_poll_auth = tc.get(f"/api/auth/google/poll-session?state={sim_state}")
    assert r_poll_auth.json().get("status") == "authenticated", "Fallo al reportar estado autenticado"
    assert r_poll_auth.json().get("exchange_token") == sim_exchange, "Fallo en token de intercambio"
    print("✓ Polling reporta 'authenticated' con exchange_token válido.")

    # 9c. Finalizar sesión OAuth e intercambiar por cookie oficial de sesión
    r_finalize = tc.post(
        "/api/auth/google/finalize-session",
        json={"state": sim_state, "exchange_token": sim_exchange}
    )
    assert r_finalize.status_code == 200, f"Error finalizando sesión OAuth: {r_finalize.text}"
    fin_data = r_finalize.json()
    assert fin_data.get("user", {}).get("email") == "enfermeriautgz@gmail.com"
    assert fin_data.get("csrf") is not None
    print(f"✓ Sesión finalizada con éxito vía Google OAuth para: {fin_data['user']['name']}")

    # Verificar que el cliente ahora tiene acceso completo al panel de enfermería
    r_verify_session = tc.get("/api/session")
    assert r_verify_session.status_code == 200, "La sesión OAuth no autenticó el cliente"
    print("✓ Acceso verificado a /api/session mediante cookie emitida por OAuth.")

    # 10. Limpieza de datos de prueba
    cur.execute("DELETE FROM fichas_medicas WHERE email_verificacion = ?", (email_test,))
    cur.execute("DELETE FROM verificaciones_correo WHERE email = ?", (email_test,))
    conn.commit()
    conn.close()
    print("\n✓ Limpieza de datos de prueba ejecutada.")

    print("\n=======================================================")
    print("   TODAS LAS PRUEBAS DE SEGURIDAD PASARON CON ÉXITO   ")
    print("=======================================================")

if __name__ == "__main__":
    run_tests()
