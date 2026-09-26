from __future__ import annotations
import uuid
from datetime import datetime, timezone

class PurchaseService:
    def __init__(self, conn): self.conn=conn
    def create(self, tenant_id, supplier_id, document_no, items):
        if not items: raise ValueError('A compra deve ter pelo menos um produto.')
        now=datetime.now(timezone.utc).isoformat(); total=sum(q*p for _,q,p in items); pid=str(uuid.uuid4())
        self.conn.execute('BEGIN')
        try:
            self.conn.execute('INSERT INTO purchases(id,tenant_id,document_no,supplier_id,total,status,created_at) VALUES(?,?,?,?,?,?,?)',(pid,tenant_id,document_no,supplier_id,total,'received',now))
            for product_id,qty,cost in items:
                if qty<=0 or cost<0: raise ValueError('Quantidade e custo devem ser válidos.')
                self.conn.execute('INSERT INTO purchase_items(id,purchase_id,product_id,quantity,unit_cost,line_total) VALUES(?,?,?,?,?,?)',(str(uuid.uuid4()),pid,product_id,qty,cost,qty*cost))
                self.conn.execute('INSERT INTO stock(id,tenant_id,product_id,warehouse,quantity,reserved,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(tenant_id,product_id,warehouse) DO UPDATE SET quantity=quantity+excluded.quantity,updated_at=excluded.updated_at',(str(uuid.uuid4()),tenant_id,product_id,'Principal',qty,0,now))
            self.conn.execute('COMMIT'); return pid
        except Exception:
            self.conn.execute('ROLLBACK'); raise
