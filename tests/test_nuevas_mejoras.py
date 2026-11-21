"""Pruebas exhaustivas de las 5 mejoras implementadas en SAMU UTGZ:
1. Importación masiva de estudiantes (Excel y CSV).
2. Dashboard inteligente de enfermería.
3. Alertas médicas destacadas (alergias, crónicos, sin sobrediagnóstico).
4. Historial cronológico de atenciones por estudiante.
5. Inventario inteligente con semáforo y existencias mínimas.
"""
import io
import os
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

os.environ['APP_ENV'] = 'development'
os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(tempfile.gettempdir()) / 'samu_test_mejoras.sqlite3')
os.environ['SAMU_PRIVATE_DIR'] = str(Path(tempfile.gettempdir()) / 'samu_test_mejoras_priv')

from fastapi.testclient import TestClient
from app.db import SessionLocal, init_db, Base, engine, Nurse, Student, Attention, Referral, Inventory
from app.auth import hash_password
from app.main import app
import app.importer as imp

client = TestClient(app)

def setup_module():
    Base.metadata.drop_all(engine)
    init_db()
    with SessionLocal.begin() as db:
        db.add(Nurse(
            name='Enfermera Jefa',
            email='enfermeria@test.utgz.edu.mx',
            password_hash=hash_password.hash('ContraseñaValida_123'),
            role='admin'
        ))

def get_auth_header():
    r = client.post('/api/session/login', json={
        'email': 'enfermeria@test.utgz.edu.mx',
        'password': 'ContraseñaValida_123'
    })
    assert r.status_code == 200, r.text
    return {'X-CSRF-Token': r.json()['csrf']}

def test_1_plantillas_e_importacion_masiva():
    h = get_auth_header()

    # 1.1 Descarga de plantillas
    r_csv = client.get('/api/estudiantes/plantilla?formato=csv', headers=h)
    assert r_csv.status_code == 200
    assert 'text/csv' in r_csv.headers['content-type']
    assert b'matricula,nombre_completo,carrera,grupo,correo' in r_csv.content

    r_xlsx = client.get('/api/estudiantes/plantilla?formato=xlsx', headers=h)
    assert r_xlsx.status_code == 200
    assert 'spreadsheetml' in r_xlsx.headers['content-type']

    # 1.2 Vista previa con archivo CSV
    csv_data = (
        "matricula,nombre_completo,carrera,grupo,correo\n"
        "24610010,Ana Martínez Morales,Ingeniería en Mecatrónica,101 A,24610010@utgz.edu.mx\n"
        "24610020,Luis Gómez Pérez,TSU en Gastronomía,202 B,24610020@utgz.edu.mx\n"
        ",Estudiante Sin Matricula,TSU en Turismo,101 C,error@utgz.edu.mx\n"
    ).encode('utf-8')

    files = {'file': ('alumnos_nuevos.csv', io.BytesIO(csv_data), 'text/csv')}
    r_prev = client.post('/api/estudiantes/importar/preview', files=files, headers=h)
    assert r_prev.status_code == 200, r_prev.text
    prev = r_prev.json()
    assert prev['ok'] is True
    assert prev['total'] == 3
    assert prev['nuevos_count'] == 2
    assert prev['errores_count'] == 1

    # 1.3 Ejecutar importación
    files = {'file': ('alumnos_nuevos.csv', io.BytesIO(csv_data), 'text/csv')}
    r_imp = client.post('/api/estudiantes/importar', files=files, data={'actualizar_duplicados': 'true'}, headers=h)
    assert r_imp.status_code == 200, r_imp.text
    res = r_imp.json()
    assert res['ok'] is True
    assert res['creados'] == 2
    assert res['actualizados'] == 0

    # 1.4 Probar duplicado y actualización académica sin borrar datos médicos
    with SessionLocal.begin() as db:
        st = db.scalar(Base.metadata.tables['fichas_medicas'].select().where(Base.metadata.tables['fichas_medicas'].c.matricula == '24610010'))
        assert st is not None
        # Simular que el estudiante tiene una alergia registrada
        student_obj = db.get(Student, st.id)
        d = dict(student_obj.datos)
        d['alergia_medicamentos'] = 'PENICILINA'
        student_obj.datos = d

    # Ahora importamos de nuevo con carrera actualizada para '24610010'
    csv_update = (
        "matricula,nombre_completo,carrera,grupo,correo\n"
        "24610010,Ana Martínez Morales,Ingeniería en Desarrollo y Gestión de Software,501 A,ana.nuevo@utgz.edu.mx\n"
    ).encode('utf-8')

    files = {'file': ('update.csv', io.BytesIO(csv_update), 'text/csv')}
    r_imp2 = client.post('/api/estudiantes/importar', files=files, data={'actualizar_duplicados': 'true'}, headers=h)
    assert r_imp2.status_code == 200
    res2 = r_imp2.json()
    assert res2['creados'] == 0
    assert res2['actualizados'] == 1

    # Verificar que los datos médicos se mantuvieron intactos
    with SessionLocal.begin() as db:
        student_check = db.scalar(Base.metadata.tables['fichas_medicas'].select().where(Base.metadata.tables['fichas_medicas'].c.matricula == '24610010'))
        student_obj = db.get(Student, student_check.id)
        assert student_obj.datos['alergia_medicamentos'] == 'PENICILINA' # Conservado
        assert student_obj.datos['programa_educativo'] == 'Ingeniería en Desarrollo y Gestión de Software' # Actualizado
        assert student_obj.datos['grupo'] == '501 A' # Actualizado

def test_2_dashboard_inteligente():
    h = get_auth_header()
    today_str = datetime.now().strftime('%Y-%m-%d')

    # Crear una atención hoy
    r_att = client.post('/api/bitacora', json={
        'fecha': today_str,
        'hora': '10:30',
        'nombre': 'Ana Martínez Morales',
        'matricula': '24610010',
        'edad': '20',
        'sexo': 'Mujer',
        'programa_educativo': 'Ingeniería en Desarrollo y Gestión de Software',
        'grupo': '501 A',
        'motivo_consulta': 'Cefalea intensa',
        'toma_ta': '120/80',
        'otro_procedimiento': 'Reposo en camilla',
        'suministro_medicamento': 'Paracetamol 500mg',
        'material_curacion': 'N/A',
        'firma_usuario': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
        'firma_enfermeria': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='
    }, headers=h)
    assert r_att.status_code == 200, r_att.text

    # Consultar dashboard
    r_dash = client.get('/api/resumen', headers=h)
    assert r_dash.status_code == 200, r_dash.text
    d = r_dash.json()

    assert d['atenciones_hoy'] >= 1
    assert d['atenciones_mes'] >= 1
    assert d['alumnos_atendidos_total'] >= 1
    assert 'inventario_alertas' in d
    assert 'ultimas_atenciones' in d
    assert len(d['ultimas_atenciones']) >= 1
    assert d['ultimas_atenciones'][0]['motivo'] == 'Cefalea intensa'
    assert 'grafica_mensual' in d
    assert len(d['grafica_mensual']) == 6

def test_3_alertas_medicas():
    h = get_auth_header()

    with SessionLocal.begin() as db:
        st = db.scalar(Base.metadata.tables['fichas_medicas'].select().where(Base.metadata.tables['fichas_medicas'].c.matricula == '24610010'))
        student_id = st.id

    r = client.get(f'/api/fichas/{student_id}', headers=h)
    assert r.status_code == 200
    ficha = r.json()
    assert 'alertas_medicas' in ficha
    alerts = ficha['alertas_medicas']
    assert alerts['estado'] == 'con_alertas'
    assert alerts['critico'] is True
    assert any(a['detalle'] == 'PENICILINA' for a in alerts['alergias'])

    # Alumno sin condiciones declaradas
    with SessionLocal.begin() as db:
        st_clean = db.get(Student, student_id)
        d = dict(st_clean.datos)
        d['alergia_medicamentos'] = 'N/A'
        d['alergia_alimentos'] = 'NINGUNA'
        d['antecedentes_personales'] = []
        d['medicamentos_no_administrar'] = 'N/A'
        d['pre_importado'] = False
        st_clean.datos = d

    r2 = client.get(f'/api/fichas/{student_id}', headers=h)
    alerts2 = r2.json()['alertas_medicas']
    assert alerts2['estado'] == 'sin_condiciones'
    assert alerts2['critico'] is False

def test_4_historial_atenciones_por_estudiante():
    h = get_auth_header()

    with SessionLocal.begin() as db:
        st = db.scalar(Base.metadata.tables['fichas_medicas'].select().where(Base.metadata.tables['fichas_medicas'].c.matricula == '24610010'))
        student_id = st.id

    r_hist = client.get(f'/api/fichas/{student_id}/historial', headers=h)
    assert r_hist.status_code == 200, r_hist.text
    h_data = r_hist.json()
    assert h_data['total_atenciones'] >= 1
    assert len(h_data['items']) >= 1
    first_event = h_data['items'][0]
    assert first_event['tipo'] == 'atencion'
    assert first_event['motivo'] == 'Cefalea intensa'
    assert first_event['detalles']['toma_ta'] == '120/80'

def test_5_inventario_inteligente():
    h = get_auth_header()
    today = datetime.now().date()

    # 5.1 Crear producto con stock agotado
    r1 = client.post('/api/inventario', json={
        'medicamento_material': 'Gasas estériles 10x10',
        'descripcion': 'Paquete con 10 gasas',
        'fecha_caducidad': (today + timedelta(days=200)).strftime('%Y-%m-%d'),
        'cantidad_inicio': 10,
        'cantidad_fin': 0,
        'stock_minimo': 4,
        'cuatrimestre': 'SEP-DIC 2026'
    }, headers=h)
    assert r1.status_code == 200

    # 5.2 Crear producto con stock bajo (2 <= 5)
    r2 = client.post('/api/inventario', json={
        'medicamento_material': 'Alcohol desnaturalizado 500ml',
        'descripcion': 'Frasco de 500ml',
        'fecha_caducidad': (today + timedelta(days=150)).strftime('%Y-%m-%d'),
        'cantidad_inicio': 8,
        'cantidad_fin': 2,
        'stock_minimo': 5,
        'cuatrimestre': 'SEP-DIC 2026'
    }, headers=h)
    assert r2.status_code == 200

    # 5.3 Crear producto próximo a caducar (<60 días)
    r3 = client.post('/api/inventario', json={
        'medicamento_material': 'Suero oral sabor uva',
        'descripcion': 'Sobre para preparar 1L',
        'fecha_caducidad': (today + timedelta(days=20)).strftime('%Y-%m-%d'),
        'cantidad_inicio': 20,
        'cantidad_fin': 15,
        'stock_minimo': 3,
        'cuatrimestre': 'SEP-DIC 2026'
    }, headers=h)
    assert r3.status_code == 200

    # 5.4 Listar inventario y verificar semáforos
    r_list = client.get('/api/inventario?cuatrimestre=SEP-DIC 2026', headers=h)
    assert r_list.status_code == 200
    items = r_list.json()

    gasas = next(i for i in items if i['medicamento_material'] == 'Gasas estériles 10x10')
    assert gasas['estado_stock']['estado'] == 'agotado'
    assert gasas['estado_stock']['color'] == 'rojo'

    alcohol = next(i for i in items if i['medicamento_material'] == 'Alcohol desnaturalizado 500ml')
    assert alcohol['estado_stock']['estado'] == 'stock_bajo'
    assert alcohol['estado_stock']['color'] == 'amarillo'

    suero = next(i for i in items if i['medicamento_material'] == 'Suero oral sabor uva')
    assert suero['estado_stock']['estado'] == 'por_caducar'
    assert suero['estado_stock']['color'] == 'amarillo'

    # 5.5 Probar filtros de estado
    r_agotados = client.get('/api/inventario?cuatrimestre=SEP-DIC 2026&filtro_estado=agotados', headers=h)
    assert len(r_agotados.json()) >= 1
    assert all(i['estado_stock']['estado'] in ('agotado', 'caducado') for i in r_agotados.json())

    r_criticos = client.get('/api/inventario?cuatrimestre=SEP-DIC 2026&filtro_estado=criticos', headers=h)
    assert len(r_criticos.json()) >= 3
