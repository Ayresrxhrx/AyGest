from __future__ import annotations
import shutil, uuid
from datetime import datetime, timezone, timedelta
from tkinter import filedialog, messagebox, simpledialog
import customtkinter as ctk
from .users import UserService, ROLES
from .invoicing import InvoiceService
from .config import APP_NAME, DB_PATH, settings

NAVY='#102A43'; MUTED='#627D98'; BG='#F4F7FA'; WHITE='#FFFFFF'; BLUE='#1769E0'; GREEN='#14804A'; RED='#C92A2A'
def money(v): return f"{float(v or 0):,.2f} MT".replace(',','X').replace('.',',').replace('X','.')
def now(): return datetime.now(timezone.utc).isoformat()
def uid(): return str(uuid.uuid4())

class EnterpriseApp(ctk.CTk):
    def __init__(self, db, tenant_id, user):
        super().__init__(); self.db=db; self.tenant_id=tenant_id; self.user=user; self.user_id=user['id']; self._schema(); self.title(APP_NAME+' — Gestão Empresarial'); self.geometry('1500x920'); self.minsize(1180,760); ctk.set_appearance_mode('light'); ctk.set_default_color_theme('blue'); self.build(); self.open('Dashboard')
    def _schema(self):
        self.db.conn.executescript('CREATE TABLE IF NOT EXISTS settings(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,key TEXT NOT NULL,value TEXT,UNIQUE(tenant_id,key));CREATE TABLE IF NOT EXISTS stock_movements(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,product_id TEXT NOT NULL,type TEXT NOT NULL,quantity REAL NOT NULL,unit_cost REAL NOT NULL DEFAULT 0,reference TEXT,notes TEXT,created_at TEXT NOT NULL,user_id TEXT);CREATE TABLE IF NOT EXISTS payments(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,sale_id TEXT,method TEXT NOT NULL,amount REAL NOT NULL,created_at TEXT NOT NULL,user_id TEXT);')
    def build(self):
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1); side=ctk.CTkFrame(self,width=270,fg_color='#0B2239',corner_radius=0); side.grid(row=0,column=0,sticky='nsew'); side.grid_propagate(False); ctk.CTkLabel(side,text='AyGest',font=ctk.CTkFont(size=32,weight='bold'),text_color='white').pack(anchor='w',padx=24,pady=(24,0)); ctk.CTkLabel(side,text='GESTÃO EMPRESARIAL',font=ctk.CTkFont(size=9,weight='bold'),text_color='#70A5D5').pack(anchor='w',padx=27,pady=(0,10)); ctk.CTkLabel(side,text=f"{self.user['name']} • {ROLES.get(self.user['role'],{}).get('label','Utilizador')}",font=ctk.CTkFont(size=10,weight='bold'),text_color='#DCEAF7').pack(anchor='w',padx=24,pady=(0,8)); self.nav=ctk.CTkScrollableFrame(side,fg_color='transparent',scrollbar_button_color='#315675'); self.nav.pack(fill='both',expand=True,padx=7)
        groups=[('PRINCIPAL',['Dashboard','POS / Vendas','Facturação']),('GESTÃO',['Produtos','Stock','Clientes','Fornecedores','Compras']),('OPERAÇÃO',['Financeiro','Relatórios']),('ADMINISTRAÇÃO',['Utilizadores','Licenciamento','Configurações','Auditoria','Backup'])]; self.buttons={}
        for title,items in groups:
            ctk.CTkLabel(self.nav,text=title,font=ctk.CTkFont(size=9,weight='bold'),text_color='#6D8BA5').pack(fill='x',padx=18,pady=(12,4))
            for item in items:
                b=ctk.CTkButton(self.nav,text=item,anchor='w',height=40,corner_radius=8,fg_color='transparent',hover_color='#173D60',text_color='#EAF2F8',command=lambda x=item:self.open(x)); b.pack(fill='x',padx=5,pady=2); self.buttons[item]=b
        ctk.CTkLabel(side,text=f'v{settings.app_version}',text_color='#6D8BA5',font=ctk.CTkFont(size=9)).pack(side='bottom',pady=10); self.content=ctk.CTkFrame(self,fg_color=BG,corner_radius=0); self.content.grid(row=0,column=1,sticky='nsew')
    def clear(self):
        for w in self.content.winfo_children(): w.destroy()
    def can(self,p): return UserService(self.db.conn).can(self.user,p)
    def header(self,title,subtitle='',actions=None):
        h=ctk.CTkFrame(self.content,fg_color='transparent'); h.pack(fill='x',padx=32,pady=(25,12)); l=ctk.CTkFrame(h,fg_color='transparent'); l.pack(side='left'); ctk.CTkLabel(l,text=title,font=ctk.CTkFont(size=29,weight='bold'),text_color=NAVY).pack(anchor='w'); ctk.CTkLabel(l,text=subtitle,text_color=MUTED).pack(anchor='w',pady=(2,0));
        for t,fn in reversed(actions or []): ctk.CTkButton(h,text=t,height=38,command=fn).pack(side='right',padx=4)
    def open(self,m):
        self.clear(); perm={'POS / Vendas':'sales','Facturação':'invoices','Produtos':'products','Stock':'stock','Clientes':'customers','Fornecedores':'suppliers','Compras':'purchases','Financeiro':'finance','Relatórios':'reports','Utilizadores':'users'}.get(m)
        if perm and not self.can(perm): return self.header('Acesso não autorizado','O seu perfil não possui permissão para este módulo.')
        fn={'Dashboard':self.dashboard,'POS / Vendas':self.pos,'Facturação':self.invoices,'Produtos':lambda:self.products(False),'Stock':lambda:self.products(True),'Clientes':lambda:self.entities('customers','Clientes'),'Fornecedores':lambda:self.entities('suppliers','Fornecedores',True),'Compras':self.purchases,'Financeiro':self.finance,'Relatórios':self.reports,'Utilizadores':self.users,'Licenciamento':self.license,'Configurações':self.config,'Auditoria':self.audit,'Backup':self.backup}.get(m)
        if fn: fn()
        for n,b in self.buttons.items(): b.configure(fg_color='#173D60' if n==m else 'transparent')
    def dashboard(self):
        self.header('Dashboard','Visão geral do negócio em tempo real.',[('Nova venda',self.pos)]); s=self.db.conn.execute("SELECT COALESCE(SUM(total),0) total,COUNT(*) n FROM sales WHERE tenant_id=? AND date(created_at)=date('now')",(self.tenant_id,)).fetchone(); low=self.db.conn.execute('SELECT COUNT(*) n FROM products p LEFT JOIN stock st ON st.product_id=p.id WHERE p.tenant_id=? AND p.active=1 AND COALESCE(st.quantity-st.reserved,0)<=p.min_stock',(self.tenant_id,)).fetchone()['n']; pro=self.db.conn.execute('SELECT COUNT(*) n FROM products WHERE tenant_id=? AND active=1',(self.tenant_id,)).fetchone()['n']; cli=self.db.conn.execute('SELECT COUNT(*) n FROM customers WHERE tenant_id=?',(self.tenant_id,)).fetchone()['n']; cards=ctk.CTkFrame(self.content,fg_color='transparent');cards.pack(fill='x',padx=27)
        for t,v,d,c in [('Vendas hoje',money(s['total']),f"{s['n']} documento(s)",GREEN),('Produtos',str(pro),'Activos',BLUE),('Stock baixo',str(low),'Requer atenção',RED if low else GREEN),('Clientes',str(cli),'Base comercial',BLUE)]: self.card(cards,t,v,d,c)
        body=ctk.CTkFrame(self.content,fg_color='transparent');body.pack(fill='both',expand=True,padx=32,pady=15); box=ctk.CTkFrame(body,fg_color=WHITE,corner_radius=14);box.pack(fill='both',expand=True);ctk.CTkLabel(box,text='Vendas dos últimos 7 dias',font=ctk.CTkFont(size=17,weight='bold'),text_color=NAVY).pack(anchor='w',padx=20,pady=18);rows=self.db.conn.execute("SELECT date(created_at) d,COALESCE(SUM(total),0) total FROM sales WHERE tenant_id=? AND date(created_at)>=date('now','-6 day') GROUP BY date(created_at) ORDER BY d",(self.tenant_id,)).fetchall(); vals={r['d']:r['total'] for r in rows};days=[((datetime.now(timezone.utc).date()-timedelta(days=6-i)).isoformat(),0) for i in range(7)];days=[(d,vals.get(d,0)) for d,_ in days];mx=max([v for _,v in days] or [1]) or 1
        for d,v in days:
            r=ctk.CTkFrame(box,fg_color='transparent');r.pack(fill='x',padx=20,pady=5);ctk.CTkLabel(r,text=d[5:],width=45,text_color=MUTED).pack(side='left');bar=ctk.CTkFrame(r,fg_color='#E6EEF7',height=22,corner_radius=5);bar.pack(side='left',fill='x',expand=True,padx=8);ctk.CTkFrame(bar,fg_color=BLUE,width=max(2,int(v/mx*350)),height=22,corner_radius=5).pack(side='left');ctk.CTkLabel(r,text=money(v),width=110,anchor='e',text_color=NAVY).pack(side='right')
    def card(self,p,t,v,d,c):
        x=ctk.CTkFrame(p,fg_color=WHITE,corner_radius=14);x.pack(side='left',fill='both',expand=True,padx=5);ctk.CTkLabel(x,text=t.upper(),font=ctk.CTkFont(size=9,weight='bold'),text_color=MUTED).pack(anchor='w',padx=18,pady=(16,3));ctk.CTkLabel(x,text=v,font=ctk.CTkFont(size=24,weight='bold'),text_color=c).pack(anchor='w',padx=18);ctk.CTkLabel(x,text=d,text_color=MUTED).pack(anchor='w',padx=18,pady=(2,16))
    def products(self,stock_only=False):
        self.header('Stock' if stock_only else 'Produtos','Catálogo, preços, stock disponível e movimentos.',[('+ Novo produto',self.product_form),('Movimento',self.stock_entry)]);q=ctk.CTkEntry(self.content,placeholder_text='Pesquisar por nome, SKU ou código de barras');q.pack(fill='x',padx=32,pady=(0,12));box=ctk.CTkScrollableFrame(self.content,fg_color='transparent');box.pack(fill='both',expand=True,padx=32,pady=(0,25))
        def render(_=None):
            for w in box.winfo_children():w.destroy();term=q.get().lower().strip();rows=self.db.conn.execute('SELECT p.*,COALESCE(SUM(st.quantity),0) qty,COALESCE(SUM(st.reserved),0) reserved,COALESCE(SUM(st.quantity-st.reserved),0) available FROM products p LEFT JOIN stock st ON st.product_id=p.id AND st.tenant_id=p.tenant_id WHERE p.tenant_id=? AND p.active=1 GROUP BY p.id ORDER BY p.name',(self.tenant_id,)).fetchall()
            for p in rows:
                if term and term not in f"{p['name']} {p['sku']} {p['barcode'] or ''}".lower():continue
                if stock_only and p['available']>p['min_stock']:continue
                c=ctk.CTkFrame(box,fg_color=WHITE,corner_radius=12);c.pack(fill='x',pady=4);ctk.CTkLabel(c,text=p['name'],font=ctk.CTkFont(size=14,weight='bold'),text_color=NAVY,width=230,anchor='w').pack(side='left',padx=15,pady=14);ctk.CTkLabel(c,text=f"SKU {p['sku']} • {p['category'] or 'Sem categoria'}",text_color=MUTED,width=190,anchor='w').pack(side='left');ctk.CTkLabel(c,text=f"Venda {money(p['sale_price'])}",text_color=NAVY,width=120).pack(side='left');ctk.CTkLabel(c,text=f"Disp. {p['available']:.2f}",font=ctk.CTkFont(weight='bold'),text_color=RED if p['available']<=p['min_stock'] else GREEN,width=110).pack(side='left');ctk.CTkButton(c,text='Editar',width=65,command=lambda x=p:self.product_form(x)).pack(side='right',padx=8)
        q.bind('<KeyRelease>',render);render()
    def product_form(self,row=None):
        w=ctk.CTkToplevel(self);w.title('Produto');w.geometry('600x760');w.grab_set();form=ctk.CTkScrollableFrame(w,fg_color=BG);form.pack(fill='both',expand=True);fields=[('Nome','name'),('SKU','sku'),('Código de barras','barcode'),('Categoria','category'),('Unidade','unit'),('Factor base','base_factor'),('Preço de compra','purchase_price'),('Preço de venda','sale_price'),('IVA (%)','vat_rate'),('Stock mínimo','min_stock')];es={}
        for lab,k in fields:ctk.CTkLabel(form,text=lab,text_color=NAVY,font=ctk.CTkFont(weight='bold')).pack(anchor='w',padx=20,pady=(10,3));es[k]=ctk.CTkEntry(form,height=40);es[k].pack(fill='x',padx=20)
        if row:
            for _,k in fields:es[k].insert(0,str(row[k] if row[k] is not None else ''))
        else:
            for k,v in {'unit':'UN','base_factor':'1','purchase_price':'0','sale_price':'0','vat_rate':'16','min_stock':'0'}.items():es[k].insert(0,v)
        def save():
            try:
                v={k:e.get().strip() for k,e in es.items()};nums={k:float(v[k]) for k in ('base_factor','purchase_price','sale_price','vat_rate','min_stock')};
                if not v['name'] or not v['sku']:raise ValueError('Nome e SKU são obrigatórios.')
                if row:self.db.conn.execute('UPDATE products SET name=?,sku=?,barcode=?,category=?,unit=?,base_factor=?,purchase_price=?,sale_price=?,vat_rate=?,min_stock=? WHERE id=? AND tenant_id=?',(v['name'],v['sku'],v['barcode'],v['category'],v['unit'],nums['base_factor'],nums['purchase_price'],nums['sale_price'],nums['vat_rate'],nums['min_stock'],row['id'],self.tenant_id))
                else:
                    pid=uid();self.db.conn.execute('INSERT INTO products(id,tenant_id,sku,barcode,name,category,unit,base_factor,purchase_price,sale_price,vat_rate,min_stock,active) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,1)',(pid,self.tenant_id,v['sku'],v['barcode'],v['name'],v['category'],v['unit'],nums['base_factor'],nums['purchase_price'],nums['sale_price'],nums['vat_rate'],nums['min_stock']));self.db.conn.execute('INSERT INTO stock VALUES(?,?,?,?,?,?,?)',(uid(),self.tenant_id,pid,'Principal',0,0,now()))
                self.db.conn.commit();w.destroy();self.open('Produtos')
            except Exception as e:messagebox.showerror('Produto',str(e),parent=w)
        ctk.CTkButton(w,text='Guardar produto',height=44,command=save).pack(fill='x',padx=25,pady=15)
    def stock_entry(self,row=None):
        products=self.db.conn.execute('SELECT id,name FROM products WHERE tenant_id=? AND active=1 ORDER BY name',(self.tenant_id,)).fetchall();w=ctk.CTkToplevel(self);w.title('Movimento de stock');w.geometry('500x420');w.grab_set();combo=ctk.CTkComboBox(w,values=[f"{p['id']}|{p['name']}" for p in products]);combo.pack(fill='x',padx=28,pady=(35,8));typ=ctk.CTkComboBox(w,values=['Entrada','Saída']);typ.set('Entrada');typ.pack(fill='x',padx=28,pady=8);qty=ctk.CTkEntry(w,placeholder_text='Quantidade');qty.pack(fill='x',padx=28,pady=8);cost=ctk.CTkEntry(w,placeholder_text='Custo unitário');cost.pack(fill='x',padx=28,pady=8)
        def save():
            try:
                pid=combo.get().split('|',1)[0];q=float(qty.get());c=float(cost.get() or 0);sign=1 if typ.get()=='Entrada' else -1
                self.db.conn.execute('BEGIN IMMEDIATE');s=self.db.conn.execute("SELECT quantity,reserved FROM stock WHERE tenant_id=? AND product_id=? AND warehouse='Principal'",(self.tenant_id,pid)).fetchone();new=s['quantity']+sign*abs(q)
                if q<=0 or new<s['reserved']:raise ValueError('Quantidade inválida ou stock insuficiente.')
                self.db.conn.execute("UPDATE stock SET quantity=?,updated_at=? WHERE tenant_id=? AND product_id=? AND warehouse='Principal'",(new,now(),self.tenant_id,pid));self.db.conn.execute('INSERT INTO stock_movements VALUES(?,?,?,?,?,?,?,?,?,?)',(uid(),self.tenant_id,pid,'IN' if sign>0 else 'OUT',abs(q),c,'manual','Movimento manual',now(),self.user_id));self.db.conn.execute('COMMIT');w.destroy();self.open('Stock')
            except Exception as e:
                try:self.db.conn.execute('ROLLBACK')
                except:pass
                messagebox.showerror('Stock',str(e),parent=w)
        ctk.CTkButton(w,text='Confirmar movimento',height=44,command=save).pack(fill='x',padx=28,pady=20)
    def pos(self):
        self.header('POS / Vendas','Venda, cliente, stock, IVA e pagamento.');left=ctk.CTkFrame(self.content,fg_color=WHITE,corner_radius=14);left.pack(side='left',fill='both',expand=True,padx=(32,7),pady=(0,25));right=ctk.CTkFrame(self.content,fg_color=WHITE,corner_radius=14,width=390);right.pack(side='right',fill='y',padx=(7,32),pady=(0,25));right.pack_propagate(False);q=ctk.CTkEntry(left,placeholder_text='Pesquisar produto/SKU/código',height=42);q.pack(fill='x',padx=15,pady=15);grid=ctk.CTkScrollableFrame(left,fg_color='transparent');grid.pack(fill='both',expand=True,padx=10);cart=[]
        def render():
            for w in grid.winfo_children():w.destroy();term=q.get().lower().strip();rows=self.db.conn.execute('SELECT p.*,COALESCE(SUM(st.quantity-st.reserved),0) available FROM products p LEFT JOIN stock st ON st.product_id=p.id WHERE p.tenant_id=? AND p.active=1 GROUP BY p.id ORDER BY p.name',(self.tenant_id,)).fetchall()
            for p in rows:
                if term and term not in f"{p['name']} {p['sku']} {p['barcode'] or ''}".lower():continue
                ctk.CTkButton(grid,text=f"{p['name']}  •  {money(p['sale_price'])}  •  disponível {p['available']:.0f}",height=55,anchor='w',command=lambda x=p:add(x)).pack(fill='x',pady=3)
        def add(p):
            for x in cart:
                if x['id']==p['id']:
                    if x['qty']+1>p['available']:return messagebox.showwarning('Stock','Stock insuficiente.',parent=self)
                    x['qty']+=1;render_cart();return
            if p['available']<1:return messagebox.showwarning('Stock','Produto sem stock.',parent=self)
            cart.append({'id':p['id'],'name':p['name'],'price':p['sale_price'],'vat':p['vat_rate'],'qty':1});render_cart()
        q.bind('<KeyRelease>',lambda _:render());render();ctk.CTkLabel(right,text='Carrinho',font=ctk.CTkFont(size=21,weight='bold'),text_color=NAVY).pack(anchor='w',padx=18,pady=15);cartbox=ctk.CTkScrollableFrame(right,fg_color='#F8FAFC');cartbox.pack(fill='both',expand=True,padx=12);client=ctk.CTkComboBox(right,values=['Consumidor final']+[f"{r['id']}|{r['name']}" for r in self.db.conn.execute('SELECT id,name FROM customers WHERE tenant_id=? ORDER BY name',(self.tenant_id,)).fetchall()]);client.pack(fill='x',padx=12,pady=6);pay=ctk.CTkComboBox(right,values=['Dinheiro','M-Pesa','Cartão']);pay.set('Dinheiro');pay.pack(fill='x',padx=12,pady=6);total=ctk.CTkLabel(right,text='0,00 MT',font=ctk.CTkFont(size=25,weight='bold'),text_color=NAVY);total.pack(anchor='e',padx=18,pady=8)
        def render_cart():
            for w in cartbox.winfo_children():w.destroy();total.configure(text=money(sum(x['price']*x['qty'] for x in cart)))
            for x in cart:
                ctk.CTkLabel(cartbox,text=f"{x['name']}  •  {x['qty']} × {money(x['price'])}",anchor='w',text_color=NAVY).pack(fill='x',padx=8,pady=7)
        def finish():
            if not cart:return messagebox.showwarning('Venda','Carrinho vazio.',parent=self)
            try:
                self.db.conn.execute('BEGIN IMMEDIATE');cid=None if client.get()=='Consumidor final' else client.get().split('|',1)[0];sub=sum(x['price']*x['qty'] for x in cart);vat=sum(x['price']*x['qty']*x['vat']/100 for x in cart);sid=uid();n=self.db.conn.execute('SELECT COUNT(*) n FROM sales WHERE tenant_id=?',(self.tenant_id,)).fetchone()['n']+1;doc=f"FT-{datetime.now().strftime('%Y%m%d')}-{n:05d}";self.db.conn.execute('INSERT INTO sales VALUES(?,?,?,?,?,?,?,?,?)',(sid,self.tenant_id,cid,sub,vat,pay.get(),'completed',doc,now()))
                for x in cart:
                    s=self.db.conn.execute("SELECT quantity,reserved FROM stock WHERE tenant_id=? AND product_id=? AND warehouse='Principal'",(self.tenant_id,x['id'])).fetchone();new=s['quantity']-x['qty']
                    if not s or new<s['reserved']:raise ValueError('Stock insuficiente: '+x['name'])
                    self.db.conn.execute("UPDATE stock SET quantity=?,updated_at=? WHERE tenant_id=? AND product_id=? AND warehouse='Principal'",(new,now(),self.tenant_id,x['id']));self.db.conn.execute('INSERT INTO sale_items VALUES(?,?,?,?,?,?,?)',(uid(),sid,x['id'],x['qty'],x['price'],x['price']*x['qty'],x['vat']));self.db.conn.execute('INSERT INTO stock_movements VALUES(?,?,?,?,?,?,?,?,?,?)',(uid(),self.tenant_id,x['id'],'SALE',x['qty'],x['price'],doc,'Venda',now(),self.user_id))
                self.db.conn.execute('INSERT INTO payments VALUES(?,?,?,?,?,?,?)',(uid(),self.tenant_id,sid,pay.get(),sub,now(),self.user_id));self.db.conn.execute('INSERT INTO finance_movements VALUES(?,?,?,?,?,?,?,?)',(uid(),self.tenant_id,self.user_id,'income','Venda '+doc,sub,pay.get(),now()));self.db.conn.execute('INSERT INTO audit_log VALUES(?,?,?,?,?,?)',(uid(),self.tenant_id,self.user_id,'sale',doc,now()));self.db.conn.execute('COMMIT');cart.clear();render_cart();render();messagebox.showinfo('Venda concluída',f'{doc}\n{money(sub)}',parent=self)
            except Exception as e:
                try:self.db.conn.execute('ROLLBACK')
                except:pass
                messagebox.showerror('Venda',str(e),parent=self)
        ctk.CTkButton(right,text='FINALIZAR VENDA',height=50,command=finish).pack(fill='x',padx=12,pady=15)
    def invoices(self):
        self.header('Facturação','Histórico e exportação profissional A4/POS.',[('Nova venda',self.pos)]);box=ctk.CTkScrollableFrame(self.content,fg_color='transparent');box.pack(fill='both',expand=True,padx=32,pady=(0,25));rows=self.db.conn.execute("SELECT s.*,COALESCE(c.name,'Consumidor final') customer FROM sales s LEFT JOIN customers c ON c.id=s.customer_id WHERE s.tenant_id=? ORDER BY s.created_at DESC",(self.tenant_id,)).fetchall()
        for r in rows:
            c=ctk.CTkFrame(box,fg_color=WHITE,corner_radius=12);c.pack(fill='x',pady=4);ctk.CTkLabel(c,text=r['document_no'],font=ctk.CTkFont(weight='bold'),text_color=NAVY).pack(side='left',padx=15,pady=14);ctk.CTkLabel(c,text=f"{r['customer']} • {money(r['total'])} • {r['payment_method']}",text_color=MUTED).pack(side='left');ctk.CTkButton(c,text='A4',width=55,command=lambda x=r['id']:self.export(x,False)).pack(side='right',padx=3);ctk.CTkButton(c,text='POS',width=55,command=lambda x=r['id']:self.export(x,True)).pack(side='right',padx=3)
    def export(self,sid,thermal):
        try:messagebox.showinfo('Documento',InvoiceService(self.db.conn).pdf(self.tenant_id,sid,thermal),parent=self)
        except Exception as e:messagebox.showerror('Documento',str(e),parent=self)
    def entities(self,table,title,supplier=False):
        self.header(title,'Cadastro, pesquisa e edição.',[('+ Novo',lambda:self.entity_form(table,title,supplier))]);box=ctk.CTkScrollableFrame(self.content,fg_color='transparent');box.pack(fill='both',expand=True,padx=32,pady=(0,25));rows=self.db.conn.execute(f'SELECT * FROM {table} WHERE tenant_id=? ORDER BY name',(self.tenant_id,)).fetchall()
        for r in rows:
            c=ctk.CTkFrame(box,fg_color=WHITE,corner_radius=12);c.pack(fill='x',pady=4);ctk.CTkLabel(c,text=r['name'],font=ctk.CTkFont(weight='bold'),text_color=NAVY,width=240,anchor='w').pack(side='left',padx=15,pady=14);ctk.CTkLabel(c,text=f"NUIT {r['nuit'] or '-'} • {r['phone'] or '-'} • {r['email'] or '-'}",text_color=MUTED).pack(side='left');ctk.CTkButton(c,text='Editar',width=65,command=lambda x=r:self.entity_form(table,title,supplier,x)).pack(side='right',padx=8)
    def entity_form(self,table,title,supplier=False,row=None):
        w=ctk.CTkToplevel(self);w.title(title);w.geometry('560x620');w.grab_set();form=ctk.CTkScrollableFrame(w,fg_color=BG);form.pack(fill='both',expand=True);fields=[('Nome / Razão social','name'),('NUIT','nuit'),('Telefone','phone'),('E-mail','email')]+([('Morada','address')] if supplier else []);es={}
        for lab,k in fields:ctk.CTkLabel(form,text=lab,text_color=NAVY,font=ctk.CTkFont(weight='bold')).pack(anchor='w',padx=22,pady=(12,3));es[k]=ctk.CTkEntry(form,height=40);es[k].pack(fill='x',padx=22)
        if row:
            for _,k in fields:es[k].insert(0,str(row[k] or ''))
        def save():
            try:
                v={k:e.get().strip() for k,e in es.items()};
                if not v['name']:raise ValueError('Nome obrigatório.')
                if row:self.db.conn.execute(f"UPDATE {table} SET {','.join(k+'=?' for k in es)} WHERE id=? AND tenant_id=?",(*v.values(),row['id'],self.tenant_id))
                else:self.db.conn.execute(f"INSERT INTO {table}(id,tenant_id,{','.join(es)}) VALUES(?,?,{','.join('?' for _ in es)})",(uid(),self.tenant_id,*v.values()))
                self.db.conn.commit();w.destroy();self.open(title)
            except Exception as e:messagebox.showerror(title,str(e),parent=w)
        ctk.CTkButton(w,text='Guardar',height=44,command=save).pack(fill='x',padx=22,pady=14)
    def purchases(self):
        self.header('Compras','Entradas de mercadoria e actualização do stock.',[('Nova compra',self.purchase_form)]);box=ctk.CTkScrollableFrame(self.content,fg_color='transparent');box.pack(fill='both',expand=True,padx=32,pady=(0,25));rows=self.db.conn.execute("SELECT p.*,COALESCE(s.name,'Sem fornecedor') supplier FROM purchases p LEFT JOIN suppliers s ON s.id=p.supplier_id WHERE p.tenant_id=? ORDER BY p.created_at DESC",(self.tenant_id,)).fetchall();
        for r in rows:
            c=ctk.CTkFrame(box,fg_color=WHITE,corner_radius=12);c.pack(fill='x',pady=4);ctk.CTkLabel(c,text=r['document_no'],font=ctk.CTkFont(weight='bold'),text_color=NAVY).pack(side='left',padx=15,pady=14);ctk.CTkLabel(c,text=f"{r['supplier']} • {money(r['total'])} • {r['status']}",text_color=MUTED).pack(side='left')
    def purchase_form(self):
        products=self.db.conn.execute('SELECT id,name,purchase_price FROM products WHERE tenant_id=? AND active=1 ORDER BY name',(self.tenant_id,)).fetchall();suppliers=self.db.conn.execute('SELECT id,name FROM suppliers WHERE tenant_id=? ORDER BY name',(self.tenant_id,)).fetchall();w=ctk.CTkToplevel(self);w.title('Nova compra');w.geometry('600x620');w.grab_set();doc=ctk.CTkEntry(w,placeholder_text='Número do documento');doc.pack(fill='x',padx=28,pady=(35,8));sup=ctk.CTkComboBox(w,values=['']+[f"{x['id']}|{x['name']}" for x in suppliers]);sup.pack(fill='x',padx=28,pady=8);prod=ctk.CTkComboBox(w,values=[f"{x['id']}|{x['name']}" for x in products]);prod.pack(fill='x',padx=28,pady=8);qty=ctk.CTkEntry(w,placeholder_text='Quantidade');qty.pack(fill='x',padx=28,pady=8);cost=ctk.CTkEntry(w,placeholder_text='Custo unitário');cost.pack(fill='x',padx=28,pady=8)
        def save():
            try:
                pid=prod.get().split('|',1)[0];q=float(qty.get());c=float(cost.get());sid=sup.get().split('|',1)[0] if sup.get() else None
                if not doc.get().strip() or not pid or q<=0 or c<0:raise ValueError('Dados da compra inválidos.')
                purchase=uid();total=q*c;self.db.conn.execute('BEGIN IMMEDIATE');self.db.conn.execute('INSERT INTO purchases VALUES(?,?,?,?,?,?,?)',(purchase,self.tenant_id,doc.get().strip(),sid,total,'received',now()));self.db.conn.execute('INSERT INTO purchase_items VALUES(?,?,?,?,?,?)',(uid(),purchase,pid,q,c,total));self.db.conn.execute("UPDATE stock SET quantity=quantity+?,updated_at=? WHERE tenant_id=? AND product_id=? AND warehouse='Principal'",(q,now(),self.tenant_id,pid));self.db.conn.execute('INSERT INTO stock_movements VALUES(?,?,?,?,?,?,?,?,?,?)',(uid(),self.tenant_id,pid,'PURCHASE',q,c,doc.get().strip(),'Compra recebida',now(),self.user_id));self.db.conn.execute('COMMIT');w.destroy();self.open('Compras')
            except Exception as e:
                try:self.db.conn.execute('ROLLBACK')
                except:pass
                messagebox.showerror('Compra',str(e),parent=w)
        ctk.CTkButton(w,text='Registar compra e actualizar stock',height=44,command=save).pack(fill='x',padx=28,pady=25)
    def finance(self):
        self.header('Financeiro & Caixa','Abertura, fecho e movimentos.',[('Abrir caixa',self.open_cash),('Fechar caixa',self.close_cash)]);rows=self.db.conn.execute('SELECT * FROM cash_sessions WHERE tenant_id=? ORDER BY opened_at DESC',(self.tenant_id,)).fetchall();self.table(['Abertura','Fecho','Fundo','Contado','Estado'],[[r['opened_at'][:16],r['closed_at'][:16] if r['closed_at'] else '-',money(r['opening_amount']),money(r['closing_amount']), 'Fechado' if r['closed_at'] else 'Aberto'] for r in rows])
    def open_cash(self):
        v=simpledialog.askfloat('Abrir caixa','Fundo inicial (MT):',parent=self,minvalue=0)
        if v is not None:self.db.conn.execute('INSERT INTO cash_sessions VALUES(?,?,?,?,?,?,?)',(uid(),self.tenant_id,self.user_id,v,None,now(),None));self.db.conn.commit();self.open('Financeiro')
    def close_cash(self):
        r=self.db.conn.execute('SELECT * FROM cash_sessions WHERE tenant_id=? AND closed_at IS NULL ORDER BY opened_at DESC LIMIT 1',(self.tenant_id,)).fetchone();
        if not r:return messagebox.showwarning('Caixa','Não existe caixa aberto.',parent=self)
        v=simpledialog.askfloat('Fechar caixa','Valor contado (MT):',parent=self,minvalue=0)
        if v is not None:self.db.conn.execute('UPDATE cash_sessions SET closing_amount=?,closed_at=? WHERE id=?',(v,now(),r['id']));self.db.conn.commit();self.open('Financeiro')
    def reports(self):
        self.header('Relatórios','Dados reais de vendas e IVA.');rows=self.db.conn.execute("SELECT date(created_at) d,COUNT(*) docs,COALESCE(SUM(total),0) total,COALESCE(SUM(vat),0) vat FROM sales WHERE tenant_id=? GROUP BY date(created_at) ORDER BY d DESC LIMIT 90",(self.tenant_id,)).fetchall();self.table(['Data','Documentos','Vendas','IVA'],[[r['d'],r['docs'],money(r['total']),money(r['vat'])] for r in rows])
    def table(self,heads,rows):
        o=ctk.CTkFrame(self.content,fg_color=WHITE,corner_radius=14);o.pack(fill='both',expand=True,padx=32,pady=(0,25));h=ctk.CTkFrame(o,fg_color='#EEF3F8',corner_radius=8);h.pack(fill='x',padx=10,pady=10);[ctk.CTkLabel(h,text=x,font=ctk.CTkFont(weight='bold'),text_color=MUTED).pack(side='left',fill='x',expand=True,padx=8,pady=10,anchor='w') for x in heads];b=ctk.CTkScrollableFrame(o,fg_color='transparent');b.pack(fill='both',expand=True,padx=10,pady=(0,10));
        for r in rows:
            x=ctk.CTkFrame(b,fg_color=WHITE,corner_radius=7);x.pack(fill='x',pady=2);[ctk.CTkLabel(x,text=str(v),text_color=NAVY).pack(side='left',fill='x',expand=True,padx=8,pady=10,anchor='w') for v in r]
    def users(self):
        self.header('Utilizadores & Permissões','Perfis e segurança.',[('Novo utilizador',self.user_form)]);rows=self.db.conn.execute('SELECT * FROM users WHERE tenant_id=? ORDER BY name',(self.tenant_id,)).fetchall();self.table(['Nome','E-mail','Perfil','Estado'],[[r['name'],r['email'] or '-',ROLES.get(r['role'],{}).get('label',r['role']),'Activo' if r['active'] else 'Inactivo'] for r in rows])
    def user_form(self):
        w=ctk.CTkToplevel(self);w.title('Novo utilizador');w.geometry('520x560');w.grab_set();es={}
        for lab,k in [('Nome','name'),('E-mail','email'),('Palavra-passe','password')]:ctk.CTkLabel(w,text=lab,text_color=NAVY).pack(anchor='w',padx=28,pady=(16,3));es[k]=ctk.CTkEntry(w,height=40,show='•' if k=='password' else None);es[k].pack(fill='x',padx=28)
        role=ctk.CTkComboBox(w,values=list(ROLES.keys()));role.set('cashier');role.pack(fill='x',padx=28,pady=15)
        def save():
            try:UserService(self.db.conn).create(self.tenant_id,es['name'].get(),es['email'].get(),es['password'].get(),role.get());self.db.conn.commit();w.destroy();self.open('Utilizadores')
            except Exception as e:messagebox.showerror('Utilizador',str(e),parent=w)
        ctk.CTkButton(w,text='Criar utilizador',height=44,command=save).pack(fill='x',padx=28,pady=20)
    def license(self):
        self.header('Licenciamento','Activation Key, plano e validade.');r=self.db.conn.execute('SELECT * FROM licenses WHERE tenant_id=? ORDER BY expires_at DESC LIMIT 1',(self.tenant_id,)).fetchone();box=ctk.CTkFrame(self.content,fg_color=WHITE,corner_radius=14);box.pack(fill='x',padx=32,pady=10);ctk.CTkLabel(box,text=f"Plano: {r['plan'] if r else '-'}",font=ctk.CTkFont(size=20,weight='bold'),text_color=NAVY).pack(anchor='w',padx=25,pady=(22,5));ctk.CTkLabel(box,text=f"Estado: {r['status'] if r else '-'} • Expira: {r['expires_at'][:10] if r and r['expires_at'] else '-'}",text_color=MUTED).pack(anchor='w',padx=25);key=ctk.CTkEntry(box,placeholder_text='Activation Key');key.pack(fill='x',padx=25,pady=14)
        def activate():
            row=self.db.conn.execute('SELECT id FROM licenses WHERE license_key=?',(key.get().strip(),)).fetchone();
            if not row:return messagebox.showerror('Licenciamento','Activation Key inválida.',parent=self)
            self.db.conn.execute("UPDATE licenses SET tenant_id=?,status='active',expires_at=? WHERE id=?",(self.tenant_id,(datetime.now(timezone.utc)+timedelta(days=365)).isoformat(),row['id']));self.db.conn.commit();self.open('Licenciamento');messagebox.showinfo('Licenciamento','Licença activada.',parent=self)
        ctk.CTkButton(box,text='Activar licença',command=activate).pack(anchor='w',padx=25,pady=(0,22))
    def config(self):
        self.header('Configurações','Dados da empresa.');r=self.db.conn.execute('SELECT * FROM tenants WHERE id=?',(self.tenant_id,)).fetchone();box=ctk.CTkFrame(self.content,fg_color=WHITE,corner_radius=14);box.pack(fill='x',padx=32,pady=10);name=ctk.CTkEntry(box,height=42);name.insert(0,r['name']);name.pack(fill='x',padx=25,pady=(25,8));nuit=ctk.CTkEntry(box,height=42);nuit.insert(0,r['nuit'] or '');nuit.pack(fill='x',padx=25,pady=8)
        def save():self.db.conn.execute('UPDATE tenants SET name=?,nuit=? WHERE id=?',(name.get().strip(),nuit.get().strip(),self.tenant_id));self.db.conn.commit();messagebox.showinfo('Configurações','Dados guardados.',parent=self)
        ctk.CTkButton(box,text='Guardar alterações',command=save).pack(anchor='w',padx=25,pady=18)
    def audit(self):
        self.header('Auditoria','Histórico das operações.');rows=self.db.conn.execute("SELECT a.created_at,COALESCE(u.name,'Sistema') user,a.action,a.details FROM audit_log a LEFT JOIN users u ON u.id=a.user_id WHERE a.tenant_id=? ORDER BY a.created_at DESC LIMIT 500",(self.tenant_id,)).fetchall();self.table(['Data','Utilizador','Acção','Detalhes'],[[r['created_at'][:19],r['user'],r['action'],r['details'] or '-'] for r in rows])
    def backup(self):
        self.header('Backup','Cópia de segurança do SQLite.',[('Criar backup',self.make_backup)]);box=ctk.CTkFrame(self.content,fg_color=WHITE,corner_radius=14);box.pack(fill='x',padx=32,pady=10);ctk.CTkLabel(box,text='Backup completo',font=ctk.CTkFont(size=20,weight='bold'),text_color=NAVY).pack(anchor='w',padx=25,pady=(22,5));ctk.CTkLabel(box,text='Pode guardar uma cópia da base de dados para recuperação.',text_color=MUTED).pack(anchor='w',padx=25,pady=(0,22))
    def make_backup(self):
        target=filedialog.asksaveasfilename(parent=self,title='Guardar backup',defaultextension='.db',filetypes=[('SQLite','*.db')],initialfile=f'AyGest-backup-{datetime.now().strftime("%Y%m%d-%H%M%S")}.db');
        if target:self.db.conn.commit();shutil.copy2(DB_PATH,target);messagebox.showinfo('Backup','Backup criado com sucesso.',parent=self)
