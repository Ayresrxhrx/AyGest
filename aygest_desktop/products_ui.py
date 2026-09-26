from __future__ import annotations
from tkinter import messagebox, ttk
import customtkinter as ctk
from .inventory import InventoryService
NAVY='#102A43'; MUTED='#627D98'; BG='#F4F7FA'; WHITE='#FFFFFF'; RED='#C92A2A'
class ProductsFrame(ctk.CTkFrame):
    def __init__(self,parent,db,tenant_id):
        super().__init__(parent,fg_color=BG,corner_radius=0);self.db,self.tenant_id=db,tenant_id;self.service=InventoryService(db.conn);self._build();self.refresh()
    def _build(self):
        h=ctk.CTkFrame(self,fg_color='transparent');h.pack(fill='x',padx=32,pady=(25,10));l=ctk.CTkFrame(h,fg_color='transparent');l.pack(side='left');ctk.CTkLabel(l,text='Produtos e Stock',font=ctk.CTkFont(size=29,weight='bold'),text_color=NAVY).pack(anchor='w');ctk.CTkLabel(l,text='Catálogo, preços, stock disponível e movimentos.',text_color=MUTED).pack(anchor='w');ctk.CTkButton(h,text='+ Novo produto',width=145,height=40,command=self.new_product).pack(side='right')
        bar=ctk.CTkFrame(self,fg_color=WHITE,corner_radius=13);bar.pack(fill='x',padx=32,pady=(0,12));self.search=ctk.CTkEntry(bar,placeholder_text='Pesquisar por nome, SKU ou código de barras',height=40);self.search.pack(side='left',fill='x',expand=True,padx=12,pady=11);self.search.bind('<KeyRelease>',lambda _:self.refresh());self.category=ctk.CTkComboBox(bar,values=['Todas'],width=150,command=lambda _:self.refresh());self.category.pack(side='left',padx=5);ctk.CTkButton(bar,text='Entrada',width=90,command=lambda:self.adjust('IN')).pack(side='left',padx=4);ctk.CTkButton(bar,text='Saída',width=90,fg_color=RED,hover_color='#A61B1B',command=lambda:self.adjust('OUT')).pack(side='left',padx=(4,12))
        wrap=ctk.CTkFrame(self,fg_color=WHITE,corner_radius=14);wrap.pack(fill='both',expand=True,padx=32,pady=(0,25));self.tree=ttk.Treeview(wrap,columns=('sku','name','category','unit','cost','price','stock','reserved','available','min'),show='headings');cols=[('sku','SKU',100),('name','Produto',230),('category','Categoria',125),('unit','Un.',60),('cost','Custo',90),('price','Venda',90),('stock','Stock',80),('reserved','Reservado',90),('available','Disponível',95),('min','Mín.',70)];
        for c,t,w in cols:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor='e' if c in ('cost','price','stock','reserved','available','min') else 'w')
        self.tree.pack(fill='both',expand=True,padx=12,pady=12);self.tree.bind('<Double-1>',lambda _:self.edit_selected());self.tree.tag_configure('low',foreground='#B42318');self.tree.tag_configure('normal',foreground=NAVY);self.summary=ctk.CTkLabel(self,text='',text_color=MUTED);self.summary.pack(anchor='w',padx=32,pady=(0,15))
    def refresh(self):
        for i in self.tree.get_children():self.tree.delete(i)
        q=self.search.get().strip().lower();sel=self.category.get();rows=self.service.list_products(self.tenant_id);cats=sorted({p['category'] for p in rows if p['category']});self.category.configure(values=['Todas']+cats);shown=0
        for p in rows:
            if q and q not in f"{p['name']} {p['sku']} {p['barcode'] or ''}".lower():continue
            if sel!='Todas' and (p['category'] or '')!=sel:continue
            tag='low' if p['available']<=p['min_stock'] else 'normal';self.tree.insert('','end',iid=p['id'],values=(p['sku'],p['name'],p['category'] or '—',p['unit'],f"{p['purchase_price']:.2f} MT",f"{p['sale_price']:.2f} MT",f"{p['quantity']:.2f}",f"{p['reserved']:.2f}",f"{p['available']:.2f}",f"{p['min_stock']:.2f}"),tags=(tag,));shown+=1
        self.summary.configure(text=f'{shown} produto(s) apresentado(s) • Duplo clique para editar')
    def selected_id(self):
        s=self.tree.selection();return s[0] if s else None
    def edit_selected(self):
        pid=self.selected_id()
        if not pid:return
        self.new_product(self.db.conn.execute('SELECT * FROM products WHERE id=? AND tenant_id=?',(pid,self.tenant_id)).fetchone())
    def new_product(self,row=None):
        w=ctk.CTkToplevel(self);w.title('Editar produto' if row else 'Novo produto');w.geometry('620x760');w.minsize(570,680);w.grab_set();w.configure(fg_color=BG);ctk.CTkLabel(w,text='Editar produto' if row else 'Novo produto',font=ctk.CTkFont(size=24,weight='bold'),text_color=NAVY).pack(anchor='w',padx=28,pady=(22,2));ctk.CTkLabel(w,text='Dados comerciais, preços e controlo de stock.',text_color=MUTED).pack(anchor='w',padx=28,pady=(0,15));form=ctk.CTkScrollableFrame(w,fg_color=BG);form.pack(fill='both',expand=True,padx=10)
        fields=[('Nome do produto','name'),('SKU','sku'),('Código de barras','barcode'),('Categoria','category'),('Unidade','unit'),('Factor base','factor'),('Preço de compra','purchase_price'),('Preço de venda','sale_price'),('IVA (%)','vat_rate'),('Stock mínimo','min_stock')];es={}
        for label,key in fields:ctk.CTkLabel(form,text=label,text_color=NAVY,font=ctk.CTkFont(size=11,weight='bold')).pack(anchor='w',padx=18,pady=(9,3));e=ctk.CTkEntry(form,height=40);e.pack(fill='x',padx=18);es[key]=e
        if row:
            for _,key in fields:es[key].insert(0,str(row[key] if row[key] is not None else ''))
        else:
            for k,v in {'unit':'UN','factor':'1','purchase_price':'0','sale_price':'0','vat_rate':'16','min_stock':'0'}.items():es[k].insert(0,v)
        f=ctk.CTkFrame(w,fg_color=WHITE);f.pack(fill='x');ctk.CTkButton(f,text='Cancelar',fg_color='#E8EEF7',text_color=NAVY,command=w.destroy).pack(side='right',padx=5,pady=16);ctk.CTkButton(f,text='Guardar produto',height=42,command=lambda:self.save_product(w,row,es)).pack(side='right',padx=5,pady=16)
    def save_product(self,w,row,es):
        try:
            v={k:e.get().strip() for k,e in es.items()};nums={k:float(v[k]) for k in ('factor','purchase_price','sale_price','vat_rate','min_stock')}
            if not v['name'] or not v['sku']:raise ValueError('Nome e SKU são obrigatórios.')
            if row:self.db.conn.execute('UPDATE products SET name=?,sku=?,barcode=?,category=?,unit=?,factor=?,purchase_price=?,sale_price=?,vat_rate=?,min_stock=? WHERE id=? AND tenant_id=?',(v['name'],v['sku'],v['barcode'],v['category'],v['unit'],nums['factor'],nums['purchase_price'],nums['sale_price'],nums['vat_rate'],nums['min_stock'],row['id'],self.tenant_id))
            else:self.service.create_product(self.tenant_id,v['name'],v['sku'],v['barcode'],v['category'],v['unit'],nums['factor'],nums['purchase_price'],nums['sale_price'],nums['vat_rate'],nums['min_stock'])
            self.db.conn.commit();w.destroy();self.refresh()
        except Exception as e:messagebox.showerror('Produto',str(e),parent=w)
    def adjust(self,kind):
        pid=self.selected_id()
        if not pid:return messagebox.showwarning('Stock','Seleccione um produto primeiro.',parent=self)
        w=ctk.CTkToplevel(self);w.title('Entrada de stock' if kind=='IN' else 'Saída de stock');w.geometry('460x300');w.grab_set();ctk.CTkLabel(w,text='Entrada de stock' if kind=='IN' else 'Saída de stock',font=ctk.CTkFont(size=22,weight='bold'),text_color=NAVY).pack(anchor='w',padx=28,pady=25);e=ctk.CTkEntry(w,placeholder_text='Quantidade');e.pack(fill='x',padx=28,pady=8);ctk.CTkLabel(w,text='A operação é registada directamente no stock.',text_color=MUTED).pack(anchor='w',padx=28,pady=5)
        def save():
            try:self.service.adjust_stock(self.tenant_id,pid,float(e.get()),kind);w.destroy();self.refresh()
            except Exception as ex:messagebox.showerror('Stock',str(ex),parent=w)
        ctk.CTkButton(w,text='Confirmar movimento',height=42,command=save).pack(fill='x',padx=28,pady=22)
