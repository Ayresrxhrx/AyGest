from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
import secrets
import urllib.request

@dataclass
class LicenseStatus:
    active: bool
    key: str | None = None
    tenant_id: str | None = None
    plan: str | None = None
    expires_at: str | None = None
    message: str = ''

class LicenseService:
    def __init__(self, api_base='', storage_path='license.json'):
        self.api_base=api_base.rstrip('/')
        self.storage_path=storage_path
    def _device_id(self):
        raw=f'{os.getenv("COMPUTERNAME","")}|{os.getenv("USERNAME","")}|{os.name}|{os.getcwd()}'
        return hashlib.sha256(raw.encode()).hexdigest()
    def _save(self,data):
        tmp=self.storage_path+'.tmp'
        with open(tmp,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
        os.replace(tmp,self.storage_path)
    def _load(self):
        try:
            with open(self.storage_path,encoding='utf-8') as f:return json.load(f)
        except (OSError,ValueError):return {}
    def activate_online(self,key,tenant_id=None):
        key=str(key or '').strip().upper()
        if not key:return LicenseStatus(False,message='A chave de activação é obrigatória.')
        if not self.api_base:return LicenseStatus(False,message='Servidor de activação não configurado.')
        payload=json.dumps({'key':key,'tenant_id':tenant_id,'device_id':self._device_id()}).encode()
        req=urllib.request.Request(self.api_base+'/api/v1/licenses/activate',data=payload,headers={'Content-Type':'application/json'},method='POST')
        try:
            with urllib.request.urlopen(req,timeout=15) as r:data=json.loads(r.read().decode())
            if not data.get('active'):return LicenseStatus(False,key=key,message=data.get('message','Chave recusada pelo servidor.'))
            data['key']=key;data['device_id']=self._device_id();data['checked_at']=datetime.now(timezone.utc).isoformat();self._save(data)
            return self.status()
        except Exception as e:return LicenseStatus(False,key=key,message=f'Não foi possível contactar o servidor de activação: {e}')
    def status(self):
        d=self._load();expires=d.get('expires_at');active=bool(d.get('active'))
        if expires:
            try: active=active and datetime.fromisoformat(expires.replace('Z','+00:00'))>datetime.now(timezone.utc)
            except ValueError: active=False
        return LicenseStatus(active,key=d.get('key'),tenant_id=d.get('tenant_id'),plan=d.get('plan'),expires_at=expires,message='Licença activa.' if active else 'Licença não activa ou expirada.')
    def verify_online(self):
        s=self.status()
        if not s.key or not self.api_base:return s
        payload=json.dumps({'key':s.key,'tenant_id':s.tenant_id,'device_id':self._device_id()}).encode()
        req=urllib.request.Request(self.api_base+'/api/v1/licenses/verify',data=payload,headers={'Content-Type':'application/json'},method='POST')
        try:
            with urllib.request.urlopen(req,timeout=10) as r:d=json.loads(r.read().decode())
            d['key']=s.key;d['device_id']=self._device_id();d['checked_at']=datetime.now(timezone.utc).isoformat();self._save(d);return self.status()
        except Exception:return s
    def deactivate_local(self):
        self._save({'active':False,'device_id':self._device_id(),'deactivated_at':datetime.now(timezone.utc).isoformat()})
        return self.status()

def generate_activation_key(prefix='AYGEST'):
    return prefix+'-'+secrets.token_hex(4).upper()+'-'+secrets.token_hex(4).upper()+'-'+secrets.token_hex(4).upper()
