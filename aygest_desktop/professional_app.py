from __future__ import annotations
import customtkinter as ctk
from .enterprise_app import EnterpriseApp
from .config import settings

NAVY='#0B2239'; BG='#F4F7FA'; MUTED='#627D98'

class ProfessionalApp(EnterpriseApp):
    """Shell principal do AyGest: navegação empresarial sem módulos fora do escopo."""
    def build(self):
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        side=ctk.CTkFrame(self,width=275,fg_color=NAVY,corner_radius=0); side.grid(row=0,column=0,sticky='nsew'); side.grid_propagate(False)
        brand=ctk.CTkFrame(side,fg_color='transparent'); brand.pack(fill='x',padx=22,pady=(22,8))
        ctk.CTkLabel(brand,text='AyGest',font=ctk.CTkFont(size=32,weight='bold'),text_color='white').pack(anchor='w')
        ctk.CTkLabel(brand,text='GESTÃO EMPRESARIAL',font=ctk.CTkFont(size=9,weight='bold'),text_color='#70A5D5').pack(anchor='w')
        ctk.CTkLabel(brand,text=f"{self.user['name']}  •  {self.user['role']}",font=ctk.CTkFont(size=10,weight='bold'),text_color='#DCEAF7').pack(anchor='w',pady=(8,0))
        self.nav=ctk.CTkScrollableFrame(side,fg_color='transparent',scrollbar_button_color='#315675',scrollbar_button_hover_color='#527B9E'); self.nav.pack(fill='both',expand=True,padx=7,pady=(4,5))
        groups=[('PRINCIPAL',['Dashboard','POS / Vendas','Facturação']),('GESTÃO',['Produtos','Stock','Clientes','Fornecedores','Compras']),('FINANCEIRO',['Financeiro','Relatórios']),('ADMINISTRAÇÃO',['Utilizadores','Licenciamento','Configurações','Auditoria','Backup'])]
        self.buttons={}
        for title,items in groups:
            ctk.CTkLabel(self.nav,text=title,font=ctk.CTkFont(size=9,weight='bold'),text_color='#6D8BA5').pack(fill='x',padx=18,pady=(13,5))
            for item in items:
                b=ctk.CTkButton(self.nav,text=item,anchor='w',height=40,corner_radius=8,fg_color='transparent',hover_color='#173D60',text_color='#EAF2F8',command=lambda x=item:self.open(x)); b.pack(fill='x',padx=5,pady=2); self.buttons[item]=b
        ctk.CTkLabel(side,text=f'v{settings.app_version}',text_color='#6D8BA5',font=ctk.CTkFont(size=9)).pack(pady=9)
        self.content=ctk.CTkFrame(self,fg_color=BG,corner_radius=0); self.content.grid(row=0,column=1,sticky='nsew')
        self.status=ctk.CTkLabel(self.content,text='  Pronto',anchor='w',height=25,text_color=MUTED,fg_color='#EAF0F6'); self.status.pack(side='bottom',fill='x')
    def open(self,module):
        super().open(module); self._select(module); self._status(f'{module} carregado')
    def _select(self,module):
        for name,button in self.buttons.items(): button.configure(fg_color='#173D60' if name==module else 'transparent')
    def _status(self,text):
        if self.status.winfo_exists(): self.status.configure(text=f'  {text}')
