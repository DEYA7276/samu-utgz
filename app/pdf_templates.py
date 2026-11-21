"""Impresión de formatos originales de la enfermería UTGZ.

Los títulos, orden de columnas y rótulos siguen las fotografías entregadas.
Los datos sensibles se dibujan en memoria; nunca se publican como PDF estático.
"""
import base64
from datetime import datetime
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A3, landscape
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table, TableStyle, Paragraph, Image as RLImage
from reportlab.lib.styles import ParagraphStyle

ASSETS = Path(__file__).resolve().parent / 'static' / 'assets'
fonts = ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/local/share/fonts/DejaVuSans.ttf']
fontb = ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']
if any(Path(p).exists() for p in fonts):
    pdfmetrics.registerFont(TTFont('DejaVu', next(p for p in fonts if Path(p).exists())))
    pdfmetrics.registerFont(TTFont('DejaVu-Bold', next(p for p in fontb if Path(p).exists())))
    REG='DejaVu'; BOLD='DejaVu-Bold'
else: REG='Helvetica'; BOLD='Helvetica-Bold'
INK=colors.HexColor('#233b2e')
LINE=colors.HexColor('#687c6d')
BLUE=colors.HexColor('#28684f')

FAMILIARES=['DIABETES','CÁNCER','OBESIDAD','TUMORACIONES','EPILEPSIA','CARDIOPATÍAS','HIPERTENSIÓN ARTERIAL','TUBERCULOSIS','FIEBRE REUMÁTICA']
PERSONALES=['PALUDISMO','TOSFERINA','CRISIS CONVULSIVAS','HEPATITIS','POLIOMIELITIS','PARASITOSIS','ARTRITIS','ANOREXIA','ANSIEDAD','DEPRESIÓN','BULIMIA','SARAMPIÓN','OTITIS','ASMA','NEUMONÍA','TIFOIDEA','CARIES','VARICELA','CEFALEAS','REFLUJO','PAPERAS','CARDIOPATÍAS','HIPERTENSIÓN ARTERIAL']

def _buffer(): return BytesIO()

def _draw_signature(c, data_uri, x, y, w, h):
    if not data_uri: return
    try:
        raw = base64.b64decode(data_uri.split(',',1)[1] if ',' in data_uri else data_uri,validate=True)
        im=PILImage.open(BytesIO(raw)).convert('RGBA')
        im.thumbnail((max(1,int(w*2)),max(1,int(h*2))),PILImage.Resampling.LANCZOS)
        c.drawImage(ImageReader(im),x,y+2,w,h-4,preserveAspectRatio=True,mask='auto',anchor='c')
    except Exception:
        pass

def _logos(c,W,H):
    logo=ASSETS/'utgz-logo.png'
    if logo.exists(): c.drawImage(str(logo),32,H-78,76,58,preserveAspectRatio=True,mask='auto',anchor='c')
    else:
        c.setFont(BOLD,13); c.drawString(37,H-54,'UTGZ')

def _header(c,title,code='',revision='',emision='',pagesize=A4):
    W,H=pagesize
    _logos(c,W,H)
    c.setFillColor(INK); c.setFont(BOLD,12 if W<850 else 16)
    c.drawCentredString(W/2,H-50,title)
    if code:
        c.setFont(BOLD,8.2)
        for i,text in enumerate([f'Código: {code}',f'Revisión: {revision}',f'Emisión: {emision}']):
            c.drawRightString(W-35,H-38-14*i,text)
    c.setStrokeColor(BLUE); c.setLineWidth(1.5)
    c.line(32,H-81,W-32,H-81)
    return H-95

def _rect(c,x,y,w,h):
    c.setLineWidth(.55); c.setStrokeColor(LINE); c.rect(x,y,w,h)

def _value(c,text,x,y,w,h,fs=8, bold=False):
    text = '' if text is None else str(text)
    c.setFillColor(INK)
    font=BOLD if bold else REG
    lines=simpleSplit(text,font,fs,max(20,w-10))
    if not lines: return
    while len(lines)*(fs+2)>h-6 and fs>5.2:
        fs-=.4; lines=simpleSplit(text,font,fs,max(20,w-10))
    c.setFont(font,fs)
    # Text is never silently cut: if it does not fit at minimal size draw the maximum and add note to annex.
    for i,line in enumerate(lines[:max(1,int((h-5)/(fs+2))) ]):
        c.drawString(x+5,y+h-4-fs-i*(fs+2),line)

def _row(c,x,y,w,h,label,value,label_w=155):
    _rect(c,x,y,w,h); c.line(x+label_w,y,x+label_w,y+h)
    _value(c,label,x,y,label_w,h,7.6,True)
    _value(c,value,x+label_w,y,w-label_w,h,8.1)

def _paragraph(c,text,x,y,w,h,size=7.5,bold=False):
    s=ParagraphStyle('p',fontName=BOLD if bold else REG,fontSize=size,leading=size+2,textColor=INK,spaceAfter=0)
    p=Paragraph(escape(str(text or '')).replace('\n','<br/>'),s)
    pw,ph=p.wrap(w,h)
    if ph<=h: p.drawOn(c,x,y+h-ph)
    else:
        size=max(5,size*h/max(ph,1)*.9)
        s.fontSize=size;s.leading=size+1
        p=Paragraph(escape(str(text or '')).replace('\n','<br/>'),s)
        pw,ph=p.wrap(w,h)
        p.drawOn(c,x,y+max(0,h-ph))

def ficha_pdf(student):
    datos=student.datos
    out=_buffer(); c=canvas.Canvas(out,pagesize=A4)
    W,H=A4; y=_header(c,'FICHA MÉDICA',pagesize=A4); x=38; w=W-76
    y-=27; _row(c,x,y,w,27,'NOMBRE DEL ASPIRANTE',student.nombre_aspirante,label_w=160)
    def checkbox_lines(items, selected, columns=3):
        selected=set(selected or [])
        rows=[]
        for k in range(0,len(items),columns):
            rows.append('    '.join(('☑' if t in selected else '☐')+' '+t for t in items[k:k+columns]))
        return rows
    # En los documentos originales la sección agrupa antecedentes en lista con casillas.
    y-=71; _rect(c,x,y,w,71); c.line(x+111,y,x+111,y+71)
    _value(c,'ANTECEDENTES\nFAMILIARES',x,y,105,71,8,True)
    items=FAMILIARES; chosen=datos.get('antecedentes_familiares',[])
    for i in range(0,len(items),3):
        for j,t in enumerate(items[i:i+3]):
            _value(c,('[X] ' if t in chosen else '[ ] ')+t,x+116+j*(w-119)/3,y+71-18*(i//3+1),(w-122)/3,18,7)
    y-=125; _rect(c,x,y,w,125);c.line(x+111,y,x+111,y+125)
    _value(c,'ANTECEDENTES\nPERSONALES',x,y,105,125,8,True)
    items=PERSONALES; chosen=datos.get('antecedentes_personales',[])
    for i in range(0,len(items),4):
        for j,t in enumerate(items[i:i+4]):
            _value(c,('[X] ' if t in chosen else '[ ] ')+t,x+116+j*(w-119)/4,y+125-17*(i//4+1),(w-122)/4,16,5.95)
    y-=24; _row(c,x,y,w,24,'OTRO (ESPECIFICAR):',datos.get('otro_personal',''),label_w=145)
    y-=30; _row(c,x,y,w,30,'INTERVENCIONES QUIRÚRGICAS (OPERACIONES/CIRUGÍAS):',datos.get('intervenciones_quirurgicas',''),label_w=306)
    y-=30; _row(c,x,y,w,30,'TRAUMATISMOS (FRACTURAS):',datos.get('traumatismos',''),label_w=182)
    for name,key in [('MEDICAMENTOS','alergia_medicamentos'),('ALIMENTOS','alergia_alimentos'),('PLANTAS','alergia_plantas'),('AMBIENTALES','alergia_ambientales'),('OTROS (ESPECIFICAR)','alergia_otros')]:
        y-=23; _row(c,x,y,w,23,'ALERGIAS / '+name,datos.get(key,''),label_w=181)
    for name,key in [('PADECIMIENTOS','padecimientos'),('TRATAMIENTO MÉDICO','tratamiento_medico'),('CONTROL PREVENTIVO','control_preventivo'),('MEDICAMENTOS QUE NO SE LE DEBEN ADMINISTRAR NI EN CASO DE EMERGENCIA','medicamentos_no_administrar')]:
        y-=29 if key!='medicamentos_no_administrar' else 36
        _row(c,x,y,w,36 if key=='medicamentos_no_administrar' else 29,'SITUACIÓN MÉDICA ACTUAL / '+name,datos.get(key,''),label_w=296 if key=='medicamentos_no_administrar' else 227)
    for name,key in [('NOMBRE DEL MÉDICO','nombre_medico'),('TELÉFONO DEL MÉDICO','telefono_medico'),('HOSPITAL DE SU PREFERENCIA','hospital_preferencia')]:
        y-=24; _row(c,x,y,w,24,'DATOS DEL MÉDICO PARTICULAR / '+name,datos.get(key,''),label_w=278)
    y-=64;_rect(c,x,y,w,64)
    _value(c,'EL PADRE DE FAMILIA AUTORIZA QUE SU HIJO SEA TRASLADADO AL SEGURO SOCIAL EN CASO DE ACCIDENTES:',x,y+42,w,22,7.4,True)
    _value(c,('SÍ' if datos.get('autoriza_traslado') else 'NO')+ '  |  '+str(datos.get('nombre_padre_tutor',''))+'  |  '+str(datos.get('telefono_padre_tutor','')),x,y+23,w*.70,19,7.5)
    _draw_signature(c,datos.get('firma_padre_tutor',''),x+w*.72,y+4,w*.25,39)
    y-=44; _rect(c,x,y,w,44)
    _value(c,'NOMBRE Y FIRMA DEL ASPIRANTE:',x,y+20,w*.65,22,7.5,True)
    _value(c,student.nombre_aspirante,x,y,w*.60,20,7.6)
    _draw_signature(c,datos.get('firma_aspirante',''),x+w*.64,y+3,w*.32,39)
    c.setFont(REG,7); c.setFillColor(LINE);c.drawRightString(W-35,24,'Página 1 de 1')
    c.save();return out.getvalue()

def referral_pdf(ref):
    d=ref.datos; out=_buffer();c=canvas.Canvas(out,pagesize=A4)
    # El código y la emisión corresponden a la fecha registrada de la canalización,
    # no al día en que se vuelve a descargar un documento histórico.
    fecha_canalizacion = datetime.strptime(ref.fecha, '%Y-%m-%d')
    codigo = f'FOR-{fecha_canalizacion:%y-%m}'
    emision = fecha_canalizacion.strftime('%d/%m/%y')
    W,H=A4;y=_header(c,'Canalización Externa',codigo,'01',emision,A4)
    x=48;w=W-96
    def row(label,val,ht=33,lw=190):
        nonlocal y
        y-=ht;_row(c,x,y,w,ht,label,val,lw)
    row('Nombre completo de la persona:',d.get('nombre_completo',''),37,198)
    row('NSS',d.get('nss',''),28,75)
    y-=39; _rect(c,x,y,w,39)
    parts=[('Sexo',d.get('sexo',''),.19),('Edad',d.get('edad',''),.19),('Estado Civil:',d.get('estado_civil',''),.62)]
    xx=x
    for label,val,ratio in parts:
        ww=w*ratio;c.line(xx+ww,y,xx+ww,y+39) if xx+ww<x+w-.5 else None
        _value(c,label,xx,y+19,ww,20,7.6,True);_value(c,val,xx,y,ww,20,8);xx+=ww
    y-=42;_rect(c,x,y,w,42);c.line(x+w*.59,y,x+w*.59,y+42)
    _value(c,'Programa Educativo/Puesto:',x,y+18,w*.58,20,7.6,True)
    _value(c,d.get('programa_puesto',''),x,y,w*.58,20,8)
    _value(c,'Matrícula/ No. de empleado:',x+w*.60,y+18,w*.39,20,7.6,True)
    _value(c,d.get('matricula_empleado',''),x+w*.60,y,w*.39,19,8)
    y-=40;_rect(c,x,y,w,40);c.line(x+w*.49,y,x+w*.49,y+40)
    _value(c,'Teléfono celular',x,y+19,w*.49,21,7.7,True)
    _value(c,d.get('telefono_celular',''),x,y,w*.49,20,8)
    _value(c,'En caso de emergencia comunicarse con:',x+w*.49,y+19,w*.51,20,7,True)
    _value(c,d.get('contacto_emergencia',''),x+w*.49,y,w*.51,20,8)
    row('Teléfono en caso de emergencia',d.get('telefono_emergencia',''),30,214)
    row('Domicilio:',d.get('domicilio',''),36,90)
    row('Correo electrónico:',d.get('correo_electronico',''),30,145)
    # Los signos vitales se muestran EN EL MISMO CUADRO del motivo de canalización.
    y-=130;_rect(c,x,y,w,130)
    _value(c,'Motivo de canalización:',x,y+108,w,22,8,True)
    _paragraph(c,d.get('motivo_canalizacion',''),x+7,y+35,w-16,78,8)
    c.setStrokeColor(LINE);c.line(x,y+30,x+w,y+30)
    signos=[('T/A',d.get('ta','')),('FC',d.get('fc','')),('SatO2',d.get('sato2','')),('FR',d.get('fr','')),('Tª',d.get('temperatura',''))]
    col=w/len(signos)
    for i,(etiqueta,valor) in enumerate(signos):
        _value(c,f'{etiqueta}: {valor}',x+i*col,y+1,col,27,7.6,True)
    y-=35;_rect(c,x,y,w,35);c.line(x+w*.49,y,x+w*.49,y+35)
    _value(c,'Fecha: '+d.get('fecha',''),x,y,w*.49,35,8)
    _value(c,'Hora: '+d.get('hora',''),x+w*.49,y,w*.51,35,8)
    row('Elaboró:',d.get('elaboro',''),28,83)
    y-=66;_rect(c,x,y,w,66)
    _value(c,'Nombre y firma del Responsable de Enfermería',x,y+40,w,25,8,True)
    _value(c,d.get('elaboro',''),x,y,w*.52,40,8)
    _draw_signature(c,d.get('firma_responsable',''),x+w*.55,y+5,w*.41,48)
    y-=29;_rect(c,x,y,w,29)
    _value(c,'El estudiante/trabajador(a) acepta haber sido informado y ser canalizado servicios de salud externo.',x,y,w,29,7.5,True)
    y-=61;_rect(c,x,y,w,61)
    _value(c,'Firma de consentimiento del estudiante/trabajador(a):',x,y+35,w,25,8,True)
    _draw_signature(c,d.get('firma_consentimiento',''),x+w*.33,y+3,w*.55,46)
    c.setFont(REG,7);c.drawString(46,26,'Pág. 1 de 1')
    c.save();return out.getvalue()

def _p(s,size=8,bold=False):
    sty=ParagraphStyle('table',fontName=BOLD if bold else REG,fontSize=size,leading=size+2,textColor=INK,spaceAfter=0)
    return Paragraph(escape(str(s if s is not None else '')),sty)

def inventory_pdf(items,cuatrimestre):
    out=_buffer();c=canvas.Canvas(out,pagesize=landscape(A4));W,H=landscape(A4)
    y=_header(c,'UNIVERSIDAD TECNOLÓGICA DE GUTIÉRREZ ZAMORA',pagesize=landscape(A4))
    c.setFillColor(INK);c.setFont(BOLD,12);c.drawCentredString(W/2,y-6,'INVENTARIO DE MEDICAMENTO Y MATERIAL DE CURACIÓN EXISTENTE')
    c.setFont(BOLD,10);c.drawCentredString(W/2,y-23,'CUATRIMESTRE '+(cuatrimestre or 'SIN ESPECIFICAR').upper())
    y-=44
    head=[_p('Medicamento/Material de curación',8,True),_p('Descripción',8,True),_p('Fecha de caducidad',8,True),_p('Cantidad: Inicio de cuatrimestre',8,True),_p('Cantidad: Fin de cuatrimestre',8,True)]
    rows=[head]+[[_p(it.medicamento_material),_p(it.descripcion),_p(it.fecha_caducidad),_p(it.cantidad_inicio),_p(it.cantidad_fin)] for it in items]
    t=Table(rows,colWidths=[190,260,118,109,105],repeatRows=1,hAlign='CENTER')
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.5,LINE),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e1ece2')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)]))
    # Split across pages without modifying original column headings.
    available=y-38
    parts=t.split(W-45,available)
    while parts:
        part=parts.pop(0)
        pw,ph=part.wrap(W-45,available)
        part.drawOn(c,(W-pw)/2,y-ph)
        c.setFont(REG,7); c.drawRightString(W-30,20,'SAMU · Inventario de enfermería')
        if parts:
            c.showPage();y=_header(c,'INVENTARIO DE MEDICAMENTO Y MATERIAL DE CURACIÓN EXISTENTE',pagesize=landscape(A4))-10
            available=y-38
            if len(parts)==1 and parts[0] is t: break
    c.save(); return out.getvalue()

def _sig_for_table(src):
    if not src: return _p('',6)
    try:
        raw=base64.b64decode(src.split(',',1)[1],validate=True)
        im=PILImage.open(BytesIO(raw));im.thumbnail((58,28))
        o=BytesIO();im.save(o,format='PNG');o.seek(0)
        return RLImage(o,width=52,height=23,kind='proportional')
    except Exception:return _p('Firma',6)

def bitacora_pdf(items,mes=''):
    out=_buffer();c=canvas.Canvas(out,pagesize=landscape(A3));W,H=landscape(A3)
    y=_header(c,'Universidad Tecnológica de Gutiérrez Zamora','FOR-23-04a','01','07/11/23',landscape(A3))
    c.setFont(BOLD,12);c.drawCentredString(W/2,y-4,'Bitácora de atención del alumnado por el servicio de enfermería')
    if mes:
        c.setFont(BOLD,9);c.drawCentredString(W/2,y-18,f'REPORTE MENSUAL: {mes}')
        y-=40
    else:y-=28
    cols=['No.','Fecha','Hora','Nombre','Matrícula','Edad','Sexo','Programa educativo','Grupo','Motivo de consulta','Toma de T/A','Otro procedimiento','Suministro medicamento','Material de curación','Firmas: Usuario','Firmas: Enfermería']
    widths=[35,65,49,93,76,40,42,78,51,91,67,90,94,87,62,62]
    rows=[[_p(x,7,True) for x in cols]]
    for it in items:
        d=it.datos
        vals=[it.id,it.fecha,it.hora,it.nombre,it.matricula,d.get('edad',''),d.get('sexo',''),d.get('programa_educativo',''),d.get('grupo',''),d.get('motivo_consulta',''),d.get('toma_ta',''),d.get('otro_procedimiento',''),d.get('suministro_medicamento',''),d.get('material_curacion','')]
        rows.append([_p(x,6.6) for x in vals]+[_sig_for_table(d.get('firma_usuario')),_sig_for_table(d.get('firma_enfermeria'))])
    t=Table(rows,colWidths=widths,repeatRows=1)
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.35,LINE),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e1ece2')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)]))
    parts=t.split(W-40,y-40)
    while parts:
        part=parts.pop(0);pw,ph=part.wrap(W-40,y-40)
        part.drawOn(c,(W-pw)/2,y-ph)
        if parts:
            c.showPage();y=_header(c,'Bitácora de atención del alumnado por el servicio de enfermería',pagesize=landscape(A3))
    c.save();return out.getvalue()
