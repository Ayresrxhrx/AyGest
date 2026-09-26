from __future__ import annotations
from tkinter import messagebox
import customtkinter as ctk
from .pos import POSService

class POSFrame(ctk.CTkFrame):
    def __init__(self,parent,db,tenant_id,user_id):
        super().__init__(parent,fg_color='#F5F7FA',corner_radius=0); self.db=db; self.tenant_id=tenant_id; self.user_id=user_id; self.service=POSService(db.conn); self.cart=[]; self._build(); self.refresh_products()
    def _build(self):
        ctk.CTkLabel(self,text='POS / Vendas',font=ctk.CTkFont(size=28,weight='bold'),text_color='#102A43').pack(anchor='w',padx=32,pady=(28,5))
        ctk.CTkLabel(self,text='Venda rápida com controlo de stock em tempo real',text_color='#627D98').pack(anchor='w',padx=32)
        body=ctk.CTkFrame(self,fg_color='transparent'); body.pack(fill='both',expand=True,padx=32,pady=20); body.grid_columnconfigure(0,weight=3); body.grid_columnconfigure(1,weight=2); body.grid_rowconfigure(1,weight=1)
        self.search=ctk.CTkEntry(body,placeholder_text='Pesquisar produto, SKU ou código de barras',height=42); self.search.grid(row=0,column=0,sticky='ew',padx=(0,10),pady=(0,12)); self.search.bind('<KeyRelease>',lambda e:self.refresh_products())
        ctk.CTkLabel(body,text='Carrinho',font=ctk.CTkFont(size=18,weight='bold'),text_color='#102A43').grid(row=0,column=1,sticky='w',pady=(0,12))
        self.products=ctk.CTkScrollableFrame(body,fg_color='white'); self.products.grid(row=1,column=0,sticky='nsew',padx=(0,10))
        right=ctk.CTkFrame(body,fg_color='white',corner_radius=14); right.grid(row=1,column=1,sticky='nsew'); right.grid_rowconfigure(0,weight=1); right.grid_columnconfigure(0,weight=1)
        self.cartbox=ctk.CTkScrollableFrame(right,fg_color='transparent'); self.cartbox.grid(row=0,column=0,sticky='nsew',padx=12,pady=12)
        self.total=ctk.CTkLabel(right,text='Total: 0,00 MT',font=ctk.CTkFont(size=24,weight='bold'),text_color='#102A43'); self.total.grid(row=1,column=0,padx=20,pady=10,sticky='e')
        self.method=ctk.CTkOptionMenu(right,values=['Dinheiro','M-Pesa','Cartão']); self.method.grid(row=2,column=0,padx=20,pady=8,sticky='ew')
        ctk.CTkButton(right,text='FINALIZAR VENDA',height=48,font=ctk.CTkFont(size=14,weight='bold'),command=self.finish).grid(row=3,column=0,padx=20,pady=(8,20),sticky='ew')
    def refresh_products(self):
        if not hasattr(self,'products'): return
        for w in self.products.winfo_children(): w.destroy()
        for p in self.service.products(self.tenant_id,self.search.get()):
            card=ctk.CTkFrame(self.products,fg_color='#F8FAFC',corner_radius=10); card.pack(fill='x',pady=5)
            ctk.CTkLabel(card,text=p['name'],font=ctk.CTkFont(size=14,weight='bold'),text_color='#102A43').pack(side='left',padx=14,pady=12)
            ctk.CTkLabel(card,text=f"{p['sale_price']:.2f} MT · disponível {p['available']:.2f}",text_color='#627D98').pack(side='left',padx=8)
            ctk.CTkButton(card,text='Adicionar',width=90,command=lambda x=p:self.add(x)).pack(side='right',padx=10)
    def add(self,p):
        for item in self.cart:
            if item['product_id']==p['id']: item['quantity']+=1; self.refresh_cart(); return
        self.cart.append({'product_id':p['id'],'name':p['name'],'quantity':1}); self.refresh_cart()
    def refresh_cart(self):
        for w in self.cartbox.winfo_children(): w.destroy()
        total=0
        for i,item in enumerate(self.cart):
            p=self.db.conn.execute('SELECT sale_price FROM products WHERE id=?',(item['product_id'],)).fetchone(); line=float(p['sale_price'])*item['quantity']; total+=line
            ctk.CTkLabel(self.cartbox,text=f"{item['name']}\n{item['quantity']} × {p['sale_price']:.2f} MT = {line:.2f} MT",justify='left').pack(fill='x',pady=6)
            ctk.CTkButton(self.cartbox,text='−',width=35,command=lambda n=i:self.remove(n)).pack(anchor='e')
        self.total.configure(text=f'Total: {total:.2f} MT')
    def remove(self,i):
        self.cart[i]['quantity']-=1
        if self.cart[i]['quantity']<=0: self.cart.pop(i)
        self.refresh_cart()
    def finish(self):
        try:
            result=self.service.complete_sale(self.tenant_id,self.user_id,self.cart,self.method.get()); self.cart=[]; self.refresh_cart(); self.refresh_products(); messagebox.showinfo('Venda concluída',f"Venda {result['number']} registada.\nTotal: {result['total']:.2f} MT")
        except Exception as exc: messagebox.showerror('Não foi possível concluir',str(exc))
