from __future__ import annotations
import sqlite3, uuid
from datetime import datetime, timedelta, timezone

class ReservationService:
    def __init__(self, conn: sqlite3.Connection): self.conn=conn
    def expire(self, tenant_id):
        now=datetime.now(timezone.utc).isoformat(); self.conn.execute('BEGIN IMMEDIATE')
        try:
            rows=self.conn.execute("SELECT product_id,quantity FROM reservations WHERE tenant_id=? AND status='active' AND expires_at<=?",(tenant_id,now)).fetchall()
            for r in rows: self.conn.execute("UPDATE stock SET reserved=MAX(0,reserved-?),updated_at=? WHERE tenant_id=? AND product_id=?",(r['quantity'],now,tenant_id,r['product_id']))
            self.conn.execute("UPDATE reservations SET status='expired' WHERE tenant_id=? AND status='active' AND expires_at<=?",(tenant_id,now)); self.conn.execute('COMMIT')
        except Exception: self.conn.execute('ROLLBACK'); raise
    def reserve(self,tenant_id,product_id,quantity,user_id,days=3):
        quantity=float(quantity)
        if quantity<=0: raise ValueError('A quantidade deve ser maior que zero.')
        self.expire(tenant_id); self.conn.execute('BEGIN IMMEDIATE')
        try:
            s=self.conn.execute("SELECT quantity,reserved FROM stock WHERE tenant_id=? AND product_id=? ORDER BY warehouse LIMIT 1",(tenant_id,product_id)).fetchone()
            if not s or s['quantity']-s['reserved']<quantity: raise ValueError('Stock disponível insuficiente para a reserva.')
            rid=str(uuid.uuid4()); now=datetime.now(timezone.utc); self.conn.execute("INSERT INTO reservations VALUES(?,?,?,?,?,?,?,?)",(rid,tenant_id,product_id,quantity,user_id,'active',(now+timedelta(days=days)).isoformat(),now.isoformat())); self.conn.execute("UPDATE stock SET reserved=reserved+?,updated_at=? WHERE tenant_id=? AND product_id=?",(quantity,now.isoformat(),tenant_id,product_id)); self.conn.execute('COMMIT'); return rid
        except Exception: self.conn.execute('ROLLBACK'); raise
    def release(self,tenant_id,reservation_id):
        self.conn.execute('BEGIN IMMEDIATE')
        try:
            r=self.conn.execute("SELECT product_id,quantity,status FROM reservations WHERE id=? AND tenant_id=?",(reservation_id,tenant_id)).fetchone()
            if not r or r['status']!='active': raise ValueError('Reserva não está activa.')
            self.conn.execute("UPDATE stock SET reserved=MAX(0,reserved-?),updated_at=? WHERE tenant_id=? AND product_id=?",(r['quantity'],datetime.now(timezone.utc).isoformat(),tenant_id,r['product_id'])); self.conn.execute("UPDATE reservations SET status='released' WHERE id=?",(reservation_id,)); self.conn.execute('COMMIT')
        except Exception: self.conn.execute('ROLLBACK'); raise

class QuotationService:
    def __init__(self,conn): self.conn=conn
    def create(self,tenant_id,customer_id,total,days=3):
        now=datetime.now(timezone.utc); qid=str(uuid.uuid4()); no='ORC-'+now.strftime('%Y%m%d%H%M%S')+'-'+qid[:6].upper(); self.conn.execute("INSERT INTO quotations VALUES(?,?,?,?,?,?,?,?)",(qid,tenant_id,customer_id,float(total),no,(now+timedelta(days=days)).isoformat(),'open',now.isoformat())); return qid
    def approve(self,tenant_id,quotation_id):
        self.conn.execute('BEGIN IMMEDIATE')
        try:
            q=self.conn.execute("SELECT * FROM quotations WHERE id=? AND tenant_id=?",(quotation_id,tenant_id)).fetchone()
            if not q: raise ValueError('Cotação não encontrada.')
            if q['status']!='open': raise ValueError('Esta cotação já não está aberta.')
            if datetime.fromisoformat(q['expires_at'])<=datetime.now(timezone.utc): self.conn.execute("UPDATE quotations SET status='expired' WHERE id=?",(quotation_id,)); raise ValueError('A cotação expirou e não pode ser aprovada.')
            self.conn.execute("UPDATE quotations SET status='approved' WHERE id=?",(quotation_id,)); self.conn.execute('COMMIT'); return q['document_no']
        except Exception: self.conn.execute('ROLLBACK'); raise
