"""Pruebas automatizadas con datos completamente ficticios y envío SMTP simulado."""
import os, tempfile, base64, io
from pathlib import Path
from PIL import Image, ImageDraw
os.environ['APP_ENV']='development'
os.environ['DATABASE_URL']='sqlite:///'+str(Path(tempfile.gettempdir())/'samu_test_2026.sqlite3')
os.environ['SAMU_PRIVATE_DIR']=str(Path(tempfile.gettempdir())/'samu_test_private')
from fastapi.testclient import TestClient
from app.db import SessionLocal, init_db, Base, engine, Nurse, Contact
from app.auth import hash_password
from app.main import app

client=TestClient(app)

def sig():
 im=Image.new('RGBA',(460,130),'white');d=ImageDraw.Draw(im);d.line([(8,88),(100,24),(160,92),(260,22),(400,88)],fill='#12345a',width=6)
 b=io.BytesIO();im.save(b,'PNG');return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()

def setup_module():
 Base.metadata.drop_all(engine);init_db()
 with SessionLocal.begin() as db:
  db.add(Nurse(name='Responsable ficticio',email='enfermeria@ejemplo.test',password_hash=hash_password.hash('ContraseñaSegura_123'),role='admin'))

def login():
 r=client.post('/api/session/login',json={'email':'enfermeria@ejemplo.test','password':'ContraseñaSegura_123'})
 assert r.status_code==200,r.text
 return {'X-CSRF-Token':r.json()['csrf']}

def test_main_routes():
 assert client.get('/').status_code==200
 assert client.get('/static/style.css').status_code==200
 assert client.get('/static/app.js').status_code==200
 assert client.get('/manifest.webmanifest').status_code==200
 assert client.get('/service-worker.js').status_code==200
 assert client.get('/healthz').json()['ok']
 assert client.get('/api/fichas').status_code==401
 assert client.get('/api/catalogos').json()['generos']==['Hombre','Mujer','Otro','Prefiero no especificar']


def test_student_form_nurse_email_and_pdfs(monkeypatch):
 sign=sig()
 payload={
  'nombre_aspirante':'Aspirante Prueba','fecha_nacimiento':'2007-09-15','sexo':'Mujer',
  'nss':'12345678901','tipo_sangre':'O+',
  'antecedentes_familiares':['DIABETES'],'antecedentes_personales':['ASMA'],
  'otro_personal':'N/A','intervenciones_quirurgicas':'N/A','traumatismos':'N/A',
  'alergia_medicamentos':'N/A','alergia_alimentos':'N/A','alergia_plantas':'N/A','alergia_ambientales':'N/A','alergia_otros':'N/A',
  'padecimientos':'N/A','tratamiento_medico':'N/A','control_preventivo':'N/A','medicamentos_no_administrar':'N/A',
  'nombre_medico':'N/A','telefono_medico':'N/A','hospital_preferencia':'N/A',
  'autoriza_traslado':True,'nombre_padre_tutor':'Tutor Prueba','telefono_padre_tutor':'0000000000',
  'firma_padre_tutor':sign,'firma_aspirante':sign,
 }
 r=client.post('/api/alumnos/ficha',json=payload)
 assert r.status_code==200,r.text
 assert r.json()['folio'].startswith('FIC-')
 assert client.post('/api/alumnos/ficha',json={**payload,'sitio_web':'spam'}).status_code==422
 assert client.post('/api/alumnos/ficha',json={**payload,'sexo':'Masculino'}).status_code==422
 assert client.post('/api/alumnos/ficha',json={**payload,'nss':'1234'}).status_code==422
 h=login()
 fichas=client.get('/api/fichas');assert len(fichas.json())==1
 ident=fichas.json()[0]['id'];r=client.get(f'/api/fichas/{ident}')
 assert r.status_code==200 and r.json()['datos']['alergia_medicamentos']=='N/A'
 assert r.json()['email_verificacion']==''
 assert r.json()['datos']['fecha_nacimiento']=='2007-09-15'
 assert r.json()['datos']['nss']=='12345678901'
 assert r.json()['datos']['tipo_sangre']=='O+'
 assert r.json()['edad_actual']>=19
 r=client.post(f'/api/fichas/{ident}/validar',json={'matricula':'123456789','correo':'aspirante@ejemplo.test'},headers=h)
 assert r.status_code==200,r.text
 assert client.get('/api/estudiantes').json()[0]['correo']=='aspirante@ejemplo.test'
 assert client.get('/api/estudiantes').json()[0]['sexo']=='Mujer'
 assert client.get('/api/estudiantes').json()[0]['nss']=='12345678901'
 assert client.get('/api/estudiantes').json()[0]['programa_educativo']==''
 assert client.put(f'/api/fichas/{ident}/correo',json={'correo':'nuevo@ejemplo.test'},headers=h).status_code==200
 assert client.get('/api/estudiantes').json()[0]['correo']=='nuevo@ejemplo.test'
 
 # Formato de la bitácora: las 16 columnas del documento físico.
 att={
  'student_id':ident,'fecha':'2026-11-05','hora':'09:58','nombre':'Aspirante Prueba','matricula':'123456789','edad':'19','sexo':'Mujer',
  'programa_educativo':'Ingeniería en Mecatrónica','grupo':'1010 AEI','motivo_consulta':'Dolor de cabeza',
  'toma_ta':'120/80','otro_procedimiento':'N/A','suministro_medicamento':'N/A','material_curacion':'N/A',
  'firma_usuario':sign,'firma_enfermeria':sign,
 }
 r=client.post('/api/bitacora',json=att,headers=h);assert r.status_code==200,r.text

 ref={
  'student_id':ident,'nombre_completo':'Aspirante Prueba','nss':'12345678901','sexo':'Mujer','edad':'19','estado_civil':'Soltero(a)',
  'programa_puesto':'Ingeniería en Mecatrónica','matricula_empleado':'123456789','telefono_celular':'0000000000','contacto_emergencia':'Tutor Prueba',
  'telefono_emergencia':'0000000000','domicilio':'Domicilio ficticio, Veracruz','correo_electronico':'aspirante@ejemplo.test',
  'motivo_canalizacion':'Valoración externa solicitada','ta':'120/80','fc':'80','sato2':'98%','fr':'18','temperatura':'36.5 C','fecha':'2026-11-05','hora':'10:00','elaboro':'Responsable ficticio',
  'consentimiento_informado':True,'firma_responsable':sign,'firma_consentimiento':sign,
 }
 r=client.post('/api/canalizaciones',json=ref,headers=h);assert r.status_code==200,r.text
 refid=r.json()['id']

 r=client.get('/api/bitacora?mes=2026-11',headers=h)
 assert r.status_code==200 and len(r.json())==1
 assert client.get('/api/bitacora?mes=2026-10',headers=h).json()==[]
 r=client.post('/api/descargas',json={'tipo':'bitacora','mes':'2026-11'},headers=h)
 assert r.status_code==200,r.text
 monthly=client.get(r.json()['url'])
 assert monthly.status_code==200 and monthly.content.startswith(b'%PDF-')
 from pypdf import PdfReader
 monthly_text=PdfReader(io.BytesIO(monthly.content)).pages[0].extract_text()
 assert 'REPORTE MENSUAL: 2026-11' in monthly_text
 assert client.post('/api/descargas',json={'tipo':'bitacora','mes':'2026-13'},headers=h).status_code==400

 r=client.post('/api/inventario',json={'medicamento_material':'Material de prueba','descripcion':'Caja con 10 piezas','fecha_caducidad':'2027-05-01','cantidad_inicio':5,'cantidad_fin':3,'cuatrimestre':'SEP-DIC 2026'},headers=h)
 assert r.status_code==200,r.text
 inv_id=r.json()['id']
 r=client.put(f'/api/inventario/{inv_id}',json={'medicamento_material':'Material de prueba','descripcion':'Caja con 10 piezas','fecha_caducidad':'2027-05-01','cantidad_inicio':5,'cantidad_fin':4,'cuatrimestre':'SEP-DIC 2026'},headers=h)
 assert r.status_code==200,r.text
 assert client.get('/api/inventario').json()[0]['cantidad_fin']==4
 for kind,item in [('ficha',ident),('canalizacion',refid),('bitacora',None),('inventario',None)]:
  r=client.post('/api/descargas',json={'tipo':kind,'id':item},headers=h)
  assert r.status_code==200,r.text
  link=r.json()['url'];r=client.get(link)
  assert r.status_code==200 and r.headers['content-type']=='application/pdf' and r.content.startswith(b'%PDF-'),(kind,r.status_code,r.text[:250])
  assert len(r.content)>1000
  if kind=='canalizacion':
   from pypdf import PdfReader
   txt=PdfReader(io.BytesIO(r.content)).pages[0].extract_text()
   assert 'Código: FOR-26-11' in txt
   assert 'Revisión: 01' in txt
   assert 'Emisión: 05/11/26' in txt
   for sign_label in ['T/A: 120/80','FC: 80','SatO2: 98%','FR: 18','Tª: 36.5 C']:
    assert sign_label in txt,repr(sign_label)
  assert client.get(link).status_code==410

 r=client.post('/api/contactos',json={'nombre':'Jefatura Prueba','correo':'jefatura@ejemplo.test','area':'ING'},headers=h)
 assert r.status_code==200,r.text
 contactid=r.json()['id']
 sent=[]
 monkeypatch.setattr('app.mailer.has_smtp',lambda:True)
 monkeypatch.setattr('app.mailer.send_mail',lambda *a,**k:sent.append(a))
 r=client.post(f'/api/canalizaciones/{refid}/enviar',json={'contact_ids':[contactid]},headers=h)
 assert r.status_code==200 and r.json()['ok'] and len(sent)==1,r.text
 assert sent[0][0]=='jefatura@ejemplo.test'
 assert sent[0][3].startswith(b'%PDF-')
 assert client.get(f'/api/canalizaciones/{refid}/envios').status_code==200


def test_csrf_and_wrong_login():
 assert client.post('/api/inventario',json={}).status_code==403
 assert client.post('/api/session/login',json={'email':'enfermeria@ejemplo.test','password':'contraseña incorrecta'}).status_code==401


def test_referral_metadata_uses_record_date_not_download_day():
 from types import SimpleNamespace
 from pypdf import PdfReader
 from app.pdf_templates import referral_pdf
 logo_size=Image.open(Path(__file__).parent.parent/'app'/'static'/'assets'/'utgz-logo.png').size
 for date, code, emision in [
  ('2025-03-14', 'FOR-25-03', '14/03/25'),
  ('2026-11-05', 'FOR-26-11', '05/11/26'),
  ('2027-01-02', 'FOR-27-01', '02/01/27'),
 ]:
  document=PdfReader(io.BytesIO(referral_pdf(SimpleNamespace(fecha=date,datos={'nombre_completo':'Prueba'}))))
  assert any(image.image.size==logo_size and image.image.mode=='RGBA' for image in document.pages[0].images)
  text=document.pages[0].extract_text()
  assert f'Código: {code}' in text
  assert f'Emisión: {emision}' in text
  assert 'Revisión: 01' in text
