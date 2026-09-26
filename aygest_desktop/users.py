from __future__ import annotations
import hashlib, os, uuid

ROLES={'owner':{'label':'Administrador','permissions':{'*'}},'manager':{'label':'Gestor','permissions':{'dashboard','sales','invoices','products','stock','reservations','quotations','customers','suppliers','purchases','finance','reports'}},'cashier':{'label':'Caixa','permissions':{'dashboard','sales','invoices','customers'}},'stock':{'label':'Stock','permissions':{'dashboard','products','stock','purchases','suppliers'}}}

def hash_password(password,salt=None):
    if not isinstance(password,str) or len(password)<6: raise ValueError('A palavra-passe deve ter pelo menos 6 caracteres.')
    salt=salt or os.urandom(16).hex();digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),120000).hex();return salt+'$'+digest

def verify_password(password,stored):
    try:
        salt,digest=stored.split('$',1);return hash_password(password,salt).split('$',1)[1]==digest
    except (ValueError,AttributeError): return False

class UserService:
    def __init__(self,conn): self.conn=conn
    def create(self,tenant_id,name,email,password,role='cashier'):
        if role not in ROLES: raise ValueError('Perfil inválido.')
        uid=str(uuid.uuid4());self.conn.execute('INSERT INTO users(id,tenant_id,name,email,role,active,password_hash) VALUES(?,?,?,?,?,1,?)',(uid,tenant_id,name,email.lower().strip() if email else None,role,hash_password(password)));return uid
    def authenticate(self,tenant_id,email,password):
        row=self.conn.execute('SELECT * FROM users WHERE tenant_id=? AND lower(email)=lower(?) AND active=1',(tenant_id,email.strip())).fetchone()
        return row if row and row['password_hash'] and verify_password(password,row['password_hash']) else None
    def set_password(self,user_id,password): self.conn.execute('UPDATE users SET password_hash=? WHERE id=?',(hash_password(password),user_id))
    def set_role(self,user_id,role):
        if role not in ROLES: raise ValueError('Perfil inválido.')
        self.conn.execute('UPDATE users SET role=? WHERE id=?',(role,user_id))
    def set_active(self,user_id,active): self.conn.execute('UPDATE users SET active=? WHERE id=?',(1 if active else 0,user_id))
    def can(self,user,permission): return user and ('*' in ROLES.get(user['role'],{}).get('permissions',set()) or permission in ROLES.get(user['role'],{}).get('permissions',set()))
