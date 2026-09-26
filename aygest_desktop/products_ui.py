from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

from .inventory import InventoryService


class ProductsFrame(ctk.CTkFrame):
    def __init__(self, parent, db, tenant_id):
        super().__init__(parent, fg_color="#F5F7FA", corner_radius=0)
        self.db, self.tenant_id = db, tenant_id
        self.service = InventoryService(db.conn)
        self._build()
        self.refresh()

    def _build(self):
        header=ctk.CTkFrame(self,fg_color="transparent"); header.pack(fill="x",padx=32,pady=(28,12))
        ctk.CTkLabel(header,text="Produtos e Stock",font=ctk.CTkFont(size=28,weight="bold"),text_color="#102A43").pack(side="left")
        ctk.CTkButton(header,text="+ Novo produto",width=150,height=40,command=self.new_product).pack(side="right")
        toolbar=ctk.CTkFrame(self,fg_color="white",corner_radius=12); toolbar.pack(fill="x",padx=32,pady=(0,12))
        self.search=ctk.CTkEntry(toolbar,placeholder_text="Pesquisar por nome, SKU ou código de barras",height=38); self.search.pack(side="left",fill="x",expand=True,padx=14,pady=12); self.search.bind("<KeyRelease>",lambda _:self.refresh())
        ctk.CTkButton(toolbar,text="Entrada",width=90,command=lambda:self.adjust("IN")).pack(side="left",padx=5)
        ctk.CTkButton(toolbar,text="Saída",width=90,fg_color="#B42318",hover_color="#912018",command=lambda:self.adjust("OUT")).pack(side="left",padx=(5,14))
        wrap=ctk.CTkFrame(self,fg_color="white",corner_radius=12); wrap.pack(fill="both",expand=True,padx=32,pady=(0,32))
        self.tree=ttk.Treeview(wrap,columns=("sku","name","category","unit","price","stock","reserved","available"),show="headings")
        for c,t,w in [("sku","SKU",120),("name","Produto",250),("category","Categoria",130),("unit","Unidade",80),("price","Preço",100),("stock","Stock",90),("reserved","Reservado",100),("available","Disponível",100)]: self.tree.heading(c,text=t); self.tree.column(c,width=w,anchor="e" if c in ("price","stock","reserved","available") else "w")
        self.tree.pack(fill="both",expand=True,padx=14,pady=14)

    def refresh(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        q=self.search.get().strip().lower() if hasattr(self,"search") else ""
        for p in self.service.list_products(self.tenant_id):
            if q and q not in f"{p['name']} {p['sku']} {p['barcode'] or ''}".lower(): continue
            self.tree.insert("","end",iid=p["id"],values=(p["sku"],p["name"],p["category"] or "—",p["unit"],f"{p['sale_price']:.2f} MT",f"{p['quantity']:.2f}",f"{p['reserved']:.2f}",f"{p['available']:.2f}"))

    def new_product(self):
        win=ctk.CTkToplevel(self); win.title("Novo produto"); win.geometry("520x650"); win.transient(self.winfo_toplevel()); win.grab_set()
        fields=[("Nome",""),("SKU",""),("Código de barras",""),("Categoria",""),("Unidade","UN"),("Factor base","1"),("Preço de compra","0"),("Preço de venda","0"),("IVA %","16"),("Stock mínimo","0")]
        entries=[]
        for label,default in fields:
            ctk.CTkLabel(win,text=label).pack(anchor="w",padx=28,pady=(10,2)); e=ctk.CTkEntry(win); e.insert(0,default); e.pack(fill="x",padx=28); entries.append(e)
        def save():
            try:
                vals=[e.get() for e in entries]; self.service.create_product(self.tenant_id,vals[0],vals[1],vals[2],vals[3],vals[4],float(vals[5]),float(vals[6]),float(vals[7]),float(vals[8]),float(vals[9])); win.destroy(); self.refresh()
            except Exception as exc: messagebox.showerror("Produto",str(exc),parent=win)
        ctk.CTkButton(win,text="Guardar produto",height=42,command=save).pack(fill="x",padx=28,pady=24)

    def adjust(self, kind):
        selected=self.tree.selection()
        if not selected: return messagebox.showwarning("Stock","Seleccione um produto primeiro.")
        dialog=ctk.CTkInputDialog(text="Quantidade:",title="Entrada de stock" if kind=="IN" else "Saída de stock"); value=dialog.get_input()
        try: self.service.adjust_stock(self.tenant_id,selected[0],float(value),kind); self.refresh()
        except Exception as exc: messagebox.showerror("Stock",str(exc))
