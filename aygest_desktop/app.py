from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

try:
    import customtkinter as ctk
except ImportError as exc:
    raise SystemExit("Instale as dependências com: pip install -r requirements.txt") from exc

APP_DIR = Path.home() / ".aygest"
APP_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = APP_DIR / "aygest.db"


class Database:
    def __init__(self, path: Path = DB_PATH):
        self.conn = sqlite3.connect(path, timeout=20, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.migrate()

    def migrate(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS tenants(
            id TEXT PRIMARY KEY, name TEXT NOT NULL, nuit TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS licenses(
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, license_key TEXT UNIQUE NOT NULL,
            plan TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active', expires_at TEXT,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id)
        );
        CREATE TABLE IF NOT EXISTS products(
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, sku TEXT NOT NULL, barcode TEXT,
            name TEXT NOT NULL, category TEXT, unit TEXT NOT NULL DEFAULT 'UN', base_factor REAL NOT NULL DEFAULT 1,
            purchase_price REAL NOT NULL DEFAULT 0, sale_price REAL NOT NULL DEFAULT 0,
            vat_rate REAL NOT NULL DEFAULT 16, min_stock REAL NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1,
            UNIQUE(tenant_id, sku), FOREIGN KEY(tenant_id) REFERENCES tenants(id)
        );
        CREATE TABLE IF NOT EXISTS stock(
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, product_id TEXT NOT NULL,
            warehouse TEXT NOT NULL DEFAULT 'Principal', quantity REAL NOT NULL DEFAULT 0,
            reserved REAL NOT NULL DEFAULT 0, updated_at TEXT NOT NULL,
            UNIQUE(tenant_id, product_id, warehouse), FOREIGN KEY(product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS reservations(
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, product_id TEXT NOT NULL,
            quantity REAL NOT NULL, cashier_id TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active',
            expires_at TEXT NOT NULL, created_at TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS customers(
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, name TEXT NOT NULL, nuit TEXT, phone TEXT, email TEXT
        );
        CREATE TABLE IF NOT EXISTS sales(
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, customer_id TEXT, document_no TEXT NOT NULL,
            total REAL NOT NULL, vat REAL NOT NULL, payment_method TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'completed', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sale_items(
            id TEXT PRIMARY KEY, sale_id TEXT NOT NULL, product_id TEXT NOT NULL,
            quantity REAL NOT NULL, unit_price REAL NOT NULL, vat REAL NOT NULL, total REAL NOT NULL,
            FOREIGN KEY(sale_id) REFERENCES sales(id), FOREIGN KEY(product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS quotations(
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, customer_id TEXT, document_no TEXT NOT NULL,
            total REAL NOT NULL, expires_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cash_sessions(
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, user_id TEXT NOT NULL,
            opening_amount REAL NOT NULL, closing_amount REAL, opened_at TEXT NOT NULL, closed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS audit_log(
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, user_id TEXT, action TEXT NOT NULL, details TEXT, created_at TEXT NOT NULL
        );
        """)

    def create_demo_tenant(self):
        if self.conn.execute("SELECT 1 FROM tenants LIMIT 1").fetchone():
            return
        tenant_id = str(uuid.uuid4())
        self.conn.execute("INSERT INTO tenants VALUES (?, ?, ?, ?)", (tenant_id, "Minha Empresa", "", utc_now()))
        key = "AYG-" + uuid.uuid4().hex[:4].upper() + "-" + uuid.uuid4().hex[:4].upper() + "-" + uuid.uuid4().hex[:4].upper()
        self.conn.execute("INSERT INTO licenses VALUES (?, ?, ?, ?, ?, ?)", (str(uuid.uuid4()), tenant_id, key, "Professional", "active", (datetime.now(timezone.utc)+timedelta(days=365)).isoformat()))
        self.conn.execute("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (str(uuid.uuid4()), tenant_id, "SKU-001", "", "Produto", "Geral", "UN", 1, 0, 0, 16, 0, 1))


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class DocumentService:
    @staticmethod
    def invoice_a4(company: str, document_no: str, customer: str, items: list[dict], total: float, output: Path):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_RIGHT
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors

        doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
        styles = getSampleStyleSheet()
        title = ParagraphStyle("AyGestTitle", parent=styles["Title"], fontSize=20, spaceAfter=6)
        right = ParagraphStyle("AyGestRight", parent=styles["Normal"], alignment=TA_RIGHT)
        story = [Paragraph(company, title), Paragraph(f"FACTURA/RECIBO · {document_no}", styles["Heading2"]), Spacer(1, 10), Paragraph(f"Cliente: {customer or 'Consumidor final'}", styles["Normal"]), Spacer(1, 18)]
        data = [["Descrição", "Qtd.", "Preço", "IVA", "Total"]]
        for item in items:
            data.append([str(item["name"]), f"{item['quantity']:.2f}", f"{item['unit_price']:.2f} MT", f"{item['vat']:.2f} MT", f"{item['total']:.2f} MT"])
        data.append(["", "", "", "TOTAL", f"{total:.2f} MT"])
        table = Table(data, colWidths=[235, 55, 75, 65, 75])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#123B63")), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#D9E2EC")),
            ("ALIGN", (1,1), (-1,-1), "RIGHT"), ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#F3F6F9")),
            ("FONTNAME", (-2,-1), (-1,-1), "Helvetica-Bold"), ("BOTTOMPADDING", (0,0), (-1,0), 8), ("TOPPADDING", (0,0), (-1,0), 8),
        ]))
        story += [table, Spacer(1, 22), Paragraph("Documento emitido pelo AyGest. Conserve este documento para referência.", styles["Normal"])]
        doc.build(story)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AyGest Business")
        self.geometry("1440x900")
        self.minsize(1180, 760)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.db = Database()
        self.db.create_demo_tenant()
        self._build()

    def _build(self):
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#0B2239")
        sidebar.grid(row=0, column=0, sticky="nsew"); sidebar.grid_propagate(False)
        ctk.CTkLabel(sidebar, text="AyGest", font=ctk.CTkFont(size=28, weight="bold"), text_color="white").pack(padx=24, pady=(30, 3), anchor="w")
        ctk.CTkLabel(sidebar, text="BUSINESS MANAGEMENT", font=ctk.CTkFont(size=10, weight="bold"), text_color="#AFC4D8").pack(padx=26, pady=(0, 25), anchor="w")
        for label in ["Dashboard", "POS / Vendas", "Facturação", "Produtos", "Stock", "Reservas", "Cotações", "Clientes", "Fornecedores", "Compras", "Financeiro", "Relatórios", "Utilizadores", "Configurações"]:
            ctk.CTkButton(sidebar, text=label, anchor="w", height=40, corner_radius=8, fg_color="transparent", hover_color="#173D60", text_color="#EAF2F8", command=lambda x=label: self.select_module(x)).pack(fill="x", padx=12, pady=2)
        ctk.CTkLabel(sidebar, text="ONLINE · MULTI-TENANT", text_color="#7FD6A8", font=ctk.CTkFont(size=10, weight="bold")).pack(side="bottom", padx=20, pady=24, anchor="w")
        self.content = ctk.CTkFrame(self, fg_color="#F5F7FA", corner_radius=0); self.content.grid(row=0, column=1, sticky="nsew")
        self.show_dashboard()

    def select_module(self, module):
        if module == "Dashboard": self.show_dashboard()
        else:
            for child in self.content.winfo_children(): child.destroy()
            ctk.CTkLabel(self.content, text=module, font=ctk.CTkFont(size=30, weight="bold"), text_color="#102A43").pack(padx=40, pady=(35, 5), anchor="w")
            ctk.CTkLabel(self.content, text="Módulo preparado para integração com os serviços cloud do AyGest.", text_color="#627D98").pack(padx=40, anchor="w")

    def show_dashboard(self):
        for child in self.content.winfo_children(): child.destroy()
        ctk.CTkLabel(self.content, text="Dashboard", font=ctk.CTkFont(size=30, weight="bold"), text_color="#102A43").pack(padx=40, pady=(35, 4), anchor="w")
        ctk.CTkLabel(self.content, text="Visão geral do negócio", font=ctk.CTkFont(size=14), text_color="#627D98").pack(padx=40, anchor="w")
        grid = ctk.CTkFrame(self.content, fg_color="transparent"); grid.pack(fill="x", padx=40, pady=30)
        cards = [("Vendas hoje", "0,00 MT"), ("Stock disponível", "0"), ("Reservas activas", "0"), ("Cotações abertas", "0")]
        for i, (name, value) in enumerate(cards):
            grid.grid_columnconfigure(i, weight=1)
            card = ctk.CTkFrame(grid, fg_color="white", corner_radius=14, border_width=1, border_color="#E1E8EF"); card.grid(row=0, column=i, padx=6, sticky="nsew")
            ctk.CTkLabel(card, text=name, text_color="#627D98", font=ctk.CTkFont(size=12, weight="bold")).pack(padx=20, pady=(20, 6), anchor="w")
            ctk.CTkLabel(card, text=value, text_color="#102A43", font=ctk.CTkFont(size=24, weight="bold")).pack(padx=20, pady=(0, 20), anchor="w")
        panel = ctk.CTkFrame(self.content, fg_color="white", corner_radius=14); panel.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        ctk.CTkLabel(panel, text="AyGest Business", font=ctk.CTkFont(size=21, weight="bold"), text_color="#102A43").pack(padx=30, pady=(30, 5), anchor="w")
        ctk.CTkLabel(panel, text="POS · Stock · Reservas · Facturação · Financeiro · Multi-tenant", text_color="#627D98").pack(padx=30, anchor="w")
        ctk.CTkButton(panel, text="Abrir POS", width=150, height=42, corner_radius=9, command=lambda: self.select_module("POS / Vendas")).pack(padx=30, pady=25, anchor="w")


if __name__ == "__main__":
    App().mainloop()
