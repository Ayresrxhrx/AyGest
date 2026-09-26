from __future__ import annotations
import csv, os, sqlite3, uuid
from datetime import datetime, timezone, timedelta
from tkinter import filedialog, messagebox, simpledialog
import customtkinter as ctk
from .app import App as BaseApp
from .users import UserService, ROLES
from .dashboard_ui import DashboardFrame
from .pos_ui import POSFrame
from .products_ui import ProductsFrame
from .reservations_ui import ReservationsFrame, QuotationsFrame
from .reports_ui import ReportsFrame
from .invoicing import InvoiceService
from .finance import CashService
from .backup import create_backup
from .config import APP_NAME, settings, DB_PATH

NAVY='#102A43'; MUTED='#627D98'; BG='#F4F7FA'; WHITE='#FFFFFF'; BLUE='#1769E0'; GREEN='#14804A'; RED='#C92A2A'; AMBER='#B7791F'; BORDER='#DCE5EE'

def money(v): return f"{float(v or 0):,.2f} MT".replace(',','X').replace('.',',').replace('X','.')
def now(): return datetime.now(timezone.utc).isoformat()

class ProApp(BaseApp):
    def _shell(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(fg_color=BG); self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        side=ctk.CTkFrame(self,width=255,fg_color='#0B2239',corner_radius=0); side.grid(row=0,column=0,sticky='nsew'); side.grid_propagate(False)
        ctk.CTkLabel(side,text='AyGest',font=ctk.CTkFont(size=31,weight='bold'),text_color='white').pack(anchor='w',padx=25,pady=(25,0))
        ctk.CTkLabel(side,text='GESTÃO EMPRESARIAL',font=ctk.CTkFont(size=9,weight='bold'),text_color='#6FA8DC').pack(anchor='w',padx=27,pady=(0,18))
        ctk.CTkLabel(side,text=f"{self.user['name']}  •  {ROLES.get(self.user['role'],{}).get('label','Utilizador')}",font=ctk.CTkFont(size=10,weight='bold'),text_color='#DCEAF7').pack(anchor='w',padx=25,pady=(0,12))
        groups=[('PRINCIPAL',['Dashboard','POS / Vendas','Facturação']),('GESTÃO',['Produtos','Stock','Clientes','Fornecedores','Compras']),('OPERAÇÃO',['Reservas','Cotações','Financeiro','Relatórios']),('ADMINISTRAÇÃO',['Utilizadores','Licenciamento','Configurações'])]
        self.nav=[]
        for title,items in groups:
            ctk.CTkLabel(side,text=title,font=ctk.CTkFont(size=9,weight='bold'),text_color='#6D8BA5').pack(fill='x',padx=25,pady=(10,4))
            for item in items:
                b=ctk.CTkButton(side,text=item,anchor='w',height=38,corner_radius=7,fg_color='transparent',hover_color='#173D60',text_color='#EAF2F8',command=lambda x=item:self.open(x)); b.pack(fill='x',padx=12,pady=1); self.nav.append((item,b))
        ctk.CTkLabel(side,text=f'Versão {settings.app_version}',text_color='#6D8BA5',font=ctk.CTkFont(size=9)).pack(side='bottom',pady=17)
        self.content=ctk.CTkFrame(self,fg_color=BG,corner_radius=0); self.content.grid(row=0,column=1,sticky='nsew'); self.open('Dashboard')
    def clear(self):
        for w in self.content.winfo_children(): w.destroy()
    def allowed(self,p): return UserService(self.db.conn).can(self.user,p)
    def header(self,title,subtitle='',actions=None):
        h=ctk.CTkFrame(self.content,fg_color='transparent'); h.pack(fill='x',padx=32,pady=(25,12));
        left=ctk.CTkFrame(h,fg_color='transparent'); left.pack(side='left'); ctk.CTkLabel(left,text=title,font=ctk.CTkFont(size=29,weight='bold'),text_color=NAVY).pack(anchor='w'); ctk.CTkLabel(left,text=subtitle,text_color=MUTED).pack(anchor='w',pady=(2,0))
        if actions:
            for text,cmd in reversed(actions): ctk.CTkButton(h,text=text,command=cmd,height=38).pack(side='right',padx=4)
    def open(self,m):
        self.clear(); mapping={'POS / Vendas':'sales','Facturação':'invoices','Produtos':'products','Stock':'stock','Clientes':'customers','Fornecedores':'suppliers','Compras':'purchases','Reservas':'reservations','Cotações':'quotations','Financeiro':'finance','Relatórios':'reports','Utilizadores':'users'}
        if m in mapping and not self.allowed(mapping[m]): return self.denied()
        if m=='Dashboard': return DashboardFrame(self.content,self.db,self.tenant_id,self.open).pack(fill='both',expand=True)
        if m=='POS / Vendas': return POSFrame(self.content,self.db,self.tenant_id,self.user_id).pack(fill='both',expand=True)
        if m in ('Produtos','Stock'): return ProductsFrame(self.content,self.db,self.tenant_id).pack(fill='both',expand=True)
        if m=='Reservas': return ReservationsFrame(self.content,self.db,self.tenant_id,self.user_id).pack(fill='both',expand=True)
        if m=='Cotações': return QuotationsFrame(self.content,self.db,self.tenant_id).pack(fill='both',expand=True)
        if m=='Relatórios': return ReportsFrame(self.content,self.db,self.tenant_id).pack(fill='both',expand=True)
        if m=='Facturação': return self.invoices()
        if m=='Clientes': return self.entities('customers','Clientes')
        if m=='Fornecedores': return self.entities('suppliers','Fornecedores',True)
        if m=='Compras': return self.purchases()
        if m=='Financeiro': return self.finance()
        if m=='Utilizadores': return self.users()
        if m=='Licenciamento': return self.license()
        if m=='Configurações': return self.settings_page()
    def denied(self):
        self.header('Acesso não autorizado','O perfil actual não possui permissão para este módulo.')
        ctk.CTkFrame(self.content,fg_color=WHITE,corner_radius=16).pack(fill='x',padx=32,pady=10)
    def toolbar(self,placeholder,refresh):
        t=ctk.CTkFrame(self.content,fg_color=WHITE,corner_radius=13); t.pack(fill='x',padx=32,pady=(0,12)); e=ctk.CTkEntry(t,placeholder_text=placeholder); e.pack(side='left',fill='x',expand=True,padx=14,pady=13); ctk.CTkButton(t,text='Pesquisar',width=100,command=lambda:refresh(e.get())).pack(side='right',padx=5); ctk.CTkButton(t,text='Limpar',width=75,fg_color='#E8EEF7',text_color=NAVY,command=lambda:(e.delete(0,'end'),refresh(''))).pack(side='right',padx=5); return e
    def table(self,headers,rows,actions=None):
        outer=ctk.CTkFrame(self.content,fg_color=WHITE,corner_radius=14); outer.pack(fill='both',expand=True,padx=32,pady=(0,25)); head=ctk.CTkFrame(outer,fg_color='#F0F4F8',corner_radius=9); head.pack(fill='x',padx=10,pady=10)
        widths=[max(90,min(230,900//len(headers))) for _ in headers]
        for i,h in enumerate(headers): ctk.CTkLabel(head,text=h,font=ctk.CTkFont(size=10,weight='bold'),text_color=MUTED,width=widths[i],anchor='w').grid(row=0,column=i,padx=8,pady=10,sticky='w')
        body=ctk.CTkScrollableFrame(outer,fg_color='transparent'); body.pack(fill='both',expand=True,padx=10,pady=(0,10))
        for idx,r in enumerate(rows):
            row=ctk.CTkFrame(body,fg_color='#FAFCFE' if idx%2==0 else WHITE,corner_radius=7); row.pack(fill='x',pady=2)
            vals=list(r)
            for i,v in enumerate(vals): ctk.CTkLabel(row,text=str(v),text_color=NAVY,width=widths[i],anchor='w').grid(row=0,column=i,padx=8,pady=10,sticky='w')
            if actions:
                for text,fn in actions:
                    ctk.CTkButton(row,text=text,width=65,height=28,command=lambda rr=r,f=fn:f(rr)).pack(side='right',padx=3,pady=5)
        return outer
    def invoices(self):
        self.header('Facturação','Facturas, documentos e impressão profissional.', [('Nova venda',lambda:self.open('POS / Vendas'))])
        rows=self.db.conn.execute("SELECT s.id,s.document_no,COALESCE(c.name,'Consumidor final') customer,s.total,s.vat,s.payment_method,s.created_at FROM sales s LEFT JOIN customers c ON c.id=s.customer_id WHERE s.tenant_id=? ORDER BY s.created_at DESC",(self.tenant_id,)).fetchall()
        box=ctk.CTkScrollableFrame(self.content,fg_color='transparent');box.pack(fill='both',expand=True,padx=32,pady=(0,25))
        for r in rows:
            c=ctk.CTkFrame(box,fg_color=WHITE,corner_radius=13);c.pack(fill='x',pady=5);ctk.CTkLabel(c,text=r['document_no'],font=ctk.CTkFont(weight='bold'),text_color=NAVY).pack(side='left',padx=18,pady=15);ctk.CTkLabel(c,text=f"{r['customer']}  •  {money(r['total'])}  •  IVA {money(r['vat'])}  •  {r['payment_method']}",text_color=MUTED).pack(side='left');ctk.CTkButton(c,text='A4',width=55,command=lambda x=r['id']:self.export_invoice(x,False)).pack(side='right',padx=3);ctk.CTkButton(c,text='POS',width=55,command=lambda x=r['id']:self.export_invoice(x,True)).pack(side='right',padx=3)
    def export_invoice(self,sale_id,thermal):
        try: path=InvoiceService(self.db.conn).pdf(self.tenant_id,sale_id,thermal); messagebox.showinfo('Documento pronto',f'Documento exportado em:\n{path}',parent=self)
        except Exception as e: messagebox.showerror('Facturação',str(e),parent=self)
    def entities(self,table,title,supplier=False):
        self.header(title,'Cadastro completo de entidades comerciais.',[(f'+ Novo {title[:-1]}',lambda:self.entity_form(table,title,supplier))])
        box=ctk.CTkScrollableFrame(self.content,fg_color='transparent');box.pack(fill='both',expand=True,padx=32,pady=(0,25)); rows=self.db.conn.execute(f'SELECT * FROM {table} WHERE tenant_id=? ORDER BY name',(self.tenant_id,)).fetchall()
        for r in rows:
            c=ctk.CTkFrame(box,fg_color=WHITE,corner_radius=13);c.pack(fill='x',pady=5);ctk.CTkLabel(c,text=r['name'],font=ctk.CTkFont(size=14,weight='bold'),text_color=NAVY).pack(side='left',padx=18,pady=14);ctk.CTkLabel(c,text=f"NUIT: {r['nuit'] or '-'}   •   {r['phone'] or '-'}   •   {r['email'] or '-'}",text_color=MUTED).pack(side='left');ctk.CTkButton(c,text='Editar',width=65,command=lambda x=r:self.entity_form(table,title,supplier,x)).pack(side='right',padx=8);ctk.CTkButton(c,text='Apagar',width=65,fg_color=RED,hover_color='#A61B1B',command=lambda x=r:self.delete_entity(table,x['id'],title)).pack(side='right',padx=2)
    def entity_form(self,table,title,supplier=False,row=None):
        w=ctk.CTkToplevel(self);w.title(('Editar ' if row else 'Novo ')+title[:-1]);w.geometry('520x600');w.grab_set(); labels=['Nome','NUIT','Telefone','E-mail'] + (['Morada'] if supplier else []); entries=[]
        for lab in labels:
            ctk.CTkLabel(w,text=lab,text_color=NAVY).pack(anchor='w',padx=30,pady=(13,3));e=ctk.CTkEntry(w,height=38);e.pack(fill='x',padx=30);entries.append(e)
        if row:
            vals=[row['name'],row['nuit'] or '',row['phone'] or '',row['email'] or '']+([row['address'] or ''] if supplier else [])
            for e,v in zip(entries,vals):e.insert(0,v)
        def save():
            vals=[e.get().strip() for e in entries]
            if not vals[0]: return messagebox.showerror(title,'O nome é obrigatório.',parent=w)
            try:
                if row:
                    sets=['name=?','nuit=?','phone=?','email=?']+(['address=?'] if supplier else []);self.db.conn.execute(f"UPDATE {table} SET {','.join(sets)} WHERE id=? AND tenant_id=?",(*vals,row['id'],self.tenant_id))
                else:
                    rid=str(uuid.uuid4());self.db.conn.execute(f"INSERT INTO {table}(id,tenant_id,name,nuit,phone,email{',address' if supplier else ''}) VALUES(?,?,?,?,?,?{',?' if supplier else ''})",(rid,self.tenant_id,*vals))
                w.destroy();self.open(title)
            except Exception as e:messagebox.showerror(title,str(e),parent=w)
        ctk.CTkButton(w,text='Guardar alterações' if row else 'Criar',height=42,command=save).pack(fill='x',padx=30,pady=25)
    def delete_entity(self,table,rid,title):
        if messagebox.askyesno(title,'Apagar este registo?',parent=self): self.db.conn.execute(f'DELETE FROM {table} WHERE id=? AND tenant_id=?',(rid,self.tenant_id));self.open(title)
    def purchases(self):
        self.header('Compras','Entradas de mercadoria, fornecedores e custos.', [('Nova compra',self.purchase_form)])
        rows=self.db.conn.execute("SELECT p.document_no,COALESCE(s.name,'Sem fornecedor'),p.total,p.status,p.created_at FROM purchases p LEFT JOIN suppliers s ON s.id=p.supplier_id WHERE p.tenant_id=? ORDER BY p.created_at DESC",(self.tenant_id,)).fetchall();self.table(['Documento','Fornecedor','Total','Estado','Data'],[[r['document_no'],r[1],money(r['total']),r['status'],r['created_at'][:16].replace('T',' ')] for r in rows])
    def purchase_form(self):
        w=ctk.CTkToplevel(self);w.title('Nova compra');w.geometry('600x620');w.grab_set();
        ctk.CTkLabel(w,text='Documento de compra',font=ctk.CTkFont(size=22,weight='bold'),text_color=NAVY).pack(anchor='w',padx=30,pady=25);doc=ctk.CTkEntry(w,placeholder_text='Número do documento');doc.pack(fill='x',padx=30,pady=8);sup=ctk.CTkComboBox(w,values=[f"{r['id']}|{r['name']}" for r in self.db.conn.execute('SELECT id,name FROM suppliers WHERE tenant_id=? ORDER BY name',(self.tenant_id,)).fetchall()]);sup.pack(fill='x',padx=30,pady=8);prod=ctk.CTkComboBox(w,values=[f"{r['id']}|{r['name']}" for r in self.db.conn.execute('SELECT id,name FROM products WHERE tenant_id=? AND active=1 ORDER BY name',(self.tenant_id,)).fetchall()]);prod.pack(fill='x',padx=30,pady=8);qty=ctk.CTkEntry(w,placeholder_text='Quantidade');qty.pack(fill='x',padx=30,pady=8);cost=ctk.CTkEntry(w,placeholder_text='Custo unitário (MT)');cost.pack(fill='x',padx=30,pady=8)
        def save():
            try:
                if not doc.get().strip() or not prod.get():raise ValueError('Documento e produto são obrigatórios.')
                pid=prod.get().split('|',1)[0];sid=sup.get().split('|',1)[0] if sup.get() else None;q=float(qty.get());c=float(cost.get());total=q*c;purchase_id=str(uuid.uuid4());self.db.conn.execute('INSERT INTO purchases(id,tenant_id,document_no,supplier_id,total,status,created_at) VALUES(?,?,?,?,?,?,?)',(purchase_id,self.tenant_id,doc.get().strip(),sid,total,'received',now()));self.db.conn.execute('INSERT INTO purchase_items(id,purchase_id,product_id,quantity,unit_cost,line_total) VALUES(?,?,?,?,?,?)',(str(uuid.uuid4()),purchase_id,pid,q,c,total));stock=self.db.conn.execute('SELECT id FROM stock WHERE tenant_id=? AND product_id=? AND warehouse=?',(self.tenant_id,pid,'Principal')).fetchone();
                if stock:self.db.conn.execute('UPDATE stock SET quantity=quantity+?,updated_at=? WHERE id=?',(q,now(),stock['id']))
                else:self.db.conn.execute('INSERT INTO stock VALUES(?,?,?,?,?,?,?)',(str(uuid.uuid4()),self.tenant_id,pid,'Principal',q,0,now()))
                w.destroy();self.open('Compras')
            except Exception as e:messagebox.showerror('Compra',str(e),parent=w)
        ctk.CTkButton(w,text='Registar entrada',height=44,command=save).pack(fill='x',padx=30,pady=25)
    def finance(self):
        self.header('Financeiro & Caixa','Abertura, movimentos, conferência e fecho do caixa.')
        cash=CashService(self.db.conn);a=cash.active(self.tenant_id,self.user_id);card=ctk.CTkFrame(self.content,fg_color=WHITE,corner_radius=16);card.pack(fill='x',padx=32,pady=8);state='ABERTO' if a else 'FECHADO';ctk.CTkLabel(card,text=f'CAIXA {state}',font=ctk.CTkFont(size=22,weight='bold'),text_color=GREEN if a else RED).pack(anchor='w',padx=25,pady=(20,3));info=ctk.CTkLabel(card,text='',text_color=MUTED);info.pack(anchor='w',padx=25,pady=5)
        if a:
            sm=cash.summary(self.tenant_id,a['id']);info.configure(text=f"Fundo: {money(sm['opening'])}  •  Vendas: {money(sm['sales'])}  •  Esperado: {money(sm['expected'])}")
        ctk.CTkButton(card,text='Fechar caixa' if a else 'Abrir caixa',command=lambda:self.toggle_cash(bool(a))).pack(anchor='w',padx=25,pady=(8,22))
        rows=self.db.conn.execute("SELECT kind,description,amount,payment_method,created_at FROM finance_movements WHERE tenant_id=? ORDER BY created_at DESC LIMIT 100",(self.tenant_id,)).fetchall();self.table(['Tipo','Descrição','Valor','Método','Data'],[[r['kind'],r['description'],money(r['amount']),r['payment_method'],r['created_at'][:16].replace('T',' ')] for r in rows])
    def toggle_cash(self,isopen):
        cash=CashService(self.db.conn)
        try:
            if isopen:
                a=cash.active(self.tenant_id,self.user_id);v=simpledialog.askfloat('Fechar caixa','Valor contado:',parent=self);cash.close_session(a['id'],v) if v is not None else None
            else:
                v=simpledialog.askfloat('Abrir caixa','Fundo inicial (MT):',parent=self);cash.open_session(self.tenant_id,self.user_id,v) if v is not None else None
            self.open('Financeiro')
        except Exception as e:messagebox.showerror('Caixa',str(e),parent=self)
    def users(self):
        self.header('Utilizadores & Permissões','Perfis, passwords e controlo de acesso.',[('+ Novo utilizador',self.new_user)])
        rows=self.db.conn.execute('SELECT * FROM users WHERE tenant_id=? ORDER BY name',(self.tenant_id,)).fetchall();box=ctk.CTkScrollableFrame(self.content,fg_color='transparent');box.pack(fill='both',expand=True,padx=32,pady=(0,25))
        for r in rows:
            c=ctk.CTkFrame(box,fg_color=WHITE,corner_radius=13);c.pack(fill='x',pady=5);ctk.CTkLabel(c,text=r['name'],font=ctk.CTkFont(weight='bold'),text_color=NAVY).pack(side='left',padx=18,pady=15);ctk.CTkLabel(c,text=f"{r['email'] or '-'}  •  {ROLES.get(r['role'],{}).get('label',r['role'])}  •  {'Activo' if r['active'] else 'Inactivo'}",text_color=MUTED).pack(side='left');ctk.CTkButton(c,text='Activar' if not r['active'] else 'Desactivar',width=100,command=lambda x=r:self.toggle_user(x)).pack(side='right',padx=7);ctk.CTkButton(c,text='Password',width=80,fg_color='#E8EEF7',text_color=NAVY,command=lambda x=r:self.change_password(x)).pack(side='right')
    def new_user(self):
        w=ctk.CTkToplevel(self);w.title('Novo utilizador');w.geometry('500x560');w.grab_set();ents=[]
        for lab in ['Nome','E-mail','Password']:
            ctk.CTkLabel(w,text=lab).pack(anchor='w',padx=30,pady=(18,3));e=ctk.CTkEntry(w,show='•' if lab=='Password' else None);e.pack(fill='x',padx=30);ents.append(e)
        ctk.CTkLabel(w,text='Perfil').pack(anchor='w',padx=30,pady=(18,3));role=ctk.CTkComboBox(w,values=list(ROLES.keys()));role.set('cashier');role.pack(fill='x',padx=30)
        def save():
            try:UserService(self.db.conn).create(self.tenant_id,*[e.get().strip() for e in ents],role.get());w.destroy();self.open('Utilizadores')
            except Exception as e:messagebox.showerror('Utilizador',str(e),parent=w)
        ctk.CTkButton(w,text='Criar utilizador',height=42,command=save).pack(fill='x',padx=30,pady=28)
    def toggle_user(self,r): UserService(self.db.conn).set_active(r['id'],not bool(r['active']));self.open('Utilizadores')
    def change_password(self,r):
        p=simpledialog.askstring('Password','Nova palavra-passe:',show='•',parent=self)
        if p:
            try:UserService(self.db.conn).set_password(r['id'],p);messagebox.showinfo('Utilizador','Password alterada.',parent=self)
            except Exception as e:messagebox.showerror('Utilizador',str(e),parent=self)
    def license(self):
        self.header('Licenciamento','Activation Key e estado da subscrição.')
        r=self.db.conn.execute('SELECT * FROM licenses WHERE tenant_id=? LIMIT 1',(self.tenant_id,)).fetchone();card=ctk.CTkFrame(self.content,fg_color=WHITE,corner_radius=16);card.pack(fill='x',padx=32,pady=10)
        for label,val in [('Plano',r['plan']),('Estado',r['status']),('Expira',r['expires_at'][:10] if r['expires_at'] else '-'),('Activation Key',r['license_key'])]:
            ctk.CTkLabel(card,text=label.upper(),font=ctk.CTkFont(size=9,weight='bold'),text_color=MUTED).pack(anchor='w',padx=25,pady=(18,0));ctk.CTkLabel(card,text=val,font=ctk.CTkFont(size=16,weight='bold'),text_color=NAVY).pack(anchor='w',padx=25,pady=(2,0))
        ctk.CTkButton(card,text='Activar nova Key',command=self.activate_key).pack(anchor='w',padx=25,pady=22)
    def activate_key(self):
        key=simpledialog.askstring('Licenciamento','Introduza a Activation Key:',parent=self)
        if key:
            self.db.conn.execute("UPDATE licenses SET license_key=?,status='active' WHERE tenant_id=?",(key.strip(),self.tenant_id));self.open('Licenciamento')
    def settings_page(self):
        self.header('Configurações','Empresa, base de dados e manutenção.')
        card=ctk.CTkFrame(self.content,fg_color=WHITE,corner_radius=16);card.pack(fill='x',padx=32,pady=10);row=self.db.conn.execute('SELECT name,nuit FROM tenants WHERE id=?',(self.tenant_id,)).fetchone();name=ctk.CTkEntry(card,height=40);name.insert(0,row['name']);name.pack(fill='x',padx=25,pady=(25,8));nuit=ctk.CTkEntry(card,height=40);nuit.insert(0,row['nuit'] or '');nuit.pack(fill='x',padx=25,pady=8)
        def save():self.db.conn.execute('UPDATE tenants SET name=?,nuit=? WHERE id=?',(name.get().strip(),nuit.get().strip(),self.tenant_id));messagebox.showinfo('Configurações','Dados da empresa guardados.',parent=self)
        ctk.CTkButton(card,text='Guardar empresa',command=save).pack(anchor='w',padx=25,pady=15);ctk.CTkButton(card,text='Criar backup da base de dados',fg_color='#E8EEF7',text_color=NAVY,command=self.backup).pack(anchor='w',padx=25,pady=(0,25))
    def backup(self):
        try:messagebox.showinfo('Backup',f'Backup criado em:\n{create_backup()}',parent=self)
        except Exception as e:messagebox.showerror('Backup',str(e),parent=self)
