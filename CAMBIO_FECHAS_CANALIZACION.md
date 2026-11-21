# Actualización del encabezado de canalización — V2

Solo se ha automatizado el encabezado de **Canalización Externa**.

- **Código**: `FOR-AA-MM`, donde `AA` es el año de dos dígitos y `MM` el mes de la **fecha de la canalización**. Ejemplo: `FOR-26-11` para noviembre de 2026.
- **Revisión**: `01` (sin cambios).
- **Emisión**: fecha de la canalización en formato `DD/MM/AA`. Ejemplo: `05/11/26`.
- La fecha se toma del dato **Fecha** que registra Enfermería al elaborar la canalización. **Reimprimir un documento anterior conserva el código y emisión originales de su registro**, aunque se descargue otro día.
- El encabezado informativo en pantalla también se actualiza al modificar la fecha del formulario.
- **No se modificaron** el diseño, el logotipo SAMU, el logotipo BiS+UTGZ de canalización, ni otros formatos PDF.

## Para usar

1. Descomprime el ZIP como una carpeta nueva.
2. No reemplaces ni borres tu `.env`, carpeta `private` o claves de cifrado. Conserva el respaldo antes de migrar cualquier dato.
3. Instala dependencias como en el README, inicia el servidor desde la nueva carpeta, y prueba una canalización.
