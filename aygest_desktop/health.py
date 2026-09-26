from __future__ import annotations
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from .config import APP_DIR, DB_PATH, BACKUP_DIR, settings

class SystemHealth:
    def __init__(self, conn=None):
        self.conn = conn
    def database(self):
        if not Path(DB_PATH).exists(): return {'ok':False,'message':'Base de dados não encontrada'}
        try:
            c=self.conn or sqlite3.connect(DB_PATH)
            row=c.execute('PRAGMA integrity_check').fetchone(); ok=bool(row and row[0]=='ok')
            return {'ok':ok,'message':row[0] if row else 'Sem resposta'}
        except Exception as e: return {'ok':False,'message':str(e)}
    def storage(self):
        try:
            usage=os.statvfs(APP_DIR) if hasattr(os,'statvfs') else None
            free=(usage.f_bavail*usage.f_frsize) if usage else 0
            return {'ok':free==0 or free>100*1024*1024,'free_bytes':free}
        except Exception:return {'ok':True,'free_bytes':0}
    def backups(self):
        files=sorted(BACKUP_DIR.glob('*'),key=lambda p:p.stat().st_mtime if p.exists() else 0,reverse=True)
        return {'count':len(files),'latest':files[0].name if files else None}
    def snapshot(self):
        return {'timestamp':datetime.now(timezone.utc).isoformat(),'database':self.database(),'storage':self.storage(),'backups':self.backups(),'cloud_configured':bool(settings.api_url),'version':settings.app_version}
