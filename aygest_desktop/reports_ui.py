from __future__ import annotations
from datetime import datetime, timezone, timedelta
import csv
from tkinter import filedialog, messagebox
import customtkinter as ctk
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from .reports import ReportService

NAVY='#102A43'; MUTED='#627D98'; BG='#F4F7FA'; WHITE='#FFFFFF'; BLUE='#1769E0'; GREEN='#14804A'; RED='#C92A2A'; AMBER='#B7791F'
def money(v): return f'{float(v or 0):,.2f} MT'.replace(',','X').replace('.',',').replace('X','.')

class ReportsFrame(ctk.CTkFrame):
    def __init__(self,parent,db,tenant_id):
        super().__init__(parent,fg_color=BG,corner_radius=0);self.db=db;self.tenant_id=tenant_id;self.service=ReportService(db.conn);self.build();self.refresh()
    def build(self):
        h=ctk.CTkFrame(self,fg_color='transparent');h.pack(fill='x',padx=32,pady=(24,10));l=ctk.CTkFrame(h,fg_color='transparent');l.pack(side='left');ctk.CTkLabel(l,text='Relatórios',font=ctk.CTkFont(size=30,weight='bold'),text_color=NAVY).pack(anchor='w');ctk.CTkLabel(l,text='Análise comercial, financeira, stock e desempenho operacional.',text_color=MUTED).pack(anchor='w')
        ctk.CTkButton(h,text='Exportar PDF',height=38,command=self.export_pdf).pack(side='right',padx=4);ctk.CTkButton(h,text='Exportar CSV',height=38,command=self.export_csv).pack(side='right',padx=4)
        filters=ctk.CTkFrame(self,fg_color=WHITE,corner_radius=13);filters.pack(fill='x',padx=32,pady=(0,14));ctk.CTkLabel(filters,text='Período',text_color=MUTED).pack(side='left',padx=(15,5),pady=12);self.period=ctk.CTkComboBox(filters,values=['Este mês','Últimos 30 dias','Últimos 90 dias','Este ano'],width=150,command=lambda _:self.refresh());self.period.set('Este mês');self.period.pack(side='left',pady=10)
        self.cards=ctk.CTkFrame(self,fg_color='transparent');self.cards.pack(fill='x',padx=32,pady=(0,15));self.labels=[]
        for title in ['Vendas','Compras','IVA','Margem bruta','N.º vendas']:
            c=ctk.CTkFrame(self.cards,fg_color=WHITE,corner_radius=14);c.pack(side='left',fill='x',expand=True,padx=4);ctk.CTkLabel(c,text=title,font=ctk.CTkFont(size=11,weight='bold'),text_color=MUTED).pack(anchor='w',padx=18,pady=(16,3));x=ctk.CTkLabel(c,text='0,00 MT',font=ctk.CTkFont(size=20,weight='bold'),text_color=NAVY);x.pack(anchor='w',padx=18,pady=(0,16));self.labels.append(x)
        body=ctk.CTkScrollableFrame(self,fg_color='transparent');body.pack(fill='both',expand=True,padx=32,pady=(0,20));self.panels=[]
        for title in ['Vendas por dia','Produtos mais vendidos','Métodos de pagamento','Stock crítico']:
            p=ctk.CTkFrame(body,fg_color=WHITE,corner_radius=14);p.pack(fill='x',pady=6);ctk.CTkLabel(p,text=title,font=ctk.CTkFont(size=18,weight='bold'),text_color=NAVY).pack(anchor='w',padx=20,pady=(17,5));f=ctk.CTkFrame(p,fg_color='#F8FAFC',corner_radius=10);f.pack(fill='x',padx=15,pady=(0,15));self.panels.append(f)
    def dates(self):
        now=datetime.now(timezone.utc);p=self.period.get()
        if p=='Últimos 30 dias':start=now-timedelta(days=30)
        elif p=='Últimos 90 dias':start=now-timedelta(days=90)
        elif p=='Este ano':start=now.replace(month=1,day=1,hour=0,minute=0,second=0,microsecond=0)
        else:start=now.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
        return start.isoformat(),now.isoformat()
    def clear(self):
        for p in self.panels:
            for w in p.winfo_children():w.destroy()
    def refresh(self):
        if not hasattr(self,'panels'):return
        start,end=self.dates();s=self.service.sales(self.tenant_id,start,end);p=self.service.purchases(self.tenant_id,start,end);vals=[s['total'],p['total'],s['vat'],s['total']-p['total'],s['count']]
        for lab,val in zip(self.labels,vals):lab.configure(text=str(val) if lab==self.labels[-1] else money(val))
        self.clear(); any_data=False
        for r in self.service.daily_sales(self.tenant_id,start,end):self.row(self.panels[0],f"{r['day']}  •  {r['count']} venda(s)",money(r['total']));any_data=True
        for r in self.service.top_products(self.tenant_id,start,end):self.row(self.panels[1],f"{r['product_name']}  •  {r['quantity']:.2f} un.",money(r['total']));any_data=True
        for r in self.service.payments(self.tenant_id,start,end):self.row(self.panels[2],f"{r['payment_method']}  •  {r['count']} venda(s)",money(r['total']));any_data=True
        for r in self.service.low_stock(self.tenant_id):self.row(self.panels[3],f"{r['name']}  •  {r['sku']}",f"Disponível: {float(r['quantity'])-float(r['reserved']):.2f} / Mín.: {float(r['min_stock']):.2f}",RED);any_data=True
        if not any_data:ctk.CTkLabel(self.panels[0],text='Sem dados para o período seleccionado.',text_color=MUTED).pack(pady=20)
    def row(self,parent,left,right,color=NAVY):
        c=ctk.CTkFrame(parent,fg_color=WHITE,corner_radius=7);c.pack(fill='x',padx=7,pady=3);ctk.CTkLabel(c,text=left,text_color=NAVY).pack(side='left',padx=14,pady=9);ctk.CTkLabel(c,text=right,text_color=color,font=ctk.CTkFont(weight='bold')).pack(side='right',padx=14)
    def export_csv(self):
        path=filedialog.asksaveasfilename(title='Exportar relatório',defaultextension='.csv',filetypes=[('CSV','*.csv')],initialfile='aygest_relatorio.csv')
        if not path:return
        start,end=self.dates();s=self.service.sales(self.tenant_id,start,end);p=self.service.purchases(self.tenant_id,start,end)
        with open(path,'w',newline='',encoding='utf-8-sig') as f:
            w=csv.writer(f,delimiter=';');w.writerow(['AyGest - Relatório']);w.writerow(['Período',start,end]);w.writerow([]);w.writerow(['Indicador','Valor']);w.writerow(['Vendas',s['total']]);w.writerow(['Compras',p['total']]);w.writerow(['IVA',s['vat']]);w.writerow(['Margem bruta',s['total']-p['total']]);w.writerow(['Número de vendas',s['count']]);w.writerow([]);w.writerow(['Produto','Quantidade','Total'])
            for r in self.service.top_products(self.tenant_id,start,end):w.writerow([r['product_name'],r['quantity'],r['total']])
        messagebox.showinfo('Relatórios',f'Relatório exportado em:\n{path}',parent=self)
    def export_pdf(self):
        path=filedialog.asksaveasfilename(title='Exportar relatório PDF',defaultextension='.pdf',filetypes=[('PDF','*.pdf')],initialfile='aygest_relatorio.pdf')
        if not path:return
        start,end=self.dates();s=self.service.sales(self.tenant_id,start,end);p=self.service.purchases(self.tenant_id,start,end);styles=getSampleStyleSheet();title=ParagraphStyle('AyTitle',parent=styles['Title'],textColor=colors.HexColor('#102A43'),spaceAfter=8);small=ParagraphStyle('AySmall',parent=styles['Normal'],textColor=colors.HexColor('#627D98'));story=[Paragraph('AyGest — Relatório de Gestão',title),Paragraph(f'Período: {start[:10]} até {end[:10]}',small),Spacer(1,16)]
        summary=[['Indicador','Valor'],['Vendas',money(s['total'])],['Compras',money(p['total'])],['IVA',money(s['vat'])],['Margem bruta',money(s['total']-p['total'])],['Número de vendas',str(s['count'])]];t=Table(summary,colWidths=[270,220]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#102A43')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#DCE5EE')),('ALIGN',(1,1),(1,-1),'RIGHT'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F5F8FB')]),('PADDING',(0,0),(-1,-1),8)]));story.append(t);story.append(Spacer(1,18));story.append(Paragraph('Produtos mais vendidos',styles['Heading2']));data=[['Produto','Quantidade','Total']]
        for r in self.service.top_products(self.tenant_id,start,end):data.append([str(r['product_name']),f"{float(r['quantity']):.2f}",money(r['total'])])
        if len(data)==1:data.append(['Sem vendas no período','—','0,00 MT'])
        t=Table(data,colWidths=[300,100,90],repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1769E0')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('GRID',(0,0),(-1,-1),0.35,colors.HexColor('#DCE5EE')),('ALIGN',(1,1),(-1,-1),'RIGHT'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F8FAFC')]),('PADDING',(0,0),(-1,-1),7)]));story.append(t);SimpleDocTemplate(path,pagesize=A4,rightMargin=36,leftMargin=36,topMargin=40,bottomMargin=40,title='AyGest - Relatório de Gestão').build(story);messagebox.showinfo('Relatórios','Relatório PDF exportado com sucesso.',parent=self)
