from __future__ import annotations
from datetime import datetime, timezone
import customtkinter as ctk
NAVY='#102A43'; MUTED='#627D98'; BG='#F3F6FA'; WHITE='#FFFFFF'; BLUE='#1769E0'; GREEN='#14804A'; RED='#C92A2A'
def money(v): return f"{float(v):,.2f} MT".replace(',','X').replace('.',',').replace('X','.')
class DashboardFrame(ctk.CTkFrame):
    def __init__(self,parent,db,tenant_id,on_navigate=None):
        super().__init__(parent,fg_color=BG,corner_radius=0);self.db=db;self.tenant_id=tenant_id;self.on_navigate=on_navigate;self._build();self.refresh()
    def _build(self):
        head=ctk.CTkFrame(self,fg_color='transparent');head.pack(fill='x',padx=34,pady=(26,12));left=ctk.CTkFrame(head,fg_color='transparent');left.pack(side='left');ctk.CTkLabel(left,text='Visão geral',font=ctk.CTkFont(size=30,weight='bold'),text_color=NAVY).pack(anchor='w');self.period=ctk.CTkLabel(left,text='',font=ctk.CTkFont(size=12),text_color=MUTED);self.period.pack(anchor='w',pady=(2,0));ctk.CTkButton(head,text='+ Nova venda',width=130,height=38,command=lambda:self.go('POS / Vendas')).pack(side='right',padx=5);ctk.CTkButton(head,text='Novo produto',width=130,height=38,fg_color='#E8EEF7',hover_color='#DCE6F3',text_color=NAVY,command=lambda:self.go('Produtos')).pack(side='right',padx=5)
        self.cards=ctk.CTkFrame(self,fg_color='transparent');self.cards.pack(fill='x',padx=34,pady=8);self.card_labels=[]
        for title in ('Vendas do mês','Facturas','Margem estimada','Stock baixo'):
            c=ctk.CTkFrame(self.cards,fg_color=WHITE,corner_radius=16,border_width=1,border_color='#E3EAF2');c.pack(side='left',fill='x',expand=True,padx=(0,12));ctk.CTkLabel(c,text=title,font=ctk.CTkFont(size=12,weight='bold'),text_color=MUTED).pack(anchor='w',padx=20,pady=(17,3));v=ctk.CTkLabel(c,text='0',font=ctk.CTkFont(size=25,weight='bold'),text_color=NAVY);v.pack(anchor='w',padx=20);self.card_labels.append(v);ctk.CTkFrame(c,height=10,fg_color='transparent').pack()
        body=ctk.CTkFrame(self,fg_color='transparent');body.pack(fill='both',expand=True,padx=34,pady=(12,28));body.grid_columnconfigure(0,weight=3);body.grid_columnconfigure(1,weight=2);body.grid_rowconfigure(0,weight=1)
        trend=ctk.CTkFrame(body,fg_color=WHITE,corner_radius=16,border_width=1,border_color='#E3EAF2');trend.grid(row=0,column=0,sticky='nsew',padx=(0,10));ctk.CTkLabel(trend,text='Desempenho de vendas',font=ctk.CTkFont(size=18,weight='bold'),text_color=NAVY).pack(anchor='w',padx=22,pady=(20,2));ctk.CTkLabel(trend,text='Últimos 6 meses',text_color=MUTED).pack(anchor='w',padx=22);self.chart=ctk.CTkCanvas(trend,bg=WHITE,highlightthickness=0);self.chart.pack(fill='both',expand=True,padx=18,pady=15);self.chart.bind('<Configure>',lambda _:self.draw_chart())
        right=ctk.CTkFrame(body,fg_color=WHITE,corner_radius=16,border_width=1,border_color='#E3EAF2');right.grid(row=0,column=1,sticky='nsew');ctk.CTkLabel(right,text='Alertas operacionais',font=ctk.CTkFont(size=18,weight='bold'),text_color=NAVY).pack(anchor='w',padx=20,pady=(20,4));self.alerts=ctk.CTkScrollableFrame(right,fg_color='#F8FAFC',corner_radius=10);self.alerts.pack(fill='both',expand=True,padx=16,pady=(8,16));foot=ctk.CTkFrame(right,fg_color='transparent');foot.pack(fill='x',padx=16,pady=(0,16));ctk.CTkButton(foot,text='Ver stock',command=lambda:self.go('Stock')).pack(side='left',fill='x',expand=True,padx=(0,5));ctk.CTkButton(foot,text='Relatórios',fg_color='#E8EEF7',hover_color='#DCE6F3',text_color=NAVY,command=lambda:self.go('Relatórios')).pack(side='left',fill='x',expand=True,padx=(5,0))
    def go(self,m):
        if self.on_navigate:self.on_navigate(m)
    def refresh(self):
        now=datetime.now(timezone.utc);start=now.replace(day=1,hour=0,minute=0,second=0,microsecond=0);end=datetime(now.year+1,1,1,tzinfo=timezone.utc) if now.month==12 else datetime(now.year,now.month+1,1,tzinfo=timezone.utc);self.period.configure(text=f"Período actual · {start.strftime('%B %Y').title()}");s=self.db.conn.execute("SELECT COUNT(*) n,COALESCE(SUM(total),0) total FROM sales WHERE tenant_id=? AND status='completed' AND created_at>=? AND created_at<?",(self.tenant_id,start.isoformat(),end.isoformat())).fetchone();p=self.db.conn.execute("SELECT COALESCE(SUM(total),0) total FROM purchases WHERE tenant_id=? AND created_at>=? AND created_at<?",(self.tenant_id,start.isoformat(),end.isoformat())).fetchone();low=self.db.conn.execute("SELECT COUNT(*) n FROM products p LEFT JOIN stock s ON s.product_id=p.id AND s.tenant_id=p.tenant_id WHERE p.tenant_id=? AND p.active=1 AND COALESCE(s.quantity,0)-COALESCE(s.reserved,0)<=p.min_stock",(self.tenant_id,)).fetchone();self.card_labels[0].configure(text=money(s['total']));self.card_labels[1].configure(text=str(s['n']));self.card_labels[2].configure(text=money(s['total']-p['total']));self.card_labels[3].configure(text=str(low['n']));self.load_alerts();self.load_trend();self.draw_chart()
    def load_alerts(self):
        for w in self.alerts.winfo_children():w.destroy()
        rows=self.db.conn.execute("SELECT p.name,p.sku,COALESCE(s.quantity,0) qty,p.min_stock FROM products p LEFT JOIN stock s ON s.product_id=p.id AND s.tenant_id=p.tenant_id WHERE p.tenant_id=? AND p.active=1 AND COALESCE(s.quantity,0)-COALESCE(s.reserved,0)<=p.min_stock ORDER BY qty ASC LIMIT 8",(self.tenant_id,)).fetchall()
        if not rows:ctk.CTkLabel(self.alerts,text='Tudo em ordem\nNenhum produto abaixo do mínimo.',text_color=GREEN,font=ctk.CTkFont(weight='bold')).pack(pady=30)
        for r in rows:
            row=ctk.CTkFrame(self.alerts,fg_color=WHITE,corner_radius=10);row.pack(fill='x',pady=4,padx=3);ctk.CTkLabel(row,text=r['name'],font=ctk.CTkFont(weight='bold'),text_color=NAVY).pack(anchor='w',padx=12,pady=(9,0));ctk.CTkLabel(row,text=f"SKU {r['sku']} · Stock {r['qty']:.2f} · Mínimo {r['min_stock']:.2f}",text_color=RED).pack(anchor='w',padx=12,pady=(1,9))
    def load_trend(self):
        self.trend=[];now=datetime.now(timezone.utc)
        for i in range(5,-1,-1):
            y=now.year;m=now.month-i
            while m<=0:m+=12;y-=1
            start=datetime(y,m,1,tzinfo=timezone.utc);end=datetime(y+1,1,1,tzinfo=timezone.utc) if m==12 else datetime(y,m+1,1,tzinfo=timezone.utc);r=self.db.conn.execute("SELECT COALESCE(SUM(total),0) total FROM sales WHERE tenant_id=? AND status='completed' AND created_at>=? AND created_at<?",(self.tenant_id,start.isoformat(),end.isoformat())).fetchone();self.trend.append((start.strftime('%b').title(),float(r['total'])))
    def draw_chart(self):
        if not hasattr(self,'trend') or not self.chart.winfo_exists():return
        self.chart.delete('all');w=max(300,self.chart.winfo_width());h=max(220,self.chart.winfo_height());pad=38;values=[max(0.0,float(v)) for _,v in self.trend];scale=max(max(values,default=0.0),1.0);count=max(1,len(self.trend)-1);self.chart.create_line(pad,h-pad,w-pad,h-pad,fill='#D9E2EC');self.chart.create_line(pad,pad,pad,h-pad,fill='#D9E2EC');pts=[]
        for i,(label,val) in enumerate(self.trend):
            x=pad+i*((w-2*pad)/count);y=h-pad-(max(0.0,float(val))/scale)*(h-2*pad);pts.append((x,y));self.chart.create_oval(x-4,y-4,x+4,y+4,fill=BLUE,outline=BLUE);self.chart.create_text(x,h-18,text=label,fill=MUTED,font=('Segoe UI',9));self.chart.create_text(x,y-13,text=money(val).replace(' MT',''),fill=NAVY,font=('Segoe UI',8,'bold'))
        if len(pts)>1:self.chart.create_line(*[v for p in pts for v in p],fill=BLUE,width=3,smooth=True)
