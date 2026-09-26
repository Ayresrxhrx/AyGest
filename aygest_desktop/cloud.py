from __future__ import annotations
from datetime import datetime, timezone
from .api_client import ApiClient

class CloudService:
    """Camada única para sincronização online; mantém a aplicação preparada para multi-tenant sem misturar HTTP na UI."""
    def __init__(self, base_url=None): self.client=ApiClient(base_url)
    def health(self): return self.client.request('GET','/health')
    def login(self,email,password): return self.client.request('POST','/auth/login',json={'email':email,'password':password})
    def tenant(self,token): return self.client.request('GET','/tenant',token=token)
    def push(self,token,tenant_id,events): return self.client.request('POST','/sync/push',token=token,json={'tenant_id':tenant_id,'events':events,'client_time':datetime.now(timezone.utc).isoformat()})
    def pull(self,token,tenant_id,since=None): return self.client.request('GET','/sync/pull',token=token,params={'tenant_id':tenant_id,'since':since} if since else {'tenant_id':tenant_id})
