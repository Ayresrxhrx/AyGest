from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from tkinter import messagebox

import customtkinter as ctk

from .config import APP_NAME, DB_PATH
from .products_ui import ProductsFrame
from .security import generate_activation_key


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path=DB_PATH):
        self.conn=sqlite3.connect(path,timeout=20,isolation_level=None); self.conn.row_factory=sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL"); self.conn.execute("PRAGMA foreign_keys=ON"); self.migrate()

    def migrate(self):
        self.conn.executescript('''
        CREATE TABLE IF NOT EXISTS tenants(id TEXT PRIMARY KEY,name TEXT NOT NULL,nuit TEXT,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS licenses(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,license_key TEXT UNIQUE NOT NULL,plan TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'active',expires_at TEXT,FOREIGN KEY(tenant_id) REFERENCES tenants(id));
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,name TEXT NOT NULL,email TEXT UNIQUE,role TEXT NOT NULL DEFAULT 'cashier',active INTEGER NOT NULL DEFAULT 1,FOREIGN KEY(tenant_id) REFERENCES tenants(id));
        CREATE TABLE IF NOT EXISTS products(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,sku TEXT NOT NULL,barcode TEXT,name TEXT NOT NULL,category TEXT,unit TEXT NOT NULL DEFAULT 'UN',base_factor REAL NOT NULL DEFAULT 1,purchase_price REAL NOT NULL DEFAULT 0,sale_price REAL NOT NULL DEFAULT 0,vat_rate REAL NOT NULL DEFAULT 16,min_stock REAL NOT NULL DEFAULT 0,active INTEGER NOT NULL DEFAULT 1,UNIQUE(tenant_id,sku),FOREIGN KEY(tenant_id) REFERENCES tenants(id));
        CREATE TABLE IF NOT EXISTS stock(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,product_id TEXT NOT NULL,warehouse TEXT NOT NULL DEFAULT 'Principal',quantity REAL NOT NULL DEFAULT 0,reserved REAL NOT NULL DEFAULT 0,updated_at TEXT NOT NULL,UNIQUE(tenant_id,product_id,warehouse),FOREIGN KEY(product_id) REFERENCES products(id));
        CREATE TABLE IF NOT EXISTS reservations(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,product_id TEXT NOT NULL,quantity REAL NOT NULL,cashier_id TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'active',expires_at TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(product_id) REFERENCES products(id));
        CREATE TABLE IF NOT EXISTS customers(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,name TEXT NOT NULL,nuit TEXT,phone TEXT,email TEXT);
        CREATE TABLE IF NOT EXISTS sales(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,customer_id TEXT,document_no TEXT NOT NULL,total REAL NOT NULL,vat REAL NOT NULL,payment_method TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'completed',created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS quotations(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,customer_id TEXT,document_no TEXT NOT NULL,total REAL NOT NULL,expires_at TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'open',created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS cash_sessions(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,user_id TEXT NOT NULL,opening_amount REAL NOT NULL,closing_amount REAL,opened_at TEXT NOT NULL,closed_at TEXT);
        CREATE TABLE IF NOT EXISTS audit_log(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,user_id TEXT,action TEXT NOT NULL,details TEXT,created_at TEXT NOT NULL);
        ''')

    def bootstrap(self):
        row=self.conn.execute("SELECT id FROM tenants LIMIT 1").fetchone()
        if row: return row["id"]
        tenant_id=str(uuid.uuid4()); self.conn.execute("INSERT INTO tenants VALUES(?,?,?,?)",(tenant_id,"Minha Empresa","",utc_now()))
        self.conn.execute("INSERT INTO licenses VALUES(?,?,?,?,?,?)",(str(uuid.uuid4()),tenant_id,generate_activation_key(),"Professional","active",(datetime.now(timezone.utc)+timedelta(days=365)).isoformat()))
        self.conn.execute("INSERT INTO users VALUES(?,?,?,?,?,?)",(str(uuid.uuid4()),tenant_id,"Administrador","admin@local","owner",1))
        return tenant_id


class App(ctk.CTk):
    def __init__(self):
        super().__init__(); self.title(APP_NAME); self.geometry("1440x900"); self.minsize(1180,760)
        ctk.set_appearance_mode("light"); ctk.set_default_color_theme("blue")
        self.db=Database(); self.tenant_id=self.db.bootstrap(); self._build_shell()

    def _build_shell(self):
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        sidebar=ctk.CTkFrame(self,width=250,corner_radius=0,fg_color="#0B2239"); sidebar.grid(row=0,column=0,sticky="nsew"); sidebar.grid_propagate(False)
        ctk.CTkLabel(sidebar,text="AyGest",font=ctk.CTkFont(size=28,weight="bold"),text_color="white").pack(padx=24,pady=(30,3),anchor="w")
        ctk.CTkLabel(sidebar,text="BUSINESS MANAGEMENT",font=ctk.CTkFont(size=10,weight="bold"),text_color="#AFC4D8").pack(padx=26,pady=(0,25),anchor="w")
        for module in ["Dashboard","POS / Vendas","Facturação","Produtos","Stock","Reservas","Cotações","Clientes","Fornecedores","Compras","Financeiro","Relatórios","Utilizadores","Licenciamento","Configurações"]:
            ctk.CTkButton(sidebar,text=module,anchor="w",height=40,corner_radius=8,fg_color="transparent",hover_color="#173D60",text_color="#EAF2F8",command=lambda m=module:self.open_module(m)).pack(fill="x",padx=12,pady=2)
        ctk.CTkLabel(sidebar,text="ONLINE · MULTI-TENANT",text_color="#7FD6A8",font=ctk.CTkFont(size=10,weight="bold")).pack(side="bottom",padx=20,pady=24,anchor="w")
        self.content=ctk.CTkFrame(self,fg_color="#F5F7FA",corner_radius=0); self.content.grid(row=0,column=1,sticky="nsew"); self.open_module("Dashboard")

    def clear(self):
        for child in self.content.winfo_children(): child.destroy()

    def open_module(self,module):
        self.clear()
        if module=="Dashboard": return self.dashboard()
        if module in ("Produtos","Stock"): return ProductsFrame(self.content,self.db,self.tenant_id).pack(fill="both",expand=True)
        if module=="Licenciamento": return self.licensing()
        ctk.CTkLabel(self.content,text=module,font=ctk.CTkFont(size=30,weight="bold"),text_color="#102A43").pack(padx=40,pady=(35,5),anchor="w")
        ctk.CTkLabel(self.content,text="Este módulo será implementado na fase correspondente.",text_color="#627D98").pack(padx=40,anchor="w")

    def dashboard(self):
        ctk.CTkLabel(self.content,text="Dashboard",font=ctk.CTkFont(size=30,weight="bold"),text_color="#102A43").pack(padx=40,pady=(35,4),anchor="w")
        ctk.CTkLabel(self.content,text="Visão geral do negócio",text_color="#627D98").pack(padx=40,anchor="w")
        grid=ctk.CTkFrame(self.content,fg_color="transparent"); grid.pack(fill="x",padx=40,pady=30)
        for i,(name,value) in enumerate([("Vendas hoje","0,00 MT"),("Stock disponível","0"),("Reservas activas","0"),("Cotações abertas","0")]):
            grid.grid_columnconfigure(i,weight=1); card=ctk.CTkFrame(grid,fg_color="white",corner_radius=14,border_width=1,border_color="#E1E8EF"); card.grid(row=0,column=i,padx=6,sticky="nsew")
            ctk.CTkLabel(card,text=name,text_color="#627D98",font=ctk.CTkFont(size=12,weight="bold")).pack(padx=20,pady=(20,6),anchor="w"); ctk.CTkLabel(card,text=value,text_color="#102A43",font=ctk.CTkFont(size=24,weight="bold")).pack(padx=20,pady=(0,20),anchor="w")

    def licensing(self):
        ctk.CTkLabel(self.content,text="Licenciamento",font=ctk.CTkFont(size=30,weight="bold"),text_color="#102A43").pack(padx=40,pady=(35,5),anchor="w")
        row=ctk.CTkFrame(self.content,fg_color="white",corner_radius=14); row.pack(fill="x",padx=40,pady=25)
        r=self.db.conn.execute("SELECT license_key,plan,status,expires_at FROM licenses WHERE tenant_id=? LIMIT 1",(self.tenant_id,)).fetchone(); text=f"Plano: {r['plan']}\nEstado: {r['status']}\nExpira: {r['expires_at']}\nKey: {r['license_key']}"
        ctk.CTkLabel(row,text=text,justify="left",font=ctk.CTkFont(size=15),text_color="#102A43").pack(padx=25,pady=25,anchor="w")
        ctk.CTkButton(row,text="Verificar licença",command=lambda:messagebox.showinfo("AyGest","A licença será validada pelo servidor quando a API cloud estiver configurada.")).pack(padx=25,pady=(0,25),anchor="w")


if __name__=="__main__": App().mainloop()
