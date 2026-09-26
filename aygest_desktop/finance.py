from __future__ import annotations
import uuid
from datetime import datetime, timezone

class CashService:
    def __init__(self, conn): self.conn=conn
    def open_session(self, tenant_id, user_id, opening_amount):
        if opening_amount < 0: raise ValueError('O fundo inicial não pode ser negativo.')
        active=self.conn.execute("SELECT id FROM cash_sessions WHERE tenant_id=? AND user_id=? AND closed_at IS NULL",(tenant_id,user_id)).fetchone()
        if active: raise ValueError('Já existe um caixa aberto para este utilizador.')
        sid=str(uuid.uuid4());self.conn.execute("INSERT INTO cash_sessions(id,tenant_id,user_id,opening_amount,opened_at) VALUES(?,?,?,?,?)",(sid,tenant_id,user_id,opening_amount,datetime.now(timezone.utc).isoformat()));return sid
    def close_session(self, session_id, closing_amount):
        if closing_amount < 0: raise ValueError('O valor de fecho não pode ser negativo.')
        row=self.conn.execute("SELECT id FROM cash_sessions WHERE id=? AND closed_at IS NULL",(session_id,)).fetchone()
        if not row: raise ValueError('Caixa aberto não encontrado.')
        self.conn.execute("UPDATE cash_sessions SET closing_amount=?,closed_at=? WHERE id=?",(closing_amount,datetime.now(timezone.utc).isoformat(),session_id))
    def active(self, tenant_id, user_id): return self.conn.execute("SELECT * FROM cash_sessions WHERE tenant_id=? AND user_id=? AND closed_at IS NULL ORDER BY opened_at DESC LIMIT 1",(tenant_id,user_id)).fetchone()
    def summary(self, tenant_id, session_id):
        s=self.conn.execute("SELECT * FROM cash_sessions WHERE id=? AND tenant_id=?",(session_id,tenant_id)).fetchone()
        if not s: raise ValueError('Sessão não encontrada.')
        sales=self.conn.execute("SELECT COALESCE(SUM(total),0) total,COALESCE(SUM(vat),0) vat FROM sales WHERE tenant_id=? AND created_at>=? AND status='completed'",(tenant_id,s['opened_at'])).fetchone()
        movements=self.conn.execute("SELECT COALESCE(SUM(CASE WHEN kind='income' THEN amount ELSE 0 END),0) income,COALESCE(SUM(CASE WHEN kind='expense' THEN amount ELSE 0 END),0) expense FROM finance_movements WHERE tenant_id=? AND created_at>=?",(tenant_id,s['opened_at'])).fetchone()
        expected=s['opening_amount']+sales['total']+movements['income']-movements['expense']
        return {'opening':s['opening_amount'],'sales':sales['total'],'vat':sales['vat'],'income':movements['income'],'expense':movements['expense'],'expected':expected}
    def history(self, tenant_id, limit=100):
        return self.conn.execute("SELECT * FROM cash_sessions WHERE tenant_id=? ORDER BY opened_at DESC LIMIT ?",(tenant_id,limit)).fetchall()

class FinanceService:
    def __init__(self, conn): self.conn=conn
    def ensure(self): self.conn.execute("CREATE TABLE IF NOT EXISTS finance_movements(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,user_id TEXT,kind TEXT NOT NULL,description TEXT NOT NULL,amount REAL NOT NULL,payment_method TEXT NOT NULL,created_at TEXT NOT NULL)")
    def add(self, tenant_id, user_id, description, amount, kind, payment_method='Cash'):
        if amount<=0: raise ValueError('O valor deve ser maior que zero.')
        if kind not in ('income','expense'): raise ValueError('Tipo de movimento inválido.')
        self.ensure();self.conn.execute("INSERT INTO finance_movements VALUES(?,?,?,?,?,?,?)",(str(uuid.uuid4()),tenant_id,user_id,kind,description,amount,payment_method,datetime.now(timezone.utc).isoformat()))
    def movements(self, tenant_id, limit=200):
        self.ensure();return self.conn.execute("SELECT * FROM finance_movements WHERE tenant_id=? ORDER BY created_at DESC LIMIT ?",(tenant_id,limit)).fetchall()
    def totals(self, tenant_id):
        self.ensure();return self.conn.execute("SELECT COALESCE(SUM(CASE WHEN kind='income' THEN amount ELSE 0 END),0) income,COALESCE(SUM(CASE WHEN kind='expense' THEN amount ELSE 0 END),0) expense FROM finance_movements WHERE tenant_id=?",(tenant_id,)).fetchone()
