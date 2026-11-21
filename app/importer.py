"""Módulo de importación masiva de estudiantes (Excel y CSV) y generación de plantillas."""
import csv
import io
import re
import unicodedata
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

HEADER_MAP = {
    'matricula': ['matricula', 'no_control', 'num_control', 'nocontrol', 'control', 'clave', 'id'],
    'nombre_completo': ['nombre_completo', 'nombre', 'alumno', 'estudiante', 'nombres', 'nombre_aspirante', 'nombrecompleto'],
    'carrera': ['carrera', 'programa', 'programa_educativo', 'programaeducativo', 'especialidad', 'licenciatura', 'ingenieria', 'tsu'],
    'grupo': ['grupo', 'seccion', 'grado_grupo', 'aula'],
    'correo': ['correo', 'email', 'correo_institucional', 'correoinstitucional', 'correo_electronico', 'correoelectronico']
}

def normalize_key(text: str) -> str:
    if not text:
        return ''
    s = str(text).strip().lower()
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
    s = re.sub(r'[\s\-_]+', '_', s)
    s = re.sub(r'[^a-z0-9_]', '', s).strip('_')
    return s

def generate_template_csv() -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["matricula", "nombre_completo", "carrera", "grupo", "correo"])
    # UTF-8 BOM para apertura correcta en Excel y hojas de cálculo
    return b'\xef\xbb\xbf' + output.getvalue().encode('utf-8')

def generate_template_excel() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Estudiantes UTGZ"

    headers = ["Matrícula", "Nombre Completo", "Carrera / Programa Educativo", "Grupo", "Correo Institucional"]
    ws.append(headers)

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="28684F", end_color="28684F", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin', color='DCE5DC'),
        right=Side(style='thin', color='DCE5DC'),
        top=Side(style='thin', color='DCE5DC'),
        bottom=Side(style='thin', color='DCE5DC')
    )

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border

    # Anchos óptimos de columna para facilitar captura limpia
    widths = [18, 36, 46, 14, 32]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

def parse_student_file(content: bytes, filename: str) -> list[dict]:
    filename_lower = (filename or '').lower()
    raw_rows: list[list[str]] = []

    if filename_lower.endswith(('.xlsx', '.xlsm', '.xltx')):
        from openpyxl import load_workbook
        wb = load_workbook(filename=io.BytesIO(content), data_only=True)
        ws = wb.active
        for row in ws.iter_rows(values_only=True):
            if any(cell is not None and str(cell).strip() != '' for cell in row):
                raw_rows.append([str(c).strip() if c is not None else '' for c in row])
    else:
        # Try different encodings for CSV
        text_content = None
        for enc in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
            try:
                text_content = content.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if text_content is None:
            text_content = content.decode('utf-8', errors='replace')

        # Detect delimiter: comma, semicolon, tab
        first_line = text_content.splitlines()[0] if text_content.splitlines() else ''
        delim = ','
        if ';' in first_line and first_line.count(';') > first_line.count(','):
            delim = ';'
        elif '\t' in first_line and first_line.count('\t') > first_line.count(','):
            delim = '\t'

        reader = csv.reader(io.StringIO(text_content), delimiter=delim)
        for row in reader:
            if any(cell.strip() for cell in row):
                raw_rows.append([cell.strip() for cell in row])

    if not raw_rows:
        return []

    # Map headers
    header_row = raw_rows[0]
    col_mapping = {}
    for idx, col_name in enumerate(header_row):
        norm = normalize_key(col_name)
        for target, aliases in HEADER_MAP.items():
            if target not in col_mapping and (norm == target or norm in aliases or any(a in norm for a in aliases)):
                col_mapping[target] = idx
                break

    # If matricula or nombre was not matched by name, fallback to positional if standard 5 columns
    if 'matricula' not in col_mapping and len(header_row) >= 2:
        col_mapping['matricula'] = 0
    if 'nombre_completo' not in col_mapping and len(header_row) >= 2:
        col_mapping['nombre_completo'] = 1
    if 'carrera' not in col_mapping and len(header_row) >= 3:
        col_mapping['carrera'] = 2
    if 'grupo' not in col_mapping and len(header_row) >= 4:
        col_mapping['grupo'] = 3
    if 'correo' not in col_mapping and len(header_row) >= 5:
        col_mapping['correo'] = 4

    parsed: list[dict] = []
    # Process data rows starting from row 2
    for row_num, row in enumerate(raw_rows[1:], start=2):
        if not any(cell for cell in row):
            continue

        def get_val(key):
            idx = col_mapping.get(key)
            if idx is not None and idx < len(row):
                return row[idx].strip()
            return ''

        matricula = get_val('matricula')
        nombre = get_val('nombre_completo')
        carrera = get_val('carrera')
        grupo = get_val('grupo')
        correo = get_val('correo')

        error = None
        if not matricula:
            error = "Matrícula requerida"
        elif not nombre:
            error = "Nombre completo requerido"
        elif correo and not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', correo):
            error = f"Correo inválido: {correo}"

        parsed.append({
            'fila': row_num,
            'matricula': matricula,
            'nombre_completo': nombre,
            'carrera': carrera,
            'grupo': grupo,
            'correo': correo,
            'error': error
        })

    return parsed
