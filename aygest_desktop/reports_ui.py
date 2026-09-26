from __future__ import annotations
import customtkinter as ctk
from .reports import ReportService

class ReportsFrame(ctk.CTkFrame):
    def __init__(self,parent,db,tenant_id):
        super().__init__(parent,fg_color='#F5F7FA',corner_radius=0);self.db=db;self.tenant_id=tenant_id;self.service=ReportService(db.conn);self.build()
    def build(self):
        ctk.CTkLabel(self,text='Relatórios',font=ctk.CTkFont(size=30,weight='bold'),text_color='#102A43').pack(anchor='w',padx=40,pady=(35,2));ctk.CTkLabel(self,text='Indicadores reais da operação do período seleccionado.',text_color='#627D98').pack(anchor='w',padx=40)
        self.cards=ctk.CTkFrame(self,fg_color='transparent');self.cards.pack(fill='x',padx=40,pady=25);self.labels=[]
        for title in ['Vendas','Compras','IVA','Margem bruta']:
            card=ctk.CTkFrame(self.cards,fg_color='white',corner_radius=14);card.pack(side='left',fill='x',expand=True,padx=(0,12));ctk.CTkLabel(card,text=title,font=ctk.CTkFont(size=13,weight='bold'),text_color='#627D98').pack(anchor='w',padx=20,pady=(18,4));lab=ctk.CTkLabel(card,text='0,00 MT',font=ctk.CTkFont(size=24,weight='bold'),text_color='#102A43');lab.pack(anchor='w',padx=20,pady=(0,18));self.labels.append(lab)
        body=ctk.CTkFrame(self,fg_color='white',corner_radius=14);body.pack(fill='both',expand=True,padx=40,pady=(0,30));ctk.CTkLabel(body,text='Resumo mensal',font=ctk.CTkFont(size=19,weight='bold'),text_color='#102A43').pack(anchor='w',padx=25,pady=(22,3));self.period=ctk.CTkLabel(body,text='',text_color='#627D98');self.period.pack(anchor='w',padx=25);self.table=ctk.CTkScrollableFrame(body,fg_color='#F8FAFC');self.table.pack(fill='both',expand=True,padx=20,pady=20);self.refresh()
    def refresh(self):
        data=self.service.monthly(self.tenant_id);self.period.configure(text=f"Período: {data['period']} · {data['sales_count']} vendas");vals=[data['sales_total'],data['purchases_total'],data['vat'],data['gross_margin']]
        for lab,val in zip(self.labels,vals):lab.configure(text=f'{val:,.2f} MT'.replace(',','X').replace('.',',').replace('X','.'))
        for w in self.table.winfo_children():w.destroy()
        ctk.CTkLabel(self.table,text='Stock actual',font=ctk.CTkFont(size=15,weight='bold'),text_color='#102A43').pack(anchor='w',padx=12,pady=10)
        for r in self.service.stock(self.tenant_id):
            row=ctk.CTkFrame(self.table,fg_color='white',corner_radius=8);row.pack(fill='x',pady=3,padx=3);ctk.CTkLabel(row,text=f"{r['name']} · {r['sku']}",font=ctk.CTkFont(weight='bold'),text_color='#102A43').pack(side='left',padx=15,pady=10);ctk.CTkLabel(row,text=f"Stock: {r['quantity']:.2f} | Reservado: {r['reserved']:.2f} | Venda: {r['sale_price']:.2f} MT",text_color='#627D98').pack(side='right',padx=15)
