# SAMU · Sistema de Atención Médica Universitaria — UTGZ

[![Pipeline CI/CD](https://github.com/DEYA7276/samu-utgz/actions/workflows/deploy.yml/badge.svg)](https://github.com/DEYA7276/samu-utgz/actions)
[![Vercel Deployment](https://img.shields.io/badge/Deployment-Vercel-black?logo=vercel)](https://samu-utgz.vercel.app)
[![Version](https://img.shields.io/badge/Version-v2.0.0-28684F)](https://github.com/DEYA7276/samu-utgz)

**Versión 2.0 · proyecto de desarrollo y despliegue continuo (DevOps) para la Universidad Tecnológica de Gutiérrez Zamora.**

Diseñado para enfermería de la Universidad Tecnológica de Gutiérrez Zamora. Se tomaron como referencia principal las cuatro fotos de formatos físicos recibidas del personal: **ficha médica, bitácora FOR-23-04a, canalización externa FOR-23-05 e inventario por cuatrimestre**. **No contiene registros reales copiados de las fotografías**.

## ¿Qué incluye?

| Módulo | Funcionalidad implementada |
|---|---|
| Alumno/aspirante | Ficha médica por pasos con firma y autorización, fecha de nacimiento, edad calculada, género, NSS, tipo de sangre y carrera UTGZ. El NSS se cifra con los demás datos clínicos y se reutiliza al vincular la ficha en Enfermería; no se consulta al IMSS |
| Enfermería | Inicio de sesión con contraseña, roles, sesiones y protección CSRF, consulta y validación de fichas, matrícula y fotografía |
| Bitácora | Registro de atención con consulta y descarga de PDF por mes |
| Canalización externa | Campos del FOR-23-05, firmas, consentimiento, PDF, envío vía SMTP a correos institucionales almacenados en base de datos y bitácora de envíos |
| Inventario | Medicamento/material de curación, cantidades de inicio y fin por cuatrimestre, filtros y descarga de reporte PDF cuatrimestral |
| Android | Proyecto Flutter para compilar APK, sin Expo Go para usuarios finales |
| iPhone/iPad | PWA para Safari: Compartir → Agregar a pantalla de inicio |

**Diseño:** tema verde salvia de UTGZ y modo oscuro seleccionable, con preferencia guardada en el dispositivo. El logo PNG tiene fondo transparente y se utiliza en la web/PWA y como ícono del APK.

La oferta educativa se mantiene como catálogo seleccionable en las fichas y formularios de Enfermería. Google OAuth queda desactivado hasta que la institución configure credenciales y autorice el proveedor de identidad; mientras tanto, se conserva el inicio de sesión institucional actual con correo y contraseña.

## Decisión técnica

Se eligió **FastAPI + SQLAlchemy + PostgreSQL** para esta versión; aunque la especificación anterior contemplaba Laravel/MySQL, la base y el backend son reemplazables y no afectan los campos originales. **SQLite** se utiliza automáticamente solo en desarrollo. Los campos clínicos, firmas y fotografías se guardan cifrados con Fernet (la clave debe persistir y mantenerse segura). El frontend es PWA con HTML/CSS/JavaScript, sin servicios de terceros para dibujar firmas; Flutter implementa el contenedor Android. La PWA permite abrir la interfaz sin instalar software externo, pero **el envío y consulta de datos requieren Internet**. Los datos clínicos nunca se cachean con el service worker.

## Prueba local en Windows (solo desarrollo)

Requiere Python 3.12+ y terminal PowerShell. Abrir una terminal en la carpeta raíz del ZIP:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:APP_ENV="development"
python -m app.cli create-admin --email enfermeria@ejemplo.edu.mx --name "Responsable de Enfermería"
uvicorn app.main:app --reload --env-file .env
```

Visitar `http://127.0.0.1:8000`. Carga el `.env` para que el servidor use la misma clave de cifrado con la que se guardaron los datos; no arranques el servidor con una clave distinta. El formulario del alumno no solicita correo ni código; su correo lo registra Enfermería durante la validación. No usar el modo de desarrollo con información médica personal de verdad. El administrador se crea una única vez; la contraseña se ingresa de manera interactiva (mínimo 12 caracteres).

## Publicación para que nadie encienda XAMPP

El backend funciona de manera permanente en un servidor **VPS o hosting administrado** con Docker, PostgreSQL y Caddy (HTTPS automático). El equipo de Enfermería solo necesita Internet y el enlace del dominio. Se pagan los recursos del proveedor y se realizan tareas de actualización y monitoreo.

1. Contratar o disponer de un VPS Linux con Docker Compose y dominio administrado por la institución, con puertos 80/443 accesibles.
2. Copiar todos los archivos de este proyecto al VPS. Crear `.env` a partir de `.env.example` **sin compartirlo** y definir `SAMU_DOMAIN`, `POSTGRES_PASSWORD`, `DATA_ENCRYPTION_KEY`, `OTP_PEPPER` y cuentas `SMTP_*`. Generar la clave con:
   `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
3. Apuntar registro DNS A del dominio al servidor. Registrar contraseña fuerte del administrador y custodiar claves fuera del repositorio.
4. Desde `deploy/` ejecutar `docker compose --env-file ../.env -f compose.yaml up -d --build`. El servidor reinicia automáticamente los contenedores tras reinicios del sistema.
5. Para crear el administrador de Enfermería, ejecutar desde `deploy/`:
   `docker compose --env-file ../.env -f compose.yaml exec api python -m app.cli create-admin --email admin@tu-dominio.edu.mx --name "Responsable de Enfermería"`
6. Abrir `https://tu-dominio.edu.mx/healthz` y luego `/login` y `/alumno` para comprobar funcionamiento.
7. Realizar pruebas con datos inventados y **auditoría de privacidad y seguridad antes de incorporar información médica real**.

**Copia de seguridad:** planificar un `pg_dump` cifrado diario de PostgreSQL y conservar por separado `DATA_ENCRYPTION_KEY`. Ejemplo de volcado manual desde `deploy/`:

```bash
docker compose --env-file ../.env -f compose.yaml exec -T database pg_dump -U samu samu > samu_backup_$(date +%F).sql
```

Conservar el respaldo en almacenamiento **cifrado** con control de acceso (no subir bases clínicas a Drive o GitHub). Probar restauración regularmente; rotación de logs, supervisión y actualizaciones siguen siendo responsabilidad técnica.

## SMTP — envío real al correo

En `.env`, definir SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM y SMTP_TLS. La cuenta debe estar habilitada para SMTP por su proveedor de correo; no se inventan credenciales. Enfermería guarda los correos autorizados en **Destinatarios guardados**; al abrir una canalización puede elegir destinatarios y pulsar **Enviar PDF por correo**. El sistema registra aceptación SMTP y fallos; **aceptación no significa entrega final ni lectura**. Confirmar autorización institucional y políticas de transferencia de datos médicos antes de habilitar.

## PWA para iPhone

Publicar primero en HTTPS. Abrir Safari en el iPhone → visitar la URL → botón **Compartir** → **Agregar a pantalla de inicio** → Abrir SAMU. La app usa Internet para los registros, no necesita App Store ni Expo Go.

## APK Android con Flutter

Seguir `android_flutter/README.md`. Flutter SDK es necesario **solo en la computadora que compila**, no en los celulares que instalan el APK. El ZIP contiene el código para generar el APK, **no un APK compilado**. Una APK compilada debe probarse en un teléfono físico.

## Seguridad y limitaciones que no debes ignorar

- Acceso a expedientes solo con sesión de Enfermería. Los datos sensibles se cifran en la base de datos y en los respaldos es obligatorio proteger también las claves.
- Nunca usar fotografías de fichas reales como datos de ejemplo. Mantener documentos sensibles fuera de GitHub y Google Drive compartido.
- La firma táctil es un trazo digital **no una firma electrónica avanzada**; revisar validez legal y consentimiento institucional.
- El formulario conserva el contenido visible de los formatos entregados; la vista web usa campos adicionales únicamente para seguridad y vinculación técnica (fecha de nacimiento/edad calculada, sexo/género y folio).
- Requiere integrar el correo institucional de Enfermería, confirmar autorización para tratar datos médicos, evaluar políticas de protección de datos personales en México y realizar pruebas de aceptación con el personal de Enfermería.
- No promete disponibilidad 100% ni mantenimiento cero. El hosting debe monitorearse y mantenerse actualizado.
- No incluye cifrado extremo a extremo; el servidor accede a los datos para procesar y generar los PDFs. El acceso al servidor debe estar restringido.
- Un solo servidor no equivale a alta disponibilidad; para operación de misión crítica se necesita redundancia, políticas de recuperación y soporte.

## Estructura

```
app/main.py                API FastAPI
app/db.py                  Modelos y cifrado clínico
app/auth.py                Sesiones, roles, CSRF y contraseñas
app/mailer.py              Envío SMTP real
app/pdf_templates.py       PDF que reproduce los campos originales
app/static/index.html      Entrada de la PWA
app/static/style.css       Diseño responsive mate
app/static/app.js          Formularios, bitácora, inventario, firma táctil
app/static/service-worker.js  Offline solo de recursos estáticos
app/cli.py                 Alta inicial de administrador
android_flutter/           Código para compilar APK Flutter
   lib/main.dart
deploy/                    Docker, PostgreSQL, Caddy HTTPS
tests/                     Pruebas de flujo con datos ficticios
```

## Ejecutar pruebas

```bash
pip install -r requirements-dev.txt
pytest -q tests/
```

Los tests usan correos `@ejemplo.test` y simulan SMTP: no envían información clínica a terceras personas. **Esta versión requiere revisión humana, pruebas en dispositivos reales y evaluación de seguridad antes de uso institucional.**
