from __future__ import annotations
import sqlite3, uuid
from datetime import datetime, timezone

PAYMENT_METHODS={"Dinheiro","M-Pesa","Cartão"}

def now(): return datetime.now(timezone.utc).isoformat()

class POSService:
    def __init__(self, conn: sqlite3.Connection): self.conn=conn
    def products(self, tenant_id, search=""):
        p=f"%{search.strip()}%"
        return self.conn.execute("SELECT p.id,p.sku,p.barcode,p.name,p.sale_price,p.vat_rate,COALESCE(SUM(s.quantity-s.reserved),0) available FROM products p LEFT JOIN stock s ON s.product_id=p.id AND s.tenant_id=p.tenant_id WHERE p.tenant_id=? AND p.active=1 AND (?='' OR p.name LIKE ? OR p.sku LIKE ? OR COALESCE(p.barcode,'') LIKE ?) GROUP BY p.id ORDER BY p.name COLLATE NOCASE",(tenant_id,search.strip(),p,p,p)).fetchall()
    def _ensure_finance(self):
        self.conn.execute("CREATE TABLE IF NOT EXISTS finance_movements(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,user_id TEXT,kind TEXT NOT NULL,description TEXT NOT NULL,amount REAL NOT NULL,payment_method TEXT NOT NULL,created_at TEXT NOT NULL)")
    def complete_sale(self, tenant_id,user_id,cart,payment_method,customer_id=None):
        if not cart: raise ValueError("A venda não contém produtos.")
        if payment_method not in PAYMENT_METHODS: raise ValueError("Método de pagamento inválido.")
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            total=vat=0.0; validated=[]
            for item in cart:
                row=self.conn.execute("SELECT sale_price,vat_rate,name FROM products WHERE id=? AND tenant_id=? AND active=1",(item['product_id'],tenant_id)).fetchone()
                stock=self.conn.execute("SELECT quantity,reserved FROM stock WHERE product_id=? AND tenant_id=? ORDER BY warehouse LIMIT 1",(item['product_id'],tenant_id)).fetchone()
                qty=float(item['quantity'])
                if not row or not stock: raise ValueError(f"Produto não encontrado: {item.get('name','')}")
                if qty<=0: raise ValueError("A quantidade deve ser maior que zero.")
                if stock['quantity']-stock['reserved']<qty: raise ValueError(f"Stock insuficiente para {row['name']}.")
                line=float(row['sale_price'])*qty; total+=line; vat+=line*float(row['vat_rate'])/(100+float(row['vat_rate']));validated.append((item['product_id'],qty,row,line))
            sale_id=str(uuid.uuid4()); created=now(); number="FT-"+datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')+"-"+sale_id[:6].upper();subtotal=total-vat
            self.conn.execute("INSERT INTO sales(id,tenant_id,customer_id,total,vat,payment_method,status,document_no,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(sale_id,tenant_id,customer_id,total,vat,payment_method,'completed',number,created))
            self.conn.execute("CREATE TABLE IF NOT EXISTS sale_items(id TEXT PRIMARY KEY,sale_id TEXT NOT NULL,product_id TEXT NOT NULL,quantity REAL NOT NULL,unit_price REAL NOT NULL,line_total REAL NOT NULL,vat_rate REAL NOT NULL,FOREIGN KEY(sale_id) REFERENCES sales(id))")
            for pid,qty,p,line in validated:
                self.conn.execute("INSERT INTO sale_items VALUES(?,?,?,?,?,?,?)",(str(uuid.uuid4()),sale_id,pid,qty,p['sale_price'],line,p['vat_rate']))
                cur=self.conn.execute("UPDATE stock SET quantity=quantity-?,updated_at=? WHERE tenant_id=? AND product_id=? AND quantity-reserved>=?",(qty,created,tenant_id,pid,qty))
                if cur.rowcount!=1: raise ValueError(f"Não foi possível actualizar o stock de {p['name']}.")
            self._ensure_finance();self.conn.execute("INSERT INTO finance_movements VALUES(?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),tenant_id,user_id,'SALE',f'Venda {number}',total,payment_method,created))
            self.conn.execute("INSERT INTO audit_log VALUES(?,?,?,?,?,?)",(str(uuid.uuid4()),tenant_id,user_id,'SALE_COMPLETED',f'{number}|total={total:.2f}|subtotal={subtotal:.2f}|vat={vat:.2f}',created));self.conn.execute("COMMIT")
            return {'id':sale_id,'number':number,'total':total,'subtotal':subtotal,'vat':vat}
        except Exception:
            self.conn.execute("ROLLBACK");raise
    def cancel_sale(self, tenant_id,user_id,sale_id,reason):
        if not reason.strip(): raise ValueError('Indique o motivo da anulação.')
        self.conn.execute('BEGIN IMMEDIATE')
        try:
            sale=self.conn.execute("SELECT * FROM sales WHERE id=? AND tenant_id=?",(sale_id,tenant_id)).fetchone()
            if not sale: raise ValueError('Factura não encontrada.')
            if sale['status']!='completed': raise ValueError('Esta factura já não está activa.')
            items=self.conn.execute('SELECT product_id,quantity FROM sale_items WHERE sale_id=?',(sale_id,)).fetchall()
            for item in items:
                cur=self.conn.execute("UPDATE stock SET quantity=quantity+?,updated_at=? WHERE tenant_id=? AND product_id=?",(float(item['quantity']),now(),tenant_id,item['product_id']))
                if cur.rowcount!=1: raise ValueError('Produto da factura já não possui registo de stock.')
            self.conn.execute("UPDATE sales SET status='cancelled' WHERE id=? AND tenant_id=?",(sale_id,tenant_id))
            self._ensure_finance();self.conn.execute("INSERT INTO finance_movements VALUES(?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),tenant_id,user_id,'SALE_REVERSAL',f'Anulação {sale["document_no"]}: {reason.strip()}',-float(sale['total']),sale['payment_method'],now()))
            self.conn.execute("INSERT INTO audit_log VALUES(?,?,?,?,?,?)",(str(uuid.uuid4()),tenant_id,user_id,'SALE_CANCELLED',f'{sale["document_no"]}|{reason.strip()}',now()));self.conn.execute('COMMIT')
        except Exception:
            self.conn.execute('ROLLBACK');raise
    def sale(self,tenant_id,sale_id): return self.conn.execute('SELECT * FROM sales WHERE id=? AND tenant_id=?',(sale_id,tenant_id)).fetchone()
