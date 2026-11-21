"""Inicialización segura de la primera cuenta de enfermería."""
import argparse, getpass
from sqlalchemy import select
from .db import init_db, SessionLocal, Nurse
from .auth import hash_password

def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['create-admin'])
    p.add_argument('--email',required=True)
    p.add_argument('--name',default='Responsable de enfermería')
    a=p.parse_args()
    password=getpass.getpass('Contraseña segura (mínimo 12 caracteres): ')
    if len(password)<12: raise SystemExit('Se requieren al menos 12 caracteres.')
    init_db()
    with SessionLocal.begin() as db:
        if db.scalar(select(Nurse).where(Nurse.email==a.email.strip().lower())):
            raise SystemExit('Este correo ya existe; no se sobrescribió.')
        db.add(Nurse(name=a.name,email=a.email.strip().lower(),password_hash=hash_password.hash(password),role='admin'))
    print('Cuenta administrativa creada. Usa /login para ingresar.')
if __name__=='__main__': main()
