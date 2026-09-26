from __future__ import annotations
import sqlite3, uuid
from datetime import datetime, timezone

class POSService:
    def __init__(self, conn: sqlite3.Connection): self.conn = conn
    def products(self, tenant_id, search=""):
        p=f"%{search.strip()}%"
        return self.conn.execute("SELECT p.id,p.sku,p.barcode,p.name,p.sale_price,p.vat_rate,COALESCE(SUM(s.quantity-s.reserved),0) available FROM products p LEFT JOIN stock s ON s.product_id=p.id AND s.tenant_id=p.tenant_id WHERE p.tenant_id=? AND p.active=1 AND (?='' OR p.name LIKE ? OR p.sku LIKE ? OR COALESCE(p.barcode,'') LIKE ?) GROUP BY p.id ORDER BY p.name COLLATE NOCASE",(tenant_id,search.strip(),p,p,p)).fetchall()
    def complete_sale(self, tenant_id,user_id,cart,payment_method,customer_id=None):
        if not cart: raise ValueError("A venda não contém produtos.")
        if payment_method not in {"Dinheiro","M-Pesa","Cartão"}: raise ValueError("Método de pagamento inválido.")
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            total=vat=0.0
            for item in cart:
                row=self.conn.execute("SELECT sale_price,vat_rate FROM products WHERE id=? AND tenant_id=? AND active=1",(item['product_id'],tenant_id)).fetchone()
                stock=self.conn.execute("SELECT quantity,reserved FROM stock WHERE product_id=? AND tenant_id=? ORDER BY warehouse LIMIT 1",(item['product_id'],tenant_id)).fetchone()
                qty=float(item['quantity'])
                if not row or not stock: raise ValueError("Produto não encontrado.")
                if qty<=0 or stock['quantity']-stock['reserved']<qty: raise ValueError(f"Stock insuficiente para {item['name']}.")
                line=float(row['sale_price'])*qty; total+=line; vat+=line*float(row['vat_rate'])/(100+float(row['vat_rate']))
            sale_id=str(uuid.uuid4()); number="FT-"+datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')+"-"+sale_id[:6].upper()
            self.conn.execute("INSERT INTO sales VALUES(?,?,?,?,?,?,?,?,?)",(sale_id,tenant_id,customer_id,number,total,vat,payment_method,'completed',datetime.now(timezone.utc).isoformat()))
            self.conn.execute("CREATE TABLE IF NOT EXISTS sale_items(id TEXT PRIMARY KEY,sale_id TEXT NOT NULL,product_id TEXT NOT NULL,quantity REAL NOT NULL,unit_price REAL NOT NULL,line_total REAL NOT NULL,vat_rate REAL NOT NULL,FOREIGN KEY(sale_id) REFERENCES sales(id))")
            for item in cart:
                p=self.conn.execute("SELECT sale_price,vat_rate FROM products WHERE id=?",(item['product_id'],)).fetchone(); qty=float(item['quantity']); line=float(p['sale_price'])*qty
                self.conn.execute("INSERT INTO sale_items VALUES(?,?,?,?,?,?,?)",(str(uuid.uuid4()),sale_id,item['product_id'],qty,p['sale_price'],line,p['vat_rate']))
                self.conn.execute("UPDATE stock SET quantity=quantity-?,updated_at=? WHERE tenant_id=? AND product_id=? AND quantity-reserved>=?",(qty,datetime.now(timezone.utc).isoformat(),tenant_id,item['product_id'],qty))
            self.conn.execute("INSERT INTO audit_log VALUES(?,?,?,?,?,?)",(str(uuid.uuid4()),tenant_id,user_id,'SALE_COMPLETED',number,datetime.now(timezone.utc).isoformat())); self.conn.execute("COMMIT")
            return {'id':sale_id,'number':number,'total':total,'vat':vat}
        except Exception: self.conn.execute("ROLLBACK"); raise
