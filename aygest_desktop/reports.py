from __future__ import annotations
from datetime import datetime, timezone

class ReportService:
    def __init__(self, conn): self.conn=conn
    def _period(self,start,end):
        where=[];args=[]
        if start: where.append('created_at>=?');args.append(start)
        if end: where.append('created_at<?');args.append(end)
        return where,args
    def sales(self, tenant_id, start=None, end=None):
        where=['tenant_id=?','status=\'completed\''];args=[tenant_id];w,a=self._period(start,end);where+=w;args+=a
        return self.conn.execute(f"SELECT COUNT(*) count,COALESCE(SUM(total),0) total,COALESCE(SUM(vat),0) vat,COALESCE(SUM(subtotal),0) subtotal FROM sales WHERE {' AND '.join(where)}",args).fetchone()
    def purchases(self, tenant_id, start=None, end=None):
        where=['tenant_id=?'];args=[tenant_id];w,a=self._period(start,end);where+=w;args+=a
        return self.conn.execute(f"SELECT COUNT(*) count,COALESCE(SUM(total),0) total FROM purchases WHERE {' AND '.join(where)}",args).fetchone()
    def stock(self, tenant_id):
        return self.conn.execute("SELECT p.name,p.sku,COALESCE(s.quantity,0) quantity,COALESCE(s.reserved,0) reserved,p.purchase_price,p.sale_price,COALESCE(p.min_stock,0) min_stock FROM products p LEFT JOIN stock s ON s.product_id=p.id AND s.tenant_id=p.tenant_id WHERE p.tenant_id=? AND p.active=1 ORDER BY p.name",(tenant_id,)).fetchall()
    def top_products(self,tenant_id,start=None,end=None,limit=10):
        where=['s.tenant_id=?','s.status=\'completed\''];args=[tenant_id];w,a=self._period(start,end);where+=w;args+=a
        return self.conn.execute(f"SELECT si.product_id,si.product_name,SUM(si.quantity) quantity,SUM(si.line_total) total FROM sale_items si JOIN sales s ON s.id=si.sale_id WHERE {' AND '.join(where)} GROUP BY si.product_id,si.product_name ORDER BY total DESC LIMIT ?",args+[limit]).fetchall()
    def payments(self,tenant_id,start=None,end=None):
        where=['tenant_id=?'];args=[tenant_id];w,a=self._period(start,end);where+=w;args+=a
        return self.conn.execute(f"SELECT payment_method,COUNT(*) count,COALESCE(SUM(total),0) total FROM sales WHERE {' AND '.join(where)} AND status='completed' GROUP BY payment_method ORDER BY total DESC",args).fetchall()
    def daily_sales(self,tenant_id,start,end):
        return self.conn.execute("SELECT substr(created_at,1,10) day,COUNT(*) count,COALESCE(SUM(total),0) total FROM sales WHERE tenant_id=? AND status='completed' AND created_at>=? AND created_at<? GROUP BY substr(created_at,1,10) ORDER BY day",(tenant_id,start,end)).fetchall()
    def low_stock(self,tenant_id):
        return [r for r in self.stock(tenant_id) if float(r['quantity'])-float(r['reserved'])<=float(r['min_stock'])]
    def monthly(self, tenant_id):
        now=datetime.now(timezone.utc);start=now.replace(day=1,hour=0,minute=0,second=0,microsecond=0);end=datetime(now.year+1,1,1,tzinfo=timezone.utc) if now.month==12 else datetime(now.year,now.month+1,1,tzinfo=timezone.utc)
        s=self.sales(tenant_id,start.isoformat(),end.isoformat());p=self.purchases(tenant_id,start.isoformat(),end.isoformat());return {'period':start.strftime('%m/%Y'),'sales_count':s['count'],'sales_total':s['total'],'vat':s['vat'],'purchases_total':p['total'],'gross_margin':s['total']-p['total']}
