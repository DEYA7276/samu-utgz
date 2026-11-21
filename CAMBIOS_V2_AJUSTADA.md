# SAMU - Ajustes mínimos sobre el diseño V2

- El logo de la UTGZ se usa en PNG transparente en los encabezados de todos los PDF generados; el logo de SAMU se conserva en la aplicación.
- En el login de Enfermería aparece un botón adicional para que el estudiante pueda llenar la ficha. La portada V2 sigue igual.
- En el formulario de alumnos se agrega fecha de nacimiento, cálculo instantáneo de edad y selección de sexo/género. La edad se vuelve a calcular desde el servidor.
- El alumno **no captura matrícula ni correo**. Enfermería registra ambos al validar la ficha y puede actualizar el correo posteriormente.
- Los datos disponibles de la ficha validada (nombre, matrícula, sexo/género, edad, correo registrado por Enfermería y contacto/teléfono del tutor) se reutilizan en bitácora y canalizaciones.
- En canalización, aparecen T/A, FC, SatO2, FR y Tª dentro del recuadro Motivo de canalización, en pantalla y en el PDF.
- Los PDF de ficha médica, canalización, bitácora e inventario usan `app/static/assets/utgz-logo.png`, recortado del logotipo institucional disponible en los formatos.
- El formulario público sin correo/OTP tiene un límite básico de envíos y honeypot, pero **antes de producción** requiere antiabuso adicional (por ejemplo CAPTCHA validado en servidor, controles del proxy y limitación de solicitudes). Usar HTTPS; no capturar fichas reales por HTTP de la red local.
- Compatible con las fichas históricas: `email_verificacion` conserva el dato previo, mientras fichas nuevas quedan vacías hasta que Enfermería lo registre. Conservar **toda la carpeta `private` y su clave** del mismo entorno antes de actualizar.

## Prueba rápida

1. Abrir la raíz del proyecto y crear/activar el venv de V2 si no existe.
2. Iniciar servidor con `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --env-file .env` (si `.env` existe).
3. Abrir `http://127.0.0.1:8000/`: diseño V2 y 2 accesos.
4. Abrir `/alumno`: llenar fecha de nacimiento, comprobar edad, continuar ficha sin correo.
5. Abrir `/login`: botón adicional `Soy estudiante · Llenar ficha médica`.
6. Registrar alumno con datos de prueba, entrar como Enfermería y validar con matrícula + correo; comprobar canalización PDF.

La APK de Android debe compilarse nuevamente si se cambió la dirección del servidor. Se conserva la configuración de Flutter que exige HTTPS para la versión que se distribuya.
