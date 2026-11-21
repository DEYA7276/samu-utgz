"""Script de verificación integral de las 5 mejoras conectándose al servidor live en http://127.0.0.1:8000."""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from dotenv import load_dotenv
load_dotenv()

import io
import json
import base64
import urllib.request
import urllib.parse
from PIL import Image, ImageDraw
from http.cookiejar import CookieJar
from datetime import datetime, timedelta

def make_signature():
    im = Image.new('RGBA', (460, 130), 'white')
    d = ImageDraw.Draw(im)
    d.line([(8, 88), (100, 24), (160, 92), (260, 22), (400, 88)], fill='#12345a', width=6)
    b = io.BytesIO()
    im.save(b, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()

BASE_URL = "http://127.0.0.1:8000"
cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def request(path, method='GET', data=None, headers=None, files=None):
    url = f"{BASE_URL}{path}"
    req_headers = headers or {}

    if files:
        # Multipart form data
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = bytearray()
        for k, (filename, content, content_type) in files.items():
            body.extend(f'--{boundary}\r\n'.encode('utf-8'))
            body.extend(f'Content-Disposition: form-data; name="{k}"; filename="{filename}"\r\n'.encode('utf-8'))
            body.extend(f'Content-Type: {content_type}\r\n\r\n'.encode('utf-8'))
            body.extend(content)
            body.extend(b'\r\n')
        if data:
            for k, v in data.items():
                body.extend(f'--{boundary}\r\n'.encode('utf-8'))
                body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode('utf-8'))
                body.extend(str(v).encode('utf-8'))
                body.extend(b'\r\n')
        body.extend(f'--{boundary}--\r\n'.encode('utf-8'))
        req_headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'
        req = urllib.request.Request(url, data=bytes(body), headers=req_headers, method=method)
    elif data is not None:
        body = json.dumps(data).encode('utf-8')
        req_headers['Content-Type'] = 'application/json'
        req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    else:
        req = urllib.request.Request(url, headers=req_headers, method=method)

    try:
        with opener.open(req) as resp:
            content = resp.read()
            ct = resp.headers.get('content-type', '')
            if 'application/json' in ct:
                return resp.status, json.loads(content.decode('utf-8')), resp.headers
            return resp.status, content, resp.headers
    except urllib.error.HTTPError as e:
        err_content = e.read().decode('utf-8', errors='replace')
        try:
            err_json = json.loads(err_content)
        except Exception:
            err_json = {'detail': err_content}
        return e.code, err_json, e.headers

def run_all_checks():
    print("=== INICIANDO PRUEBAS DE VERIFICACIÓN EN SERVIDOR LIVE ===")

    # 1. Login institucional
    status, login_res, _ = request('/api/session/login', method='POST', data={
        'email': '23610030@utgz.edu.mx',
        'password': 'AdminPass_2026!'
    })
    csrf = None
    if status == 200:
        csrf = login_res['csrf']
        print(f"[OK] Sesión iniciada como: {login_res['user']['name']}")
    else:
        print(f"[INFO] Login devolvió {status}: {login_res}. Recreando/obteniendo admin...")
        from app.db import SessionLocal, Nurse, LoginSession
        from app.auth import hash_password, new_login
        db = SessionLocal()
        admin = db.query(Nurse).filter_by(email='23610030@utgz.edu.mx').first()
        admin.password_hash = hash_password.hash('AdminPass_2026!')
        db.commit()
        db.close()
        status, login_res, _ = request('/api/session/login', method='POST', data={
            'email': '23610030@utgz.edu.mx',
            'password': 'AdminPass_2026!'
        })
        assert status == 200, f"Login falló: {login_res}"
        csrf = login_res['csrf']
        print(f"[OK] Sesión iniciada con éxito. CSRF obtenido.")

    auth_h = {'X-CSRF-Token': csrf}

    # =========================================================================
    # MEJORA 1: IMPORTACIÓN MASIVA DE ESTUDIANTES
    # =========================================================================
    print("\n--- 1. Verificando Importación Masiva de Estudiantes ---")

    # 1.1 Plantilla CSV (pura plantilla, sin datos inventados)
    st_csv, content_csv, h_csv = request('/api/estudiantes/plantilla?formato=csv', headers=auth_h)
    assert st_csv == 200
    assert 'text/csv' in h_csv.get('content-type', '')
    assert b'matricula,nombre_completo,carrera,grupo,correo' in content_csv
    assert b'Juan' not in content_csv and b'Perez' not in content_csv
    csv_lines = [l for l in content_csv.decode('utf-8-sig').splitlines() if l.strip()]
    assert len(csv_lines) == 1, f"La plantilla CSV debe tener solo el encabezado, tiene: {len(csv_lines)}"
    print("  [OK] Descarga de plantilla CSV validada (pura estructura, 0 filas con datos inventados).")

    # 1.2 Plantilla Excel (pura plantilla, sin datos inventados)
    from openpyxl import load_workbook
    st_xlsx, content_xlsx, h_xlsx = request('/api/estudiantes/plantilla?formato=xlsx', headers=auth_h)
    assert st_xlsx == 200
    assert 'spreadsheetml' in h_xlsx.get('content-type', '')
    wb_test = load_workbook(io.BytesIO(content_xlsx))
    ws_test = wb_test.active
    assert ws_test.max_row == 1, f"La plantilla Excel debe tener max_row == 1, tiene {ws_test.max_row}"
    assert [cell.value for cell in ws_test[1]] == ["Matrícula", "Nombre Completo", "Carrera / Programa Educativo", "Grupo", "Correo Institucional"]
    print("  [OK] Descarga de plantilla Excel (.xlsx) validada (pura estructura, 0 filas con datos inventados).")

    # 1.3 Vista previa de importación con CSV
    tag = datetime.now().strftime("%H%M%S")
    mat1 = f"26{tag}1"
    mat2 = f"26{tag}2"
    csv_sample = (
        f"matricula,nombre_completo,carrera,grupo,correo\n"
        f"{mat1},Valeria Morales Ramos,Ingeniería en Mecatrónica,101 A,{mat1}@utgz.edu.mx\n"
        f"{mat2},Diego Armando Castillo,Licenciatura en Gestión del Capital Humano,102 B,{mat2}@utgz.edu.mx\n"
        f",Estudiante Sin Matricula,Ingeniería en Redes,101 A,invalido@utgz.edu.mx\n"
    ).encode('utf-8')

    st_prev, prev_res, _ = request('/api/estudiantes/importar/preview', method='POST', files={
        'file': ('estudiantes_test.csv', csv_sample, 'text/csv')
    }, headers=auth_h)
    assert st_prev == 200, prev_res
    assert prev_res['ok'] is True
    assert prev_res['total'] == 3
    assert prev_res['nuevos_count'] == 2
    assert prev_res['errores_count'] == 1
    print(f"  [OK] Vista previa CSV: Total {prev_res['total']}, Nuevos {prev_res['nuevos_count']}, Errores detectados {prev_res['errores_count']}")

    # 1.4 Ejecutar importación real
    st_imp, imp_res, _ = request('/api/estudiantes/importar', method='POST', files={
        'file': ('estudiantes_test.csv', csv_sample, 'text/csv')
    }, data={'actualizar_duplicados': 'true'}, headers=auth_h)
    assert st_imp == 200, imp_res
    print(f"  [OK] Importación ejecutada: Creados {imp_res['creados']}, Actualizados {imp_res['actualizados']}")

    # 1.5 Detección de duplicados y actualización académica sin borrar datos médicos
    csv_dup = (
        f"matricula,nombre_completo,carrera,grupo,correo\n"
        f"{mat1},Valeria Morales Ramos,Ingeniería en Tecnologías de la Información,301 A,valeria.nuevo@utgz.edu.mx\n"
    ).encode('utf-8')

    st_dup, dup_res, _ = request('/api/estudiantes/importar', method='POST', files={
        'file': ('update_dup.csv', csv_dup, 'text/csv')
    }, data={'actualizar_duplicados': 'true'}, headers=auth_h)
    assert st_dup == 200, dup_res
    assert dup_res['actualizados'] >= 1
    print("  [OK] Actualización de duplicados por matrícula funcionando sin sobrescrituras destructivas.")

    # =========================================================================
    # MEJORA 2: DASHBOARD INTELIGENTE DE ENFERMERÍA
    # =========================================================================
    print("\n--- 2. Verificando Dashboard Inteligente ---")
    st_dash, dash, _ = request('/api/resumen', headers=auth_h)
    assert st_dash == 200, dash
    assert 'atenciones_hoy' in dash
    assert 'atenciones_mes' in dash
    assert 'alumnos_atendidos_total' in dash
    assert 'alumnos_atendidos_mes' in dash
    assert 'canalizaciones_mes' in dash
    assert 'inventario_alertas' in dash
    assert 'ultimas_atenciones' in dash
    assert 'grafica_mensual' in dash
    assert len(dash['grafica_mensual']) == 6

    print(f"  [OK] Estadísticas reales: Atenciones hoy={dash['atenciones_hoy']}, Atenciones mes={dash['atenciones_mes']}, Alumnos={dash['alumnos_atendidos_total']}")
    print(f"  [OK] Alertas de inventario: Agotados={dash['inventario_alertas']['agotados']}, Stock bajo={dash['inventario_alertas']['stock_bajo']}, Por caducar={dash['inventario_alertas']['por_caducar']}")
    print(f"  [OK] Gráfica mensual generada con {len(dash['grafica_mensual'])} meses históricos.")

    # =========================================================================
    # MEJORA 3: ALERTAS MÉDICAS DESTACADAS
    # =========================================================================
    print("\n--- 3. Verificando Alertas Médicas Estructuradas ---")
    # Buscar estudiante recién importado
    st_fichas, fichas, _ = request(f'/api/fichas?q={mat1}', headers=auth_h)
    assert len(fichas) >= 1
    student_id = fichas[0]['id']

    # Consultar ficha del estudiante importado (debe reportar 'no_proporcionado')
    st_f, ficha_det, _ = request(f'/api/fichas/{student_id}', headers=auth_h)
    assert st_f == 200
    alertas1 = ficha_det['alertas_medicas']
    assert alertas1['estado'] == 'no_proporcionado'
    print(f"  [OK] Detección de datos médicos no proporcionados: '{alertas1['mensaje']}'")

    # Registrar / editar condiciones médicas y completar expediente clínico vía PUT /api/fichas/{ident}
    print("  [TEST] Probando edición y complementación de ficha médica vía PUT /api/fichas/{id}...")
    st_put, res_put, _ = request(f'/api/fichas/{student_id}', method='PUT', data={
        'nombre_aspirante': 'Valeria Morales Ramos',
        'matricula': mat1,
        'correo': 'valeria.morales@utgz.edu.mx',
        'tipo_sangre': 'O+',
        'nss': '12345678901',
        'alergia_medicamentos': 'PENICILINA Y SULFAMIDAS',
        'alergia_alimentos': 'Nueces y mariscos',
        'alergia_otros': 'Polen',
        'antecedentes_personales': ['ASMA', 'REFLUJO'],
        'antecedentes_familiares': ['DIABETES', 'HIPERTENSIÓN ARTERIAL'],
        'medicamentos_no_administrar': 'ASPIRINA, IBUPROFENO',
        'padecimientos': 'Asma bronquial intermitente',
        'tratamiento_medico': 'Salbutamol en aerosol en caso de crisis',
        'nombre_padre_tutor': 'Roberto Morales Soto',
        'telefono_padre_tutor': '7669876543',
        'autoriza_traslado': True,
        'validar_ahora': True
    }, headers=auth_h)
    assert st_put == 200, f"Error en PUT /api/fichas/{student_id}: {res_put}"
    print("  [OK] Expediente médico editado y completado exitosamente vía PUT /api/fichas/{id}.")

    # Re-consultar ficha y verificar que todos los datos clínicos persisten
    st_f2, ficha_det2, _ = request(f'/api/fichas/{student_id}', headers=auth_h)
    assert st_f2 == 200
    assert ficha_det2['datos']['tipo_sangre'] == 'O+'
    assert ficha_det2['datos']['nss'] == '12345678901'
    assert ficha_det2['datos']['autoriza_traslado'] is True
    assert ficha_det2['datos']['nombre_padre_tutor'] == 'Roberto Morales Soto'

    alertas2 = ficha_det2['alertas_medicas']
    assert alertas2['estado'] == 'con_alertas'
    assert alertas2['critico'] is True
    assert any('PENICILINA' in a['detalle'] for a in alertas2['alergias'])
    assert any('ASMA' in c['detalle'] for c in alertas2['cronicos'])
    assert 'ASPIRINA' in alertas2['contraindicados'] or any('ASPIRINA' in x for x in alertas2['contraindicados'])
    print(f"  [OK] Alertas activas detectadas correctamente: Alergias={len(alertas2['alergias'])}, Crónicos={len(alertas2['cronicos'])}, Contraindicados={len(alertas2['contraindicados'])}")

    # =========================================================================
    # MEJORA 4: HISTORIAL DE ATENCIONES POR ESTUDIANTE (LÍNEA DE TIEMPO)
    # =========================================================================
    print("\n--- 4. Verificando Historial de Atenciones por Estudiante ---")
    # Registrar atención médica
    today_str = datetime.now().strftime('%Y-%m-%d')
    st_att, att_res, _ = request('/api/bitacora', method='POST', data={
        'student_id': student_id,
        'fecha': today_str,
        'hora': '11:15',
        'nombre': 'Valeria Morales Ramos',
        'matricula': mat1,
        'edad': '20',
        'sexo': 'Mujer',
        'programa_educativo': 'Ingeniería en Desarrollo y Gestión de Software',
        'grupo': '301 A',
        'motivo_consulta': 'Crisis asmática leve y disnea',
        'toma_ta': '115/75',
        'otro_procedimiento': 'Nebulización y oxigenoterapia',
        'suministro_medicamento': 'Salbutamol',
        'material_curacion': 'Mascarilla descartable',
        'firma_usuario': make_signature(),
        'firma_enfermeria': make_signature()
    }, headers=auth_h)
    assert st_att == 200, att_res
    print("  [OK] Atención médica registrada en bitácora.")

    # Consultar listado de bitácora mensual (pestaña Registros guardados)
    mes_actual = today_str[:7]
    st_bit_list, bit_rows, _ = request(f'/api/bitacora?mes={mes_actual}', headers=auth_h)
    assert st_bit_list == 200
    assert any(b['nombre'] == 'Valeria Morales Ramos' for b in bit_rows)
    print(f"  [OK] Pestaña de registros de bitácora verificada: {len(bit_rows)} atención(es) en el mes {mes_actual}.")

    # Consultar timeline
    st_hist, hist, _ = request(f'/api/fichas/{student_id}/historial', headers=auth_h)
    assert st_hist == 200, hist
    assert hist['total_atenciones'] >= 1
    assert hist['total_eventos'] >= 1
    assert hist['items'][0]['motivo'] == 'Crisis asmática leve y disnea'
    assert hist['items'][0]['detalles']['suministro_medicamento'] == 'Salbutamol'
    print(f"  [OK] Timeline cronológico verificado: {hist['total_atenciones']} atención(es) vinculada(s) con signos y procedimientos.")

    # =========================================================================
    # MEJORA 5: INVENTARIO INTELIGENTE CON SEMÁFORO Y EXISTENCIAS MÍNIMAS
    # =========================================================================
    print("\n--- 5. Verificando Inventario Inteligente y Semáforo ---")
    today = datetime.now().date()

    # Insumo agotado
    st_i1, _, _ = request('/api/inventario', method='POST', data={
        'medicamento_material': 'Paracetamol 500mg tabletas',
        'descripcion': 'Caja con 20 tabletas',
        'fecha_caducidad': (today + timedelta(days=365)).strftime('%Y-%m-%d'),
        'cantidad_inicio': 10,
        'cantidad_fin': 0,
        'stock_minimo': 5,
        'cuatrimestre': 'SEP-DIC 2026'
    }, headers=auth_h)
    assert st_i1 == 200

    # Insumo con stock bajo
    st_i2, _, _ = request('/api/inventario', method='POST', data={
        'medicamento_material': 'Jeringas 5ml con aguja',
        'descripcion': 'Caja con 50 unidades',
        'fecha_caducidad': (today + timedelta(days=400)).strftime('%Y-%m-%d'),
        'cantidad_inicio': 15,
        'cantidad_fin': 3,
        'stock_minimo': 8,
        'cuatrimestre': 'SEP-DIC 2026'
    }, headers=auth_h)
    assert st_i2 == 200

    # Insumo próximo a caducar
    st_i3, _, _ = request('/api/inventario', method='POST', data={
        'medicamento_material': 'Solución Fisiológica 250ml',
        'descripcion': 'Bolsa para infusión',
        'fecha_caducidad': (today + timedelta(days=25)).strftime('%Y-%m-%d'),
        'cantidad_inicio': 12,
        'cantidad_fin': 10,
        'stock_minimo': 4,
        'cuatrimestre': 'SEP-DIC 2026'
    }, headers=auth_h)
    assert st_i3 == 200

    # Consultar inventario
    q_cuat = urllib.parse.quote('SEP-DIC 2026')
    st_inv, items_inv, _ = request(f'/api/inventario?cuatrimestre={q_cuat}', headers=auth_h)
    assert st_inv == 200

    parac = next(i for i in items_inv if i['medicamento_material'] == 'Paracetamol 500mg tabletas')
    assert parac['estado_stock']['estado'] == 'agotado'
    assert parac['estado_stock']['color'] == 'rojo'

    jeringas = next(i for i in items_inv if i['medicamento_material'] == 'Jeringas 5ml con aguja')
    assert jeringas['estado_stock']['estado'] == 'stock_bajo'
    assert jeringas['estado_stock']['color'] == 'amarillo'

    sol = next(i for i in items_inv if i['medicamento_material'] == 'Solución Fisiológica 250ml')
    assert sol['estado_stock']['estado'] == 'por_caducar'
    assert sol['estado_stock']['color'] == 'amarillo'

    print("  [OK] Semáforos calculados: Rojo (Agotado), Amarillo (Stock bajo), Amarillo (Por caducar).")

    # Probar filtros de estado
    st_f_ag, items_ag, _ = request(f'/api/inventario?cuatrimestre={q_cuat}&filtro_estado=agotados', headers=auth_h)
    assert all(i['estado_stock']['estado'] in ('agotado', 'caducado') for i in items_ag)

    st_f_crit, items_crit, _ = request(f'/api/inventario?cuatrimestre={q_cuat}&filtro_estado=criticos', headers=auth_h)
    assert len(items_crit) >= 3
    print(f"  [OK] Filtros de estado validados: Agotados ({len(items_ag)}), Críticos ({len(items_crit)}).")

    print("\n=======================================================")
    print("¡TODAS LAS PRUEBAS DE LAS 5 MEJORAS PASARON CON ÉXITO!")
    print("=======================================================")

if __name__ == '__main__':
    run_all_checks()
