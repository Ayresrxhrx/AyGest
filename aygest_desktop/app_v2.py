from __future__ import annotations
from tkinter import messagebox, simpledialog
import customtkinter as ctk
from .app import App as BaseApp
from .dashboard_ui import DashboardFrame
from .backup import create_backup
from .users import UserService, ROLES
from .config import APP_NAME, settings, DB_PATH, BACKUP_DIR
from .pos_ui import POSFrame
from .products_ui import ProductsFrame
from .reservations_ui import ReservationsFrame, QuotationsFrame
from .reports_ui import ReportsFrame
from .invoicing import InvoiceService
from .finance import CashService

class App(BaseApp):
    def _shell(self):
        for w in self.winfo_children(): w.destroy()
        self.grid_columnconfigure(1,weight=1);self.grid_rowconfigure(0,weight=1)
        side=ctk.CTkFrame(self,width=250,corner_radius=0,fg_color='#0B2239');side.grid(row=0,column=0,sticky='nsew');side.grid_propagate(False)
        ctk.CTkLabel(side,text='AyGest',font=ctk.CTkFont(size=30,weight='bold'),text_color='white').pack(padx=24,pady=(28,0),anchor='w');ctk.CTkLabel(side,text='BUSINESS MANAGEMENT',font=ctk.CTkFont(size=9,weight='bold'),text_color='#6FA8DC').pack(padx=26,pady=(0,22),anchor='w');ctk.CTkLabel(side,text=f"{self.user['name']}  •  {ROLES.get(self.user['role'],{}).get('label','Utilizador')}",font=ctk.CTkFont(size=11,weight='bold'),text_color='#DCEAF7').pack(padx=24,pady=(0,16),anchor='w')
        self.nav=[]
        groups=[('PRINCIPAL',['Dashboard','POS / Vendas','Facturação']),('GESTÃO',['Produtos','Stock','Clientes','Fornecedores','Compras']),('OPERAÇÃO',['Reservas','Cotações','Financeiro','Relatórios']),('SISTEMA',['Utilizadores','Licenciamento','Configurações'])]
        for title,items in groups:
            ctk.CTkLabel(side,text=title,font=ctk.CTkFont(size=9,weight='bold'),text_color='#6D8BA5').pack(fill='x',padx=25,pady=(10,5))
            for item in items:
                b=ctk.CTkButton(side,text=item,anchor='w',height=37,corner_radius=8,fg_color='transparent',hover_color='#173D60',text_color='#EAF2F8',command=lambda x=item:self.open(x));b.pack(fill='x',padx=12,pady=1);self.nav.append((item,b))
        ctk.CTkLabel(side,text=f'Versão {settings.app_version}',text_color='#6D8BA5',font=ctk.CTkFont(size=9)).pack(side='bottom',pady=18)
        self.content=ctk.CTkFrame(self,fg_color='#F3F6FA',corner_radius=0);self.content.grid(row=0,column=1,sticky='nsew');self.open('Dashboard')
    def open(self,m):
        for w in self.content.winfo_children():w.destroy()
        mapping={'POS / Vendas':'sales','Facturação':'invoices','Produtos':'products','Stock':'stock','Reservas':'reservations','Cotações':'quotations','Clientes':'customers','Fornecedores':'suppliers','Compras':'purchases','Financeiro':'finance','Relatórios':'reports','Utilizadores':'users'}
        if m in mapping and not self.allowed(mapping[m]):return self.denied()
        if m=='Dashboard':return DashboardFrame(self.content,self.db,self.tenant_id,self.open).pack(fill='both',expand=True)
        if m=='POS / Vendas':return POSFrame(self.content,self.db,self.tenant_id,self.user_id).pack(fill='both',expand=True)
        if m in ('Produtos','Stock'):return ProductsFrame(self.content,self.db,self.tenant_id).pack(fill='both',expand=True)
        if m=='Reservas':return ReservationsFrame(self.content,self.db,self.tenant_id,self.user_id).pack(fill='both',expand=True)
        if m=='Cotações':return QuotationsFrame(self.content,self.db,self.tenant_id).pack(fill='both',expand=True)
        if m=='Relatórios':return ReportsFrame(self.content,self.db,self.tenant_id).pack(fill='both',expand=True)
        if m=='Utilizadores':return self.users_pro()
        if m=='Facturação':return self.invoices_pro()
        if m=='Clientes':return self.contacts_pro('customers','Clientes')
        if m=='Fornecedores':return self.contacts_pro('suppliers','Fornecedores')
        if m=='Compras':return self.purchases_pro()
        if m=='Financeiro':return self.finance_pro()
        if m=='Licenciamento':return self.license_pro()
        if m=='Configurações':return self.settings_pro()
    def denied(self):
        ctk.CTkLabel(self.content,text='Acesso não autorizado',font=ctk.CTkFont(size=28,weight='bold'),text_color='#102A43').pack(padx=40,pady=50,anchor='w');ctk.CTkLabel(self.content,text='O seu perfil não possui permissão para este módulo.',text_color='#627D98').pack(padx=40,anchor='w')
    def section(self,title,subtitle=''):
        h=ctk.CTkFrame(self.content,fg_color='transparent');h.pack(fill='x',padx=34,pady=(26,12));ctk.CTkLabel(h,text=title,font=ctk.CTkFont(size=28,weight='bold'),text_color='#102A43').pack(anchor='w');ctk.CTkLabel(h,text=subtitle,text_color='#627D98').pack(anchor='w',pady=(2,0))
    def users_pro(self):
        self.section('Utilizadores & permissões','Controlo de acesso por perfil, estado e palavra-passe.')
        top=ctk.CTkFrame(self.content,fg_color='white',corner_radius=14);top.pack(fill='x',padx=34,pady=(0,12));ctk.CTkButton(top,text='+ Novo utilizador',command=self.new_user).pack(side='right',padx=16,pady=14)
        box=ctk.CTkScrollableFrame(self.content,fg_color='transparent');box.pack(fill='both',expand=True,padx=34,pady=(0,28));
        for r in self.db.conn.execute('SELECT * FROM users WHERE tenant_id=? ORDER BY name',(self.tenant_id,)).fetchall():
            c=ctk.CTkFrame(box,fg_color='white',corner_radius=12);c.pack(fill='x',pady=5);ctk.CTkLabel(c,text=r['name'],font=ctk.CTkFont(size=14,weight='bold'),text_color='#102A43').pack(side='left',padx=18,pady=16);ctk.CTkLabel(c,text=f"{r['email'] or '-'}  •  {ROLES.get(r['role'],{}).get('label',r['role'])}",text_color='#627D98').pack(side='left');ctk.CTkButton(c,text='Activar' if not r['active'] else 'Desactivar',width=100,command=lambda x=r:self.toggle_user(x)).pack(side='right',padx=8);ctk.CTkButton(c,text='Password',width=90,fg_color='#E8EEF7',text_color='#102A43',command=lambda x=r:self.change_password(x)).pack(side='right',padx=4)
    def new_user(self):
        w=ctk.CTkToplevel(self);w.title('Novo utilizador');w.geometry('480x520');w.grab_set();fields=[]
        for label in ('Nome','E-mail','Password'):
            ctk.CTkLabel(w,text=label).pack(anchor='w',padx=30,pady=(16,3));e=ctk.CTkEntry(w,show='•' if label=='Password' else None);e.pack(fill='x',padx=30);fields.append(e)
        ctk.CTkLabel(w,text='Perfil').pack(anchor='w',padx=30,pady=(16,3));role=ctk.CTkOptionMenu(w,values=list(ROLES.keys()));role.set('cashier');role.pack(fill='x',padx=30)
        def save():
            try:UserService(self.db.conn).create(self.tenant_id,fields[0].get(),fields[1].get(),fields[2].get(),role.get());w.destroy();self.open('Utilizadores')
            except Exception as e:messagebox.showerror('Utilizador',str(e),parent=w)
        ctk.CTkButton(w,text='Criar utilizador',height=42,command=save).pack(fill='x',padx=30,pady=28)
    def toggle_user(self,r):
        try:UserService(self.db.conn).set_active(r['id'],not bool(r['active']));self.open('Utilizadores')
        except Exception as e:messagebox.showerror('Utilizador',str(e))
    def change_password(self,r):
        p=simpledialog.askstring('Password','Nova palavra-passe (mínimo 6 caracteres):',show='•',parent=self)
        if p:
            try:UserService(self.db.conn).set_password(r['id'],p);messagebox.showinfo('Utilizador','Palavra-passe alterada.')
            except Exception as e:messagebox.showerror('Utilizador',str(e))
    def invoices_pro(self):
        self.section('Facturação','Documentos emitidos, impressão A4 e POS.');box=ctk.CTkScrollableFrame(self.content,fg_color='transparent');box.pack(fill='both',expand=True,padx=34,pady=(0,28))
        rows=self.db.conn.execute("SELECT id,document_no,total,vat,payment_method,created_at FROM sales WHERE tenant_id=? ORDER BY created_at DESC",(self.tenant_id,)).fetchall()
        for r in rows:
            c=ctk.CTkFrame(box,fg_color='white',corner_radius=12);c.pack(fill='x',pady=5);ctk.CTkLabel(c,text=r['document_no'],font=ctk.CTkFont(weight='bold'),text_color='#102A43').pack(side='left',padx=18,pady=15);ctk.CTkLabel(c,text=f"{r['total']:.2f} MT  •  {r['payment_method']}  •  {r['created_at'][:16].replace('T',' ')}",text_color='#627D98').pack(side='left');ctk.CTkButton(c,text='A4',width=60,command=lambda x=r['id']:self.export(x,False)).pack(side='right',padx=4);ctk.CTkButton(c,text='POS',width=60,command=lambda x=r['id']:self.export(x,True)).pack(side='right',padx=4)
    def export(self,sale_id,thermal):
        try:messagebox.showinfo('Documento',f"PDF criado em:\n{InvoiceService(self.db.conn).pdf(self.tenant_id,sale_id,thermal)}")
        except Exception as e:messagebox.showerror('Documento',str(e))
    def contacts_pro(self,table,title):
        self.section(title,'Cadastro de entidades comerciais e contactos.');top=ctk.CTkFrame(self.content,fg_color='white',corner_radius=14);top.pack(fill='x',padx=34,pady=(0,12));search=ctk.CTkEntry(top,placeholder_text='Pesquisar nome, NUIT, telefone ou e-mail');search.pack(side='left',fill='x',expand=True,padx=14,pady=14);ctk.CTkButton(top,text='+ Novo',command=lambda:self.new_contact(table,title)).pack(side='right',padx=14);box=ctk.CTkScrollableFrame(self.content,fg_color='transparent');box.pack(fill='both',expand=True,padx=34,pady=(0,28));rows=self.db.conn.execute(f'SELECT * FROM {table} WHERE tenant_id=? ORDER BY name',(self.tenant_id,)).fetchall();
        for r in rows:
            c=ctk.CTkFrame(box,fg_color='white',corner_radius=12);c.pack(fill='x',pady=5);ctk.CTkLabel(c,text=r['name'],font=ctk.CTkFont(size=14,weight='bold'),text_color='#102A43').pack(side='left',padx=18,pady=15);ctk.CTkLabel(c,text=f"NUIT {r['nuit'] or '-'}  •  {r['phone'] or '-'}  •  {r['email'] or '-'}",text_color='#627D98').pack(side='left')
    def new_contact(self,table,title):
        w=ctk.CTkToplevel(self);w.title('Novo '+title[:-1]);w.geometry('480x520');w.grab_set();fields=[]
        labels=['Nome','NUIT','Telefone','E-mail'];
        for label in labels:ctk.CTkLabel(w,text=label).pack(anchor='w',padx=30,pady=(15,3));e=ctk.CTkEntry(w);e.pack(fill='x',padx=30);fields.append(e)
        if table=='suppliers':ctk.CTkLabel(w,text='Morada').pack(anchor='w',padx=30,pady=(15,3));address=ctk.CTkEntry(w);address.pack(fill='x',padx=30)
        def save():
            try:
                import uuid
                vals=[e.get().strip() for e in fields];address_val=address.get().strip() if table=='suppliers' else None
                if not vals[0]:raise ValueError('Nome é obrigatório.')
                if table=='customers':self.db.conn.execute('INSERT INTO customers VALUES(?,?,?,?,?,?)',(str(uuid.uuid4()),self.tenant_id,*vals))
                else:self.db.conn.execute('INSERT INTO suppliers VALUES(?,?,?,?,?,?,?)',(str(uuid.uuid4()),self.tenant_id,*vals,address_val))
                w.destroy();self.open(title)
            except Exception as e:messagebox.showerror(title,str(e),parent=w)
        ctk.CTkButton(w,text='Guardar',height=42,command=save).pack(fill='x',padx=30,pady=25)
    def purchases_pro(self):
        self.section('Compras','Entradas de mercadoria e histórico de fornecedores.');box=ctk.CTkScrollableFrame(self.content,fg_color='transparent');box.pack(fill='both',expand=True,padx=34,pady=(0,28));rows=self.db.conn.execute("SELECT p.*,s.name supplier FROM purchases p LEFT JOIN suppliers s ON s.id=p.supplier_id WHERE p.tenant_id=? ORDER BY p.created_at DESC",(self.tenant_id,)).fetchall();
        for r in rows:
            c=ctk.CTkFrame(box,fg_color='white',corner_radius=12);c.pack(fill='x',pady=5);ctk.CTkLabel(c,text=r['document_no'],font=ctk.CTkFont(weight='bold'),text_color='#102A43').pack(side='left',padx=18,pady=15);ctk.CTkLabel(c,text=f"{r['supplier'] or 'Sem fornecedor'}  •  {r['total']:.2f} MT  •  {r['status']}",text_color='#627D98').pack(side='left')
    def finance_pro(self):
        self.section('Financeiro & Caixa','Abertura, fecho e conferência do caixa.');cash=CashService(self.db.conn);active=cash.active(self.tenant_id,self.user_id);card=ctk.CTkFrame(self.content,fg_color='white',corner_radius=16);card.pack(fill='x',padx=34,pady=10);state='ABERTO' if active else 'FECHADO';ctk.CTkLabel(card,text=f'CAIXA {state}',font=ctk.CTkFont(size=20,weight='bold'),text_color='#14804A' if active else '#C92A2A').pack(anchor='w',padx=24,pady=(22,5));info=ctk.CTkLabel(card,text='',text_color='#627D98');info.pack(anchor='w',padx=24,pady=4)
        def refresh():
            a=cash.active(self.tenant_id,self.user_id);info.configure(text=f"Abertura: {a['opening_amount']:.2f} MT  •  Vendas: {cash.summary(self.tenant_id,a['id'])['sales']:.2f} MT  •  Esperado: {cash.summary(self.tenant_id,a['id'])['expected']:.2f} MT" if a else 'Nenhuma sessão aberta.')
        def toggle():
            try:
                a=cash.active(self.tenant_id,self.user_id)
                if a:
                    v=simpledialog.askfloat('Fechar caixa','Valor contado:',parent=self);cash.close_session(a['id'],v) if v is not None else None
                else:
                    v=simpledialog.askfloat('Abrir caixa','Fundo inicial:',parent=self,initialvalue=0);cash.open_session(self.tenant_id,self.user_id,v) if v is not None else None
                self.open('Financeiro')
            except Exception as e:messagebox.showerror('Caixa',str(e))
        ctk.CTkButton(card,text='Abrir / Fechar caixa',command=toggle).pack(anchor='w',padx=24,pady=(12,24));refresh()
    def license_pro(self):
        self.section('Licenciamento','Activation Key, plano e validade da subscrição.');r=self.db.conn.execute('SELECT * FROM licenses WHERE tenant_id=? LIMIT 1',(self.tenant_id,)).fetchone();card=ctk.CTkFrame(self.content,fg_color='white',corner_radius=16);card.pack(fill='x',padx=34,pady=10);ctk.CTkLabel(card,text='PLANO '+str(r['plan']).upper(),font=ctk.CTkFont(size=22,weight='bold'),text_color='#102A43').pack(anchor='w',padx=25,pady=(25,5));ctk.CTkLabel(card,text=f"Estado: {r['status']}\nExpira: {r['expires_at']}\nActivation Key: {r['license_key']}",justify='left',text_color='#627D98').pack(anchor='w',padx=25,pady=8);ctk.CTkButton(card,text='Copiar Activation Key',command=lambda:self.clipboard_append(r['license_key'])).pack(anchor='w',padx=25,pady=(5,25))
    def settings_pro(self):
        self.section('Configurações da empresa','Dados comerciais, cópias de segurança e operação local.');tenant=self.db.conn.execute('SELECT * FROM tenants WHERE id=?',(self.tenant_id,)).fetchone();card=ctk.CTkFrame(self.content,fg_color='white',corner_radius=16);card.pack(fill='x',padx=34,pady=10)
        fields=[]
        for label,key in [('Nome da empresa','name'),('NUIT','nuit')]:ctk.CTkLabel(card,text=label).pack(anchor='w',padx=24,pady=(18,3));e=ctk.CTkEntry(card);e.insert(0,tenant[key] or '');e.pack(fill='x',padx=24);fields.append((key,e))
        def save():
            self.db.conn.execute('UPDATE tenants SET name=?,nuit=? WHERE id=?',(fields[0][1].get().strip(),fields[1][1].get().strip(),self.tenant_id));messagebox.showinfo('Configurações','Dados da empresa actualizados.')
        ctk.CTkButton(card,text='Guardar dados',command=save).pack(anchor='w',padx=24,pady=18);ctk.CTkButton(card,text='Criar backup agora',fg_color='#E8EEF7',hover_color='#DCE6F3',text_color='#102A43',command=lambda:self.backup_now()).pack(anchor='w',padx=24,pady=(0,24));ctk.CTkLabel(self.content,text=f'Base de dados local: {DB_PATH}\nBackups: {BACKUP_DIR}',text_color='#627D98',justify='left').pack(anchor='w',padx=34,pady=10)
    def backup_now(self):
        try:messagebox.showinfo('Backup',f'Backup criado em:\n{create_backup()}')
        except Exception as e:messagebox.showerror('Backup',str(e))
