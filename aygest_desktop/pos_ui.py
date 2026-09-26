from __future__ import annotations
from tkinter import messagebox
import customtkinter as ctk
from .pos import POSService
from .invoicing import InvoiceService

NAVY='#102A43'; MUTED='#627D98'; BG='#F4F7FA'; WHITE='#FFFFFF'; BLUE='#1769E0'; RED='#C92A2A'; GREEN='#14804A'; AMBER='#B7791F'

class POSFrame(ctk.CTkFrame):
    def __init__(self,parent,db,tenant_id,user_id):
        super().__init__(parent,fg_color=BG,corner_radius=0); self.db=db; self.tenant_id=tenant_id; self.user_id=user_id; self.service=POSService(db.conn); self.cart=[]; self.customer_id=None; self.last_sale=None; self._build(); self.refresh_products()
    def _build(self):
        h=ctk.CTkFrame(self,fg_color='transparent');h.pack(fill='x',padx=30,pady=(24,10));l=ctk.CTkFrame(h,fg_color='transparent');l.pack(side='left');ctk.CTkLabel(l,text='POS / Vendas',font=ctk.CTkFont(size=29,weight='bold'),text_color=NAVY).pack(anchor='w');ctk.CTkLabel(l,text='Venda, cliente, pagamento e baixa de stock numa única operação.',text_color=MUTED).pack(anchor='w')
        self.customer=ctk.CTkComboBox(h,width=260,values=['Consumidor final'],command=self.customer_changed);self.customer.pack(side='right',padx=(8,0));
        self.load_customers()
        body=ctk.CTkFrame(self,fg_color='transparent');body.pack(fill='both',expand=True,padx=30,pady=10);body.grid_columnconfigure(0,weight=3);body.grid_columnconfigure(1,weight=2);body.grid_rowconfigure(1,weight=1)
        self.search=ctk.CTkEntry(body,placeholder_text='Pesquisar produto, SKU ou código de barras',height=42);self.search.grid(row=0,column=0,sticky='ew',padx=(0,10),pady=(0,10));self.search.bind('<KeyRelease>',lambda _:self.refresh_products());ctk.CTkButton(body,text='Limpar pesquisa',width=110,command=lambda:(self.search.delete(0,'end'),self.refresh_products())).grid(row=0,column=0,sticky='e',padx=(0,18),pady=(0,10))
        ctk.CTkLabel(body,text='Carrinho',font=ctk.CTkFont(size=18,weight='bold'),text_color=NAVY).grid(row=0,column=1,sticky='w',pady=(0,10))
        self.products=ctk.CTkScrollableFrame(body,fg_color=WHITE,corner_radius=14);self.products.grid(row=1,column=0,sticky='nsew',padx=(0,10));
        right=ctk.CTkFrame(body,fg_color=WHITE,corner_radius=14);right.grid(row=1,column=1,sticky='nsew');right.grid_rowconfigure(0,weight=1);right.grid_columnconfigure(0,weight=1)
        self.cartbox=ctk.CTkScrollableFrame(right,fg_color='transparent');self.cartbox.grid(row=0,column=0,sticky='nsew',padx=12,pady=12)
        summary=ctk.CTkFrame(right,fg_color='#F4F7FA',corner_radius=10);summary.grid(row=1,column=0,sticky='ew',padx=12,pady=8);self.total=ctk.CTkLabel(summary,text='0,00 MT',font=ctk.CTkFont(size=25,weight='bold'),text_color=NAVY);self.total.pack(anchor='e',padx=15,pady=(10,0));self.vat_label=ctk.CTkLabel(summary,text='IVA: 0,00 MT',text_color=MUTED);self.vat_label.pack(anchor='e',padx=15,pady=(0,10))
        self.method=ctk.CTkOptionMenu(right,values=['Dinheiro','M-Pesa','Cartão'],height=40);self.method.grid(row=2,column=0,padx=12,pady=5,sticky='ew')
        ctk.CTkButton(right,text='FINALIZAR VENDA',height=48,fg_color=GREEN,hover_color='#0D683C',font=ctk.CTkFont(size=14,weight='bold'),command=self.finish).grid(row=3,column=0,padx=12,pady=(6,8),sticky='ew')
        self.print_btn=ctk.CTkButton(right,text='A4 / POS da última venda',height=38,fg_color='#E8EEF7',text_color=NAVY,command=self.print_last,state='disabled');self.print_btn.grid(row=4,column=0,padx=12,pady=(0,14),sticky='ew')
    def load_customers(self):
        self.customer_map={'Consumidor final':None};rows=self.db.conn.execute('SELECT id,name FROM customers WHERE tenant_id=? ORDER BY name COLLATE NOCASE',(self.tenant_id,)).fetchall();
        for r in rows:self.customer_map[f"{r['name']}"] = r['id']
        self.customer.configure(values=list(self.customer_map.keys()));self.customer.set('Consumidor final')
    def customer_changed(self,name):self.customer_id=self.customer_map.get(name)
    def refresh_products(self):
        if not hasattr(self,'products'):return
        for w in self.products.winfo_children():w.destroy()
        rows=self.service.products(self.tenant_id,self.search.get())
        if not rows:ctk.CTkLabel(self.products,text='Nenhum produto encontrado.',text_color=MUTED).pack(pady=45);return
        for p in rows:
            available=float(p['available']);card=ctk.CTkFrame(self.products,fg_color='#F8FAFC',corner_radius=10);card.pack(fill='x',pady=5,padx=4)
            info=ctk.CTkFrame(card,fg_color='transparent');info.pack(side='left',fill='x',expand=True);ctk.CTkLabel(info,text=p['name'],font=ctk.CTkFont(size=14,weight='bold'),text_color=NAVY).pack(anchor='w',padx=14,pady=(10,1));ctk.CTkLabel(info,text=f"SKU {p['sku'] or '-'}  •  {float(p['sale_price']):.2f} MT  •  disponível {available:g}",text_color=MUTED).pack(anchor='w',padx=14,pady=(0,10))
            b=ctk.CTkButton(card,text='Adicionar',width=90,command=lambda x=p:self.add(x));b.pack(side='right',padx=10,pady=12);b.configure(state='disabled' if available<=0 else 'normal')
    def add(self,p):
        for item in self.cart:
            if item['product_id']==p['id']:
                if item['quantity']+1>float(p['available']):return messagebox.showwarning('Stock insuficiente',f"Não existem unidades suficientes de {p['name']}.",parent=self)
                item['quantity']+=1;self.refresh_cart();return
        if float(p['available'])<=0:return
        self.cart.append({'product_id':p['id'],'name':p['name'],'quantity':1,'available':float(p['available']),'price':float(p['sale_price'])});self.refresh_cart()
    def refresh_cart(self):
        for w in self.cartbox.winfo_children():w.destroy()
        total=vat=0
        for i,item in enumerate(self.cart):
            line=item['price']*item['quantity'];total+=line
            row=self.db.conn.execute('SELECT vat_rate FROM products WHERE id=?',(item['product_id'],)).fetchone();vat+=line*float(row['vat_rate'])/(100+float(row['vat_rate']))
            c=ctk.CTkFrame(self.cartbox,fg_color='#F8FAFC',corner_radius=10);c.pack(fill='x',pady=4);ctk.CTkLabel(c,text=item['name'],font=ctk.CTkFont(weight='bold'),text_color=NAVY).pack(anchor='w',padx=12,pady=(9,0));ctk.CTkLabel(c,text=f"{item['quantity']} × {item['price']:.2f} MT = {line:.2f} MT",text_color=MUTED).pack(side='left',padx=12,pady=(0,9));ctk.CTkButton(c,text='−',width=30,height=27,command=lambda n=i:self.change_qty(n,-1)).pack(side='right',padx=3,pady=8);ctk.CTkButton(c,text='+',width=30,height=27,command=lambda n=i:self.change_qty(n,1)).pack(side='right',padx=3,pady=8)
        self.total.configure(text=f'{total:,.2f} MT'.replace(',','X').replace('.',',').replace('X','.'));self.vat_label.configure(text=f'IVA: {vat:,.2f} MT'.replace(',','X').replace('.',',').replace('X','.'))
    def change_qty(self,i,delta):
        item=self.cart[i];new=item['quantity']+delta
        if new>item['available']:return messagebox.showwarning('Stock insuficiente','A quantidade excede o stock disponível.',parent=self)
        if new<=0:self.cart.pop(i)
        else:item['quantity']=new
        self.refresh_cart()
    def finish(self):
        try:
            if not self.cart:return messagebox.showwarning('Venda','Adicione pelo menos um produto.',parent=self)
            result=self.service.complete_sale(self.tenant_id,self.user_id,self.cart,self.method.get(),self.customer_id);self.last_sale=result;self.cart=[];self.refresh_cart();self.refresh_products();self.print_btn.configure(state='normal');
            messagebox.showinfo('Venda concluída',f"{result['number']}\nTotal: {result['total']:.2f} MT\nPagamento: {self.method.get()}",parent=self)
        except Exception as exc:messagebox.showerror('Não foi possível concluir',str(exc),parent=self)
    def print_last(self):
        if not self.last_sale:return
        try:
            a4=InvoiceService(self.db.conn).pdf(self.tenant_id,self.last_sale['id'],False);pos=InvoiceService(self.db.conn).pdf(self.tenant_id,self.last_sale['id'],True);messagebox.showinfo('Documentos prontos',f'A4:\n{a4}\n\nPOS:\n{pos}',parent=self)
        except Exception as e:messagebox.showerror('Facturação',str(e),parent=self)
