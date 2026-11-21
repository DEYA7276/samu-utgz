"""Envíos reales exclusivamente mediante SMTP configurado; sin simulaciones de éxito."""
import os, ssl, smtplib
from email.message import EmailMessage

def has_smtp():
    return bool(os.getenv('SMTP_HOST') and os.getenv('SMTP_FROM'))

def send_mail(to,subject,body,pdf=None,pdf_name='canalizacion.pdf'):
    if not has_smtp(): raise RuntimeError('SMTP_NO_CONFIGURADO')
    msg=EmailMessage()
    msg['From']=os.environ['SMTP_FROM']
    msg['To']=to
    msg['Subject']=subject
    msg.set_content(body)
    if pdf is not None:
        msg.add_attachment(pdf,maintype='application',subtype='pdf',filename=pdf_name)
    host=os.environ['SMTP_HOST']
    port=int(os.getenv('SMTP_PORT','587'))
    tls=os.getenv('SMTP_TLS','starttls').lower()
    context=ssl.create_default_context()
    if tls=='ssl': server=smtplib.SMTP_SSL(host,port,context=context,timeout=15)
    else: server=smtplib.SMTP(host,port,timeout=15)
    try:
        if tls=='starttls': server.starttls(context=context)
        username=os.getenv('SMTP_USER','')
        if username: server.login(username,os.getenv('SMTP_PASSWORD',''))
        server.send_message(msg)
    finally: server.quit()
