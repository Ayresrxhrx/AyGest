from __future__ import annotations
import customtkinter as ctk
from tkinter import messagebox
from .users import UserService

class LoginWindow(ctk.CTkToplevel):
    def __init__(self,parent,db,tenant_id,on_success):
        super().__init__(parent);self.db=db;self.tenant_id=tenant_id;self.on_success=on_success;self.service=UserService(db.conn);self.title('AyGest — Entrar');self.geometry('460x560');self.resizable(False,False);self.protocol('WM_DELETE_WINDOW',self.cancel);self.grab_set();self.build();self.after(100,self.focus_force)
    def build(self):
        ctk.CTkLabel(self,text='AyGest',font=ctk.CTkFont(size=38,weight='bold'),text_color='#102A43').pack(pady=(55,5));ctk.CTkLabel(self,text='Gestão empresarial',text_color='#627D98').pack(pady=(0,35))
        self.email=ctk.CTkEntry(self,placeholder_text='E-mail',height=44);self.email.pack(fill='x',padx=55,pady=8)
        self.password=ctk.CTkEntry(self,placeholder_text='Palavra-passe',show='•',height=44);self.password.pack(fill='x',padx=55,pady=8);self.password.bind('<Return>',lambda _:self.login())
        first=self.db.conn.execute("SELECT id FROM users WHERE tenant_id=? AND active=1 AND password_hash IS NOT NULL AND password_hash<>'' LIMIT 1",(self.tenant_id,)).fetchone();self.first_setup=not bool(first)
        if self.first_setup:
            ctk.CTkLabel(self,text='Primeiro acesso: defina a palavra-passe do administrador.',wraplength=340,text_color='#627D98').pack(pady=(8,12));self.email.insert(0,'admin@local')
        ctk.CTkButton(self,text='Entrar' if not self.first_setup else 'Definir palavra-passe e entrar',height=44,command=self.login).pack(fill='x',padx=55,pady=18)
    def login(self):
        email=self.email.get().strip();password=self.password.get()
        try:
            if self.first_setup:
                if len(password)<6:raise ValueError('A palavra-passe deve ter pelo menos 6 caracteres.')
                user=self.db.conn.execute('SELECT id FROM users WHERE tenant_id=? AND lower(email)=lower(?) LIMIT 1',(self.tenant_id,email)).fetchone()
                if not user:raise ValueError('Administrador não encontrado.')
                self.service.set_password(user['id'],password);row=self.db.conn.execute('SELECT * FROM users WHERE id=?',(user['id'],)).fetchone()
            else:row=self.service.authenticate(self.tenant_id,email,password)
            if not row:raise ValueError('E-mail ou palavra-passe incorrectos.')
            self.grab_release();self.destroy();self.on_success(row)
        except Exception as e:messagebox.showerror('Autenticação',str(e),parent=self)
    def cancel(self):self.master.destroy()
