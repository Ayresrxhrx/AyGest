from __future__ import annotations
import uuid
import customtkinter as ctk
from tkinter import messagebox

NAVY='#102A43'; MUTED='#627D98'; BG='#F4F7FA'; WHITE='#FFFFFF'; BLUE='#1769E0'; GREEN='#14804A'; RED='#C92A2A'; BORDER='#DCE5EE'

class ManagementHub:
    def __init__(self, app):
        self.app=app; self.db=app.db; self.tenant_id=app.tenant_id; self.body=None
    def show(self):
        for w in self.app.content.winfo_children(): w.destroy()
        h=ctk.CTkFrame(self.app.content,fg_color='transparent');h.pack(fill='x',padx=32,pady=(25,14));ctk.CTkLabel(h,text='Gestão',font=ctk.CTkFont(size=30,weight='bold'),text_color=NAVY).pack(anchor='w');ctk.CTkLabel(h,text='Centro de gestão empresarial — cadastros, operação e controlo.',text_color=MUTED).pack(anchor='w',pady=(3,0))
        tabs=ctk.CTkFrame(self.app.content,fg_color=WHITE,corner_radius=12);tabs.pack(fill='x',padx=32,pady=(0,12))
        for label,fn in [('Visão geral',self.overview),('Clientes',lambda:self.entities('customers','Clientes',False)),('Fornecedores',lambda:self.entities('suppliers','Fornecedores',True)),('Produtos',lambda:self.app.open('Produtos')),('Stock',lambda:self.app.open('Stock')),('Compras',lambda:self.app.open('Compras'))]: ctk.CTkButton(tabs,text=label,fg_color='transparent',hover_color='#EAF1F8',text_color=NAVY,height=42,command=fn).pack(side='left',padx=3,pady=5)
        self.body=ctk.CTkScrollableFrame(self.app.content,fg_color='transparent');self.body.pack(fill='both',expand=True,padx=32,pady=(0,25));self.overview()
    def overview(self):
        for w in self.body.winfo_children():w.destroy()
        cards=[('Clientes','SELECT COUNT(*) FROM customers WHERE tenant_id=?',BLUE),('Fornecedores','SELECT COUNT(*) FROM suppliers WHERE tenant_id=?',GREEN),('Produtos activos','SELECT COUNT(*) FROM products WHERE tenant_id=? AND active=1',NAVY),('Stock baixo','SELECT COUNT(*) FROM products WHERE tenant_id=? AND active=1 AND COALESCE(stock,0)<=COALESCE(min_stock,0)',RED)]
        grid=ctk.CTkFrame(self.body,fg_color='transparent');grid.pack(fill='x')
        for i,(label,sql,accent) in enumerate(cards):
            n=self.db.conn.execute(sql,(self.tenant_id,)).fetchone()[0];card=ctk.CTkFrame(grid,fg_color=WHITE,corner_radius=14,border_width=1,border_color=BORDER);card.grid(row=0,column=i,padx=5,sticky='ew');grid.grid_columnconfigure(i,weight=1);ctk.CTkLabel(card,text=label,text_color=MUTED,font=ctk.CTkFont(size=11,weight='bold')).pack(anchor='w',padx=18,pady=(16,2));ctk.CTkLabel(card,text=str(n),text_color=accent,font=ctk.CTkFont(size=28,weight='bold')).pack(anchor='w',padx=18,pady=(0,16))
        section=ctk.CTkFrame(self.body,fg_color=WHITE,corner_radius=14);section.pack(fill='x',pady=14);ctk.CTkLabel(section,text='Operações rápidas',text_color=NAVY,font=ctk.CTkFont(size=17,weight='bold')).pack(anchor='w',padx=20,pady=(18,10))
        for text,fn in [('+ Cliente',lambda:self.entity_form('customers','Clientes')),('+ Fornecedor',lambda:self.entity_form('suppliers','Fornecedores',True)),('Abrir Produtos',lambda:self.app.open('Produtos')),('Abrir Stock',lambda:self.app.open('Stock')),('Nova Compra',lambda:self.app.purchase_form())]: ctk.CTkButton(section,text=text,command=fn,height=38).pack(side='left',padx=7,pady=(0,18))
    def entities(self,table,title,supplier=False):
        for w in self.body.winfo_children():w.destroy()
        top=ctk.CTkFrame(self.body,fg_color=WHITE,corner_radius=14);top.pack(fill='x',pady=(0,12));ctk.CTkLabel(top,text=title,text_color=NAVY,font=ctk.CTkFont(size=20,weight='bold')).pack(side='left',padx=18,pady=15);ctk.CTkButton(top,text='+ Novo',command=lambda:self.entity_form(table,title,supplier),height=36).pack(side='right',padx=12,pady=9);search=ctk.CTkEntry(top,placeholder_text='Pesquisar por nome, NUIT, telefone ou e-mail',width=330);search.pack(side='right',padx=8);box=ctk.CTkScrollableFrame(self.body,fg_color=WHITE,corner_radius=14);box.pack(fill='both',expand=True)
        def load():
            for w in box.winfo_children():w.destroy()
            q=f"%{search.get().strip()}%";rows=self.db.conn.execute(f"SELECT * FROM {table} WHERE tenant_id=? AND (name LIKE ? OR COALESCE(nuit,'') LIKE ? OR COALESCE(phone,'') LIKE ? OR COALESCE(email,'') LIKE ?) ORDER BY name",(self.tenant_id,q,q,q,q)).fetchall()
            if not rows:ctk.CTkLabel(box,text='Nenhum registo encontrado.',text_color=MUTED).pack(pady=40);return
            for r in rows:
                row=ctk.CTkFrame(box,fg_color='#FAFCFE',corner_radius=10);row.pack(fill='x',padx=10,pady=4);ctk.CTkLabel(row,text=r['name'],text_color=NAVY,font=ctk.CTkFont(weight='bold'),anchor='w').pack(side='left',padx=15,pady=13);ctk.CTkLabel(row,text=f"NUIT {r['nuit'] or '-'}  •  {r['phone'] or '-'}  •  {r['email'] or '-'}",text_color=MUTED).pack(side='left');ctk.CTkButton(row,text='Editar',width=70,command=lambda x=r:self.entity_form(table,title,supplier,x)).pack(side='right',padx=4);ctk.CTkButton(row,text='Eliminar',width=75,fg_color=RED,hover_color='#A61B1B',command=lambda x=r:self.delete(table,x['id'],load)).pack(side='right',padx=4)
        ctk.CTkButton(top,text='Actualizar',width=85,command=load).pack(side='right',padx=4);load()
    def entity_form(self,table,title,supplier=False,row=None):
        w=ctk.CTkToplevel(self.app);w.title(('Editar ' if row else 'Novo ')+title[:-1]);w.geometry('590x680');w.minsize(540,620);w.configure(fg_color=BG);w.transient(self.app);w.grab_set();header=ctk.CTkFrame(w,fg_color=WHITE,corner_radius=0);header.pack(fill='x');ctk.CTkLabel(header,text=('Editar ' if row else 'Novo ')+title[:-1],text_color=NAVY,font=ctk.CTkFont(size=23,weight='bold')).pack(anchor='w',padx=28,pady=(22,3));ctk.CTkLabel(header,text='Dados comerciais do registo',text_color=MUTED).pack(anchor='w',padx=28,pady=(0,18));form=ctk.CTkScrollableFrame(w,fg_color=BG);form.pack(fill='both',expand=True,padx=10,pady=10);labels=['Nome / Razão social','NUIT','Telefone','E-mail']+(['Morada'] if supplier else []);fields=[]
        for lab in labels:ctk.CTkLabel(form,text=lab,text_color=NAVY,font=ctk.CTkFont(size=11,weight='bold')).pack(anchor='w',padx=18,pady=(11,4));e=ctk.CTkEntry(form,height=42,corner_radius=8);e.pack(fill='x',padx=18);fields.append(e)
        if row:
            vals=[row['name'],row['nuit'] or '',row['phone'] or '',row['email'] or '']+([row['address'] or ''] if supplier else [])
            for e,v in zip(fields,vals):e.insert(0,v)
        footer=ctk.CTkFrame(w,fg_color=WHITE);footer.pack(fill='x');ctk.CTkButton(footer,text='Cancelar',fg_color='#E8EEF7',text_color=NAVY,command=w.destroy).pack(side='right',padx=6,pady=16);ctk.CTkButton(footer,text='Guardar',height=40,command=lambda:self.save_entity(w,table,supplier,row,fields)).pack(side='right',padx=6,pady=16)
    def save_entity(self,w,table,supplier,row,fields):
        vals=[x.get().strip() for x in fields]
        if not vals[0]:return messagebox.showerror('Gestão','Nome / razão social é obrigatório.',parent=w)
        try:
            if row:
                sets=['name=?','nuit=?','phone=?','email=?']+(['address=?'] if supplier else []);self.db.conn.execute(f"UPDATE {table} SET {','.join(sets)} WHERE id=? AND tenant_id=?",(*vals,row['id'],self.tenant_id))
            else:
                rid=str(uuid.uuid4());extra=',address' if supplier else '';marks=',?' if supplier else '';self.db.conn.execute(f"INSERT INTO {table}(id,tenant_id,name,nuit,phone,email{extra}) VALUES(?,?,?,?,?,?{marks})",(rid,self.tenant_id,*vals))
            self.db.conn.commit();w.destroy();self.show()
        except Exception as e:messagebox.showerror('Gestão',str(e),parent=w)
    def delete(self,table,rid,reload):
        if messagebox.askyesno('Gestão','Esta operação é permanente. Deseja eliminar este registo?',parent=self.app):self.db.conn.execute(f'DELETE FROM {table} WHERE id=? AND tenant_id=?',(rid,self.tenant_id));self.db.conn.commit();reload()

def install(app_class):
    def shell(self):
        for w in self.winfo_children():w.destroy()
        self.configure(fg_color=BG);self.grid_columnconfigure(1,weight=1);self.grid_rowconfigure(0,weight=1);side=ctk.CTkFrame(self,width=270,fg_color='#0B2239',corner_radius=0);side.grid(row=0,column=0,sticky='nsew');side.grid_propagate(False);ctk.CTkLabel(side,text='AyGest',font=ctk.CTkFont(size=31,weight='bold'),text_color='white').pack(anchor='w',padx=25,pady=(25,0));ctk.CTkLabel(side,text='GESTÃO EMPRESARIAL',font=ctk.CTkFont(size=9,weight='bold'),text_color='#6FA8DC').pack(anchor='w',padx=27,pady=(0,12));ctk.CTkLabel(side,text=self.user['name'],text_color='#DCEAF7',font=ctk.CTkFont(size=11,weight='bold')).pack(anchor='w',padx=25,pady=(0,8));nav=ctk.CTkScrollableFrame(side,fg_color='transparent',scrollbar_button_color='#315675',scrollbar_button_hover_color='#527B9E');nav.pack(fill='both',expand=True,padx=7)
        groups=[('PRINCIPAL',['Dashboard','POS / Vendas','Facturação']),('GESTÃO',['Gestão','Produtos','Stock','Clientes','Fornecedores','Compras']),('OPERAÇÃO',['Reservas','Cotações','Financeiro','Relatórios']),('ADMINISTRAÇÃO',['Utilizadores','Licenciamento','Configurações'])]
        for title,items in groups:
            ctk.CTkLabel(nav,text=title,text_color='#6D8BA5',font=ctk.CTkFont(size=9,weight='bold')).pack(fill='x',padx=18,pady=(11,4))
            for item in items:
                cmd=(lambda:self._management_hub.show()) if item=='Gestão' else (lambda x=item:self.open(x));ctk.CTkButton(nav,text=item,anchor='w',height=40,corner_radius=8,fg_color='transparent',hover_color='#173D60',text_color='#EAF2F8',command=cmd).pack(fill='x',padx=5,pady=2)
        ctk.CTkLabel(side,text='AyGest Desktop',text_color='#6D8BA5',font=ctk.CTkFont(size=9)).pack(side='bottom',pady=10);self.content=ctk.CTkFrame(self,fg_color=BG,corner_radius=0);self.content.grid(row=0,column=1,sticky='nsew');self._management_hub=ManagementHub(self);self.open('Dashboard')
    app_class._shell=shell
