from __future__ import annotations
import sqlite3, uuid
from datetime import datetime, timedelta, timezone
from tkinter import messagebox, simpledialog
import customtkinter as ctk
from .config import APP_NAME, DB_PATH
from .products_ui import ProductsFrame
from .pos_ui import POSFrame
from .reservations_ui import ReservationsFrame, QuotationsFrame
from .invoicing import InvoiceService
from .security import generate_activation_key
from .finance import CashService, FinanceService

def utc_now(): return datetime.now(timezone.utc).isoformat()
class Database:
    def __init__(self,path=DB_PATH):
        self.conn=sqlite3.connect(path,timeout=20,isolation_level=None);self.conn.row_factory=sqlite3.Row;self.conn.execute('PRAGMA journal_mode=WAL');self.conn.execute('PRAGMA foreign_keys=ON');self.migrate()
    def migrate(self):
        self.conn.executescript('''CREATE TABLE IF NOT EXISTS tenants(id TEXT PRIMARY KEY,name TEXT NOT NULL,nuit TEXT,created_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS licenses(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,license_key TEXT UNIQUE NOT NULL,plan TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'active',expires_at TEXT,FOREIGN KEY(tenant_id) REFERENCES tenants(id));CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,name TEXT NOT NULL,email TEXT UNIQUE,role TEXT NOT NULL DEFAULT 'cashier',active INTEGER NOT NULL DEFAULT 1,FOREIGN KEY(tenant_id) REFERENCES tenants(id));CREATE TABLE IF NOT EXISTS products(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,sku TEXT NOT NULL,barcode TEXT,name TEXT NOT NULL,category TEXT,unit TEXT NOT NULL DEFAULT 'UN',base_factor REAL NOT NULL DEFAULT 1,purchase_price REAL NOT NULL DEFAULT 0,sale_price REAL NOT NULL DEFAULT 0,vat_rate REAL NOT NULL DEFAULT 16,min_stock REAL NOT NULL DEFAULT 0,active INTEGER NOT NULL DEFAULT 1,UNIQUE(tenant_id,sku));CREATE TABLE IF NOT EXISTS stock(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,product_id TEXT NOT NULL,warehouse TEXT NOT NULL DEFAULT 'Principal',quantity REAL NOT NULL DEFAULT 0,reserved REAL NOT NULL DEFAULT 0,updated_at TEXT NOT NULL,UNIQUE(tenant_id,product_id,warehouse));CREATE TABLE IF NOT EXISTS reservations(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,product_id TEXT NOT NULL,quantity REAL NOT NULL,cashier_id TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'active',expires_at TEXT NOT NULL,created_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS customers(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,name TEXT NOT NULL,nuit TEXT,phone TEXT,email TEXT);CREATE TABLE IF NOT EXISTS suppliers(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,name TEXT NOT NULL,nuit TEXT,phone TEXT,email TEXT,address TEXT);CREATE TABLE IF NOT EXISTS purchases(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,document_no TEXT NOT NULL,supplier_id TEXT,total REAL NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'draft',created_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS purchase_items(id TEXT PRIMARY KEY,purchase_id TEXT NOT NULL,product_id TEXT NOT NULL,quantity REAL NOT NULL,unit_cost REAL NOT NULL,line_total REAL NOT NULL);CREATE TABLE IF NOT EXISTS sales(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,customer_id TEXT,total REAL NOT NULL,vat REAL NOT NULL,payment_method TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'completed',document_no TEXT NOT NULL,created_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS quotations(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,customer_id TEXT,total REAL NOT NULL,document_no TEXT NOT NULL,expires_at TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'open',created_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS cash_sessions(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,user_id TEXT NOT NULL,opening_amount REAL NOT NULL,closing_amount REAL,opened_at TEXT NOT NULL,closed_at TEXT);CREATE TABLE IF NOT EXISTS audit_log(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,user_id TEXT,action TEXT NOT NULL,details TEXT,created_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS sale_items(id TEXT PRIMARY KEY,sale_id TEXT NOT NULL,product_id TEXT NOT NULL,quantity REAL NOT NULL,unit_price REAL NOT NULL,line_total REAL NOT NULL,vat_rate REAL NOT NULL);CREATE TABLE IF NOT EXISTS finance_movements(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,user_id TEXT,kind TEXT NOT NULL,description TEXT NOT NULL,amount REAL NOT NULL,payment_method TEXT NOT NULL,created_at TEXT NOT NULL);''')
    def bootstrap(self):
        r=self.conn.execute('SELECT id FROM tenants LIMIT 1').fetchone()
        if r:return r['id']
        tid=str(uuid.uuid4());self.conn.execute('INSERT INTO tenants VALUES(?,?,?,?)',(tid,'Minha Empresa','',utc_now()));self.conn.execute('INSERT INTO licenses VALUES(?,?,?,?,?,?)',(str(uuid.uuid4()),tid,generate_activation_key(),'Professional','active',(datetime.now(timezone.utc)+timedelta(days=365)).isoformat()));self.conn.execute('INSERT INTO users VALUES(?,?,?,?,?,?)',(str(uuid.uuid4()),tid,'Administrador','admin@local','owner',1));return tid
class App(ctk.CTk):
    def __init__(self):
        super().__init__();self.title(APP_NAME);self.geometry('1440x900');self.minsize(1180,760);ctk.set_appearance_mode('light');ctk.set_default_color_theme('blue');self.db=Database();self.tenant_id=self.db.bootstrap();self.user_id=self.db.conn.execute('SELECT id FROM users WHERE tenant_id=? LIMIT 1',(self.tenant_id,)).fetchone()['id'];self._shell()
    def _shell(self):
        self.grid_columnconfigure(1,weight=1);self.grid_rowconfigure(0,weight=1);s=ctk.CTkFrame(self,width=250,corner_radius=0,fg_color='#0B2239');s.grid(row=0,column=0,sticky='nsew');s.grid_propagate(False);ctk.CTkLabel(s,text='AyGest',font=ctk.CTkFont(size=28,weight='bold'),text_color='white').pack(padx=24,pady=(30,3),anchor='w');ctk.CTkLabel(s,text='BUSINESS MANAGEMENT',font=ctk.CTkFont(size=10,weight='bold'),text_color='#AFC4D8').pack(padx=26,pady=(0,25),anchor='w')
        for m in ['Dashboard','POS / Vendas','Facturação','Produtos','Stock','Reservas','Cotações','Clientes','Fornecedores','Compras','Financeiro','Relatórios','Utilizadores','Licenciamento','Configurações']:ctk.CTkButton(s,text=m,anchor='w',height=40,corner_radius=8,fg_color='transparent',hover_color='#173D60',text_color='#EAF2F8',command=lambda x=m:self.open(x)).pack(fill='x',padx=12,pady=2)
        self.content=ctk.CTkFrame(self,fg_color='#F5F7FA',corner_radius=0);self.content.grid(row=0,column=1,sticky='nsew');self.open('Dashboard')
    def clear(self):
        for w in self.content.winfo_children():w.destroy()
    def open(self,m):
        self.clear()
        if m=='POS / Vendas':return POSFrame(self.content,self.db,self.tenant_id,self.user_id).pack(fill='both',expand=True)
        if m in ('Produtos','Stock'):return ProductsFrame(self.content,self.db,self.tenant_id).pack(fill='both',expand=True)
        if m=='Reservas':return ReservationsFrame(self.content,self.db,self.tenant_id,self.user_id).pack(fill='both',expand=True)
        if m=='Cotações':return QuotationsFrame(self.content,self.db,self.tenant_id).pack(fill='both',expand=True)
        if m=='Facturação':return self.invoices()
        if m in ('Clientes','Fornecedores'):return self.contacts(m)
        if m=='Compras':return self.purchases()
        if m=='Financeiro':return self.finance()
        if m=='Licenciamento':return self.license()
        ctk.CTkLabel(self.content,text=m,font=ctk.CTkFont(size=30,weight='bold'),text_color='#102A43').pack(padx=40,pady=(35,5),anchor='w');ctk.CTkLabel(self.content,text='Módulo preparado para a fase seguinte.',text_color='#627D98').pack(padx=40,anchor='w')
    def finance(self):
        ctk.CTkLabel(self.content,text='Financeiro & Caixa',font=ctk.CTkFont(size=30,weight='bold'),text_color='#102A43').pack(anchor='w',padx=40,pady=(35,5));body=ctk.CTkFrame(self.content,fg_color='white',corner_radius=14);body.pack(fill='x',padx=40,pady=20);cash=CashService(self.db.conn);active=cash.active(self.tenant_id,self.user_id)
        status='CAIXA ABERTO' if active else 'CAIXA FECHADO';ctk.CTkLabel(body,text=status,font=ctk.CTkFont(size=18,weight='bold')).pack(anchor='w',padx=25,pady=(22,5));info=ctk.CTkLabel(body,text='',text_color='#627D98');info.pack(anchor='w',padx=25,pady=5)
        def refresh():
            nonlocal active;active=cash.active(self.tenant_id,self.user_id)
            if active:
                sm=cash.summary(self.tenant_id,active['id']);info.configure(text=f"Abertura: {sm['opening']:.2f} MT   |   Vendas: {sm['sales']:.2f} MT   |   Esperado: {sm['expected']:.2f} MT")
            else:info.configure(text='Nenhuma sessão de caixa aberta.')
        def toggle():
            nonlocal active
            try:
                if active:
                    val=simpledialog.askfloat('Fechar caixa','Valor contado no caixa:',parent=self)
                    if val is not None:cash.close_session(active['id'],val);refresh()
                else:
                    val=simpledialog.askfloat('Abrir caixa','Fundo inicial (MT):',parent=self,initialvalue=0)
                    if val is not None:cash.open_session(self.tenant_id,self.user_id,val);refresh()
            except Exception as e:messagebox.showerror('Caixa',str(e),parent=self)
        ctk.CTkButton(body,text='Abrir / Fechar Caixa',command=toggle).pack(anchor='w',padx=25,pady=(10,25));refresh()
        ctk.CTkLabel(self.content,text='Movimentos recentes',font=ctk.CTkFont(size=20,weight='bold'),text_color='#102A43').pack(anchor='w',padx=40,pady=(15,5));box=ctk.CTkScrollableFrame(self.content,fg_color='white');box.pack(fill='both',expand=True,padx=40,pady=(0,25))
        for r in self.db.conn.execute('SELECT * FROM finance_movements WHERE tenant_id=? ORDER BY created_at DESC LIMIT 100',(self.tenant_id,)).fetchall():
            c=ctk.CTkFrame(box,fg_color='#F8FAFC',corner_radius=10);c.pack(fill='x',pady=4,padx=5);ctk.CTkLabel(c,text=r['description'],font=ctk.CTkFont(weight='bold')).pack(side='left',padx=15,pady=12);ctk.CTkLabel(c,text=f"{r['kind']} · {r['amount']:.2f} MT · {r['payment_method']}",text_color='#627D98').pack(side='left')
    def contacts(self,m):
        table='customers' if m=='Clientes' else 'suppliers';ctk.CTkLabel(self.content,text=m,font=ctk.CTkFont(size=30,weight='bold'),text_color='#102A43').pack(anchor='w',padx=40,pady=(35,4));box=ctk.CTkScrollableFrame(self.content,fg_color='white');box.pack(fill='both',expand=True,padx=40,pady=20)
        for r in self.db.conn.execute(f'SELECT * FROM {table} WHERE tenant_id=? ORDER BY name',(self.tenant_id,)).fetchall():
            c=ctk.CTkFrame(box,fg_color='#F8FAFC',corner_radius=10);c.pack(fill='x',pady=5,padx=5);ctk.CTkLabel(c,text=r['name'],font=ctk.CTkFont(weight='bold'),text_color='#102A43').pack(side='left',padx=15,pady=14);ctk.CTkLabel(c,text=f"{r['phone'] or ''} · {r['email'] or ''}",text_color='#627D98').pack(side='left')
    def purchases(self):
        ctk.CTkLabel(self.content,text='Compras',font=ctk.CTkFont(size=30,weight='bold'),text_color='#102A43').pack(anchor='w',padx=40,pady=(35,4));box=ctk.CTkScrollableFrame(self.content,fg_color='white');box.pack(fill='both',expand=True,padx=40,pady=20)
        for r in self.db.conn.execute("SELECT p.*,s.name supplier FROM purchases p LEFT JOIN suppliers s ON s.id=p.supplier_id WHERE p.tenant_id=? ORDER BY p.created_at DESC",(self.tenant_id,)).fetchall():
            c=ctk.CTkFrame(box,fg_color='#F8FAFC',corner_radius=10);c.pack(fill='x',pady=5,padx=5);ctk.CTkLabel(c,text=r['document_no'],font=ctk.CTkFont(weight='bold'),text_color='#102A43').pack(side='left',padx=15,pady=14);ctk.CTkLabel(c,text=f"{r['supplier'] or 'Sem fornecedor'} · {r['total']:.2f} MT · {r['status']}",text_color='#627D98').pack(side='left')
    def invoices(self):
        ctk.CTkLabel(self.content,text='Facturação',font=ctk.CTkFont(size=30,weight='bold'),text_color='#102A43').pack(padx=40,pady=(35,5),anchor='w');box=ctk.CTkScrollableFrame(self.content,fg_color='white');box.pack(fill='both',expand=True,padx=40,pady=25)
        for r in self.db.conn.execute("SELECT id,document_no,total,vat,payment_method,created_at FROM sales WHERE tenant_id=? ORDER BY created_at DESC",(self.tenant_id,)).fetchall():
            card=ctk.CTkFrame(box,fg_color='#F8FAFC',corner_radius=10);card.pack(fill='x',pady=5,padx=5);ctk.CTkLabel(card,text=r['document_no'],font=ctk.CTkFont(weight='bold'),text_color='#102A43').pack(side='left',padx=15,pady=14);ctk.CTkLabel(card,text=f"{r['total']:.2f} MT · {r['payment_method']}",text_color='#627D98').pack(side='left');ctk.CTkButton(card,text='PDF A4',width=85,command=lambda x=r['id']:self.export_invoice(x,False)).pack(side='right',padx=5);ctk.CTkButton(card,text='POS',width=70,command=lambda x=r['id']:self.export_invoice(x,True)).pack(side='right',padx=5)
    def export_invoice(self,sale_id,thermal):
        try:messagebox.showinfo('Documento criado',InvoiceService(self.db.conn).pdf(self.tenant_id,sale_id,thermal))
        except Exception as e:messagebox.showerror('Exportação',str(e))
    def license(self):
        ctk.CTkLabel(self.content,text='Licenciamento',font=ctk.CTkFont(size=30,weight='bold'),text_color='#102A43').pack(padx=40,pady=35,anchor='w');r=self.db.conn.execute('SELECT * FROM licenses WHERE tenant_id=? LIMIT 1',(self.tenant_id,)).fetchone();ctk.CTkLabel(self.content,text=f"Plano: {r['plan']}\nEstado: {r['status']}\nExpira: {r['expires_at']}\nKey: {r['license_key']}",justify='left',font=ctk.CTkFont(size=15),text_color='#102A43').pack(padx=40,anchor='w')
if __name__=='__main__':App().mainloop()
