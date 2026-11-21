# SAMU v2 — Pruebas y entrega

## Pruebas automatizadas ejecutadas

`pytest -q tests/test_end_to_end.py`: **3 pruebas superadas** (5 de noviembre de 2026). Se comprobaron el acceso a páginas, rechazo de acceso sin sesión, ficha médica sin correo del estudiante, edad calculada, validación y correo registrados por Enfermería, bitácora, canalización, inventario, cuatro PDFs, descargas temporales de un solo uso, contactos guardados, envío SMTP **simulado** y protección CSRF.

`node --check app/static/app.js`: sintaxis validada.

Generación PDF con ReportLab: 4 documentos de prueba procesados y renderizados sin errores usando datos inventados.

## Pruebas pendientes antes del uso institucional

- Verificar la interfaz y las firmas con dedos en teléfonos Android e iPhone reales (la automatización visual del entorno está limitada).
- Crear el APK con Flutter SDK, instalarlo y probar el comportamiento del enlace de PDF en navegador externo.
- Configurar SMTP oficial e investigar entregabilidad real en correos autorizados (no se enviaron correos reales durante el desarrollo).
- Configurar dominio, servidor Linux, base PostgreSQL, HTTPS real y respaldos verificados.
- Revisar todos los formatos PDF contra originales validados por el personal de Enfermería.
- Evaluación de seguridad, consentimiento y privacidad para el tratamiento de datos de salud.
- Prueba de estrés y concurrencia si se prevé captura simultánea por numerosos alumnos.

## Estado

**Entrega: código fuente funcional de pruebas, NO sistema certificado para uso clínico.** No existe un APK compilado ni URL pública configurada dentro del ZIP. Para operar todos los días será necesario subir la solución a un servidor activo y conectar el dominio y el correo institucional.
