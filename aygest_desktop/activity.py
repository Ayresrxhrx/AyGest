from __future__ import annotations
from datetime import datetime, timezone
import json

class ActivityService:
    def __init__(self, conn): self.conn=conn
    def ensure(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS activity_log (id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT NOT NULL, user_id TEXT, action TEXT NOT NULL, entity_type TEXT, entity_id TEXT, details TEXT, created_at TEXT NOT NULL)''')
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_activity_tenant_date ON activity_log(tenant_id,created_at)')
        self.conn.commit()
    def log(self,tenant_id,action,entity_type=None,entity_id=None,user_id=None,details=None):
        self.ensure();self.conn.execute('INSERT INTO activity_log(tenant_id,user_id,action,entity_type,entity_id,details,created_at) VALUES(?,?,?,?,?,?,?)',(tenant_id,user_id,action,entity_type,entity_id,json.dumps(details,ensure_ascii=False) if details else None,datetime.now(timezone.utc).isoformat()));self.conn.commit()
    def recent(self,tenant_id,limit=100):
        self.ensure();return self.conn.execute('SELECT * FROM activity_log WHERE tenant_id=? ORDER BY created_at DESC LIMIT ?',(tenant_id,limit)).fetchall()
