from __future__ import annotations
from tkinter import messagebox
import customtkinter as ctk
from .reservations import ReservationService, QuotationService

class ReservationsFrame(ctk.CTkFrame):
    def __init__(self,parent,db,tenant_id,user_id):
        super().__init__(parent,fg_color='#F5F7FA',corner_radius=0); self.db=db; self.tenant_id=tenant_id; self.user_id=user_id; self.service=ReservationService(db.conn); self.build(); self.refresh()
    def build(self):
        ctk.CTkLabel(self,text='Reservas de Stock',font=ctk.CTkFont(size=28,weight='bold'),text_color='#102A43').pack(anchor='w',padx=32,pady=(28,5))
        bar=ctk.CTkFrame(self,fg_color='white',corner_radius=12); bar.pack(fill='x',padx=32,pady=20)
        self.product=ctk.CTkEntry(bar,placeholder_text='ID do produto'); self.product.pack(side='left',fill='x',expand=True,padx=12,pady=12)
        self.qty=ctk.CTkEntry(bar,placeholder_text='Quantidade',width=120); self.qty.pack(side='left',padx=5)
        ctk.CTkButton(bar,text='Reservar por 3 dias',command=self.reserve).pack(side='left',padx=12)
        self.list=ctk.CTkScrollableFrame(self,fg_color='white'); self.list.pack(fill='both',expand=True,padx=32,pady=(0,32))
    def refresh(self):
        self.service.expire(self.tenant_id)
        for w in self.list.winfo_children(): w.destroy()
        rows=self.db.conn.execute("SELECT r.id,r.quantity,r.expires_at,r.status,p.name FROM reservations r JOIN products p ON p.id=r.product_id WHERE r.tenant_id=? ORDER BY r.created_at DESC",(self.tenant_id,)).fetchall()
        for r in rows:
            c=ctk.CTkFrame(self.list,fg_color='#F8FAFC',corner_radius=10); c.pack(fill='x',pady=5)
            ctk.CTkLabel(c,text=f"{r['name']} · {r['quantity']:.2f}",font=ctk.CTkFont(weight='bold'),text_color='#102A43').pack(side='left',padx=14,pady=14)
            ctk.CTkLabel(c,text=f"{r['status']} · {r['expires_at']}",text_color='#627D98').pack(side='left')
            if r['status']=='active': ctk.CTkButton(c,text='Libertar',width=80,command=lambda x=r['id']:self.release(x)).pack(side='right',padx=10)
    def reserve(self):
        try: self.service.reserve(self.tenant_id,self.product.get().strip(),float(self.qty.get()),self.user_id); self.refresh()
        except Exception as e: messagebox.showerror('Reserva',str(e))
    def release(self,rid):
        try: self.service.release(self.tenant_id,rid); self.refresh()
        except Exception as e: messagebox.showerror('Reserva',str(e))

class QuotationsFrame(ctk.CTkFrame):
    def __init__(self,parent,db,tenant_id):
        super().__init__(parent,fg_color='#F5F7FA',corner_radius=0); self.db=db; self.tenant_id=tenant_id; self.service=QuotationService(db.conn); self.build(); self.refresh()
    def build(self):
        ctk.CTkLabel(self,text='Cotações',font=ctk.CTkFont(size=28,weight='bold'),text_color='#102A43').pack(anchor='w',padx=32,pady=(28,5))
        ctk.CTkButton(self,text='+ Nova cotação',command=self.new).pack(anchor='e',padx=32,pady=12)
        self.list=ctk.CTkScrollableFrame(self,fg_color='white'); self.list.pack(fill='both',expand=True,padx=32,pady=(0,32))
    def refresh(self):
        for w in self.list.winfo_children(): w.destroy()
        rows=self.db.conn.execute("SELECT * FROM quotations WHERE tenant_id=? ORDER BY created_at DESC",(self.tenant_id,)).fetchall()
        for r in rows:
            c=ctk.CTkFrame(self.list,fg_color='#F8FAFC',corner_radius=10); c.pack(fill='x',pady=5)
            ctk.CTkLabel(c,text=f"{r['document_no']} · {r['total']:.2f} MT",font=ctk.CTkFont(weight='bold'),text_color='#102A43').pack(side='left',padx=14,pady=14)
            ctk.CTkLabel(c,text=f"{r['status']} · {r['expires_at']}",text_color='#627D98').pack(side='left')
            if r['status']=='open': ctk.CTkButton(c,text='Aprovar',width=90,command=lambda x=r['id']:self.approve(x)).pack(side='right',padx=10)
    def new(self):
        win=ctk.CTkToplevel(self); win.title('Nova cotação'); win.geometry('430x220'); ctk.CTkLabel(win,text='Total da cotação').pack(pady=(25,5)); total=ctk.CTkEntry(win); total.pack(padx=30,fill='x'); ctk.CTkButton(win,text='Criar',command=lambda:self.create(win,total)).pack(pady=25)
    def create(self,win,total):
        try: self.service.create(self.tenant_id,None,float(total.get())); win.destroy(); self.refresh()
        except Exception as e: messagebox.showerror('Cotação',str(e),parent=win)
    def approve(self,rid):
        try: self.service.approve(self.tenant_id,rid); self.refresh()
        except Exception as e: messagebox.showerror('Cotação',str(e))
