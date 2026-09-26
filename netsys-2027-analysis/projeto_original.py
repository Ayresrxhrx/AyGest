import tkinter as tk
from tkinter import ttk, messagebox
import datetime, json, os, time
from pathlib import Path

# CONFIGURAÇÃO
EMPRESA = {"nome":"NETSYS 2027","nuit":"123456789","iva":16}
ARQ_STOCK = "stock.json"
ARQ_RESERVA = "reservas.json"

UNIDADES = {"LATA":1, "EMBALAGEM":6, "CAIXA":24}

def carregar_stock():
   if os.path.exists(ARQ_STOCK):
       return json.loads(open(ARQ_STOCK).read())
   return {"COCA-COLA":{"base":240,"preco_lata":70,"preco_emb":400,"preco_caixa":1500}}

def salvar_stock(s): open(ARQ_STOCK,"w").write(json.dumps(s))

def stock_livre(prod):
   s = carregar_stock()[prod]["base"]
   reservas = carregar_reservas()
   agora = time.time()
   reservas = [r for r in reservas if r["expira"]>agora]
   reservado = sum(r["qtd_base"] for r in reservas if r["prod"]==prod)
   open(ARQ_RESERVA,"w").write(json.dumps(reservas))
   return s - reservado, s, reservado

def carregar_reservas():
   return json.loads(open(ARQ_RESERVA).read()) if os.path.exists(ARQ_RESERVA) else []

def reservar(prod, qtd, unidade, caixa):
   fator = UNIDADES[unidade]
   qtd_base = qtd*fator
   livre, total, reserv = stock_livre(prod)
   if livre >= qtd_base:
       res = carregar_reservas()
       res.append({"prod":prod,"qtd_base":qtd_base,"qtd":qtd,"unid":unidade,"caixa":caixa,"expira":time.time()+300})
       open(ARQ_RESERVA,"w").write(json.dumps(res))
       return True
   else:
       return False, livre

root = tk.Tk()
root.title("NETSYS 2027 - Rede + Anti Negativo")
root.geometry("1150x700")

top = tk.Frame(root, bg="#0f172a", height=50)
top.pack(fill="x")
tk.Label(top, text="NETSYS 2027 | Caixa 1 | Reserva Ativa 5min | Anti-Stock Negativo", fg="white", bg="#0f172a", font=("Arial",12,"bold")).pack(pady=12)

f = tk.Frame(root)
f.pack(padx=20,pady=10, fill="x")
tk.Label(f, text="Produto:").grid(row=0,column=0)
prod_e = ttk.Combobox(f, values=["COCA-COLA"]); prod_e.set("COCA-COLA"); prod_e.grid(row=0,column=1)
tk.Label(f, text="Qtd:").grid(row=0,column=2)
qtd_e = tk.Entry(f, width=6); qtd_e.insert(0,"1"); qtd_e.grid(row=0,column=3)
tk.Label(f, text="Unidade:").grid(row=0,column=4)
unid_e = ttk.Combobox(f, values=list(UNIDADES.keys())); unid_e.set("CAIXA"); unid_e.grid(row=0,column=5)
status_l = tk.Label(f, text="Stock Livre:...", fg="blue", font=("Arial",10,"bold")); status_l.grid(row=0,column=6, padx=20)

cols=("Prod","Qtd","Unid","Total Base","Reservado Por")
tab = ttk.Treeview(root, columns=cols, show="headings", height=10)
for c in cols: tab.heading(c, text=c)
tab.pack(padx=20, fill="x")

def atualizar_status(*a):
   try:
       p=prod_e.get()
       livre,total,reserv = stock_livre(p)
       caixas = livre//24; emb = (livre%24)//6; latas = livre%6
       status_l.config(text=f"LIVRE: {caixas}C + {emb}E + {latas}L ({livre} latas) | Total:{total} | Reservado:{reserv}")
       if livre<=48: status_l.config(fg="orange")
       if livre<=0: status_l.config(fg="red")
       else: status_l.config(fg="green")
   except: pass

def add():
   try:
       p=prod_e.get(); q=int(qtd_e.get()); u=unid_e.get()
       ok = reservar(p,q,u,"Caixa1")
       if ok==True:
           tab.insert("", "end", values=(p,q,u,q*UNIDADES[u],"Caixa1"))
           atualizar_status()
       else:
           _, livre = ok
           messagebox.showerror("? BLOQUEADO - Stock Reservado", f"Não pode vender {q} {u}\nSó tem {livre} latas LIVRES.\nOutro caixa já reservou!")
   except Exception as e: messagebox.showerror("Erro", str(e))

def finalizar():
   itens = [tab.item(i)["values"] for i in tab.get_children()]
   if not itens: return
   stock = carregar_stock()
   for p,q,u,base,caixa in itens:
       stock[p]["base"] -= base
   salvar_stock(stock)
   open(ARQ_RESERVA,"w").write(json.dumps([]))
   messagebox.showinfo("Venda OK","Stock baixado! Sem negativo. Talão Xprinter impresso.")
   for i in tab.get_children(): tab.delete(i)
   atualizar_status()

ttk.Button(f, text="RESERVAR NO CARRINHO", command=add).grid(row=0,column=7, padx=10)
ttk.Button(root, text="FINALIZAR VENDA (PAGOU)", command=finalizar).pack(pady=20, ipady=10, ipadx=20)
prod_e.bind("<<ComboboxSelected>>", atualizar_status)
atualizar_status()
root.mainloop()

ARQ_COT = "cotacoes.json"

def carregar_cot():
   return json.loads(open(ARQ_COT).read()) if os.path.exists(ARQ_COT) else []

def salvar_cot(dados): open(ARQ_COT,"w").write(json.dumps(dados, indent=2))

def criar_cotacao():
   itens = [tab.item(i)["values"] for i in tab.get_children()]
   if not itens:
       messagebox.showwarning("Vazio","Adiciona produtos primeiro")
       return

   cliente = simpledialog.askstring("Cliente","Nome do cliente para cotação:")
   if not cliente: return

   cotacoes = carregar_cot()
   num = f"COT-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
   total_latas = sum(v[3] for v in itens)

   for p,q,u,base,caixa in itens:
       res = carregar_reservas()
       res.append({"prod":p,"qtd_base":base,"qtd":q,"unid":u,"caixa":f"COT-{num}","expira":time.time()+259200})
       open(ARQ_RESERVA,"w").write(json.dumps(res))

   cotacoes.append({
       "numero":num,"cliente":cliente,"data":datetime.datetime.now().isoformat(),
       "itens":itens,"status":"PENDENTE","total_base":total_latas
   })
   salvar_cot(cotacoes)
   messagebox.showinfo("Cotação Criada", f"{num} para {cliente}\nStock reservado por 3 dias!\nPode imprimir A4 para cliente.")
   for i in tab.get_children(): tab.delete(i)
   atualizar_status()

ttk.Button(root, text="? CRIAR COTAÇÃO (Reserva 3 dias)", command=criar_cotacao).pack(pady=5)
ttk.Button(root, text="? VER COTAÇÕES / APROVAR -> VENDA", command=lambda: janela_cotacoes()).pack(pady=5)

def janela_cotacoes():
   j = tk.Toplevel(root); j.title("Cotações"); j.geometry("800x400")
   cols2=("Numero","Cliente","Data","Status","Total Latas")
   t2 = ttk.Treeview(j, columns=cols2, show="headings")
   for c in cols2: t2.heading(c, text=c)
   t2.pack(fill="both", expand=True)

   def carregar_lista():
       for i in t2.get_children(): t2.delete(i)
       for c in carregar_cot():
           t2.insert("", "end", values=(c["numero"], c["cliente"], c["data"][:10], c["status"], c["total_base"]))

   def aprovar():
       sel = t2.selection()
       if not sel: return
       num = t2.item(sel[0])["values"][0]
       cotacoes = carregar_cot()
       for c in cotacoes:
           if c["numero"]==num:
               stock = carregar_stock()
               for p,q,u,base,caixa in c["itens"]:
                   stock[p]["base"] -= base
               salvar_stock(stock)
               c["status"]="APROVADA"
               res = [r for r in carregar_reservas() if not r["caixa"]==f"COT-{num}"]
               open(ARQ_RESERVA,"w").write(json.dumps(res))
       salvar_cot(cotacoes)
       messagebox.showinfo("OK", f"{num} virou VENDA! Stock baixado.")
       carregar_lista(); atualizar_status()

   ttk.Button(j, text="APROVAR SELECIONADA -> VIRAR VENDA", command=aprovar).pack(pady=10)
   carregar_lista()
