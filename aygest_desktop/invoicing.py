from __future__ import annotations
from pathlib import Path
import os, platform
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from .config import APP_DIR
NAVY=colors.HexColor('#102A43');MUTED=colors.HexColor('#627D98');BORDER=colors.HexColor('#D9E2EC')
class InvoiceService:
    def __init__(self,conn): self.conn=conn
    def _sale(self,tenant_id,sale_id):
        sale=self.conn.execute("SELECT s.*,t.name company,t.nuit company_nuit,c.name customer_name,c.nuit customer_nuit,c.phone customer_phone,c.email customer_email FROM sales s JOIN tenants t ON t.id=s.tenant_id LEFT JOIN customers c ON c.id=s.customer_id WHERE s.id=? AND s.tenant_id=?",(sale_id,tenant_id)).fetchone()
        if not sale: raise ValueError('Factura não encontrada.')
        return sale
    def _items(self,sale_id): return self.conn.execute("SELECT si.*,p.name product_name,p.sku,p.unit FROM sale_items si JOIN products p ON p.id=si.product_id WHERE si.sale_id=? ORDER BY si.id",(sale_id,)).fetchall()
    def pdf(self,tenant_id,sale_id,thermal=False):
        sale=self._sale(tenant_id,sale_id);items=self._items(sale_id);out=APP_DIR/'documents';out.mkdir(parents=True,exist_ok=True);safe=''.join(ch if ch.isalnum() or ch in '-_.' else '_' for ch in str(sale['document_no']));path=out/f'{safe}-{"POS" if thermal else "A4"}.pdf';(self._thermal if thermal else self._a4)(path,sale,items);return str(path)
    def open_document(self,path):
        p=Path(path)
        if not p.exists(): raise FileNotFoundError(path)
        if platform.system()=='Windows':os.startfile(str(p))
        elif platform.system()=='Darwin':os.system(f'open "{p}"')
        else:os.system(f'xdg-open "{p}"')
    def _header(self,c,sale,w,y,thermal=False):
        c.setFillColor(NAVY);c.setFont('Helvetica-Bold',15 if thermal else 20);c.drawString(12*mm,y,sale['company'] or 'AyGest');y-=6*mm;c.setFillColor(MUTED);c.setFont('Helvetica',8);c.drawString(12*mm,y,f"NUIT: {sale['company_nuit'] or '-'}");y-=7*mm;c.setFillColor(NAVY);c.setFont('Helvetica-Bold',11 if thermal else 13);c.drawString(12*mm,y,'FACTURA');y-=5*mm;c.setFillColor(MUTED);c.setFont('Helvetica',8);c.drawString(12*mm,y,f"N.º {sale['document_no']}");c.drawRightString(w-12*mm,y,str(sale['created_at'])[:19].replace('T',' '));return y-7*mm
    def _customer(self,c,sale,w,y):
        c.setStrokeColor(BORDER);c.line(12*mm,y,w-12*mm,y);y-=6*mm;c.setFillColor(MUTED);c.setFont('Helvetica-Bold',7);c.drawString(12*mm,y,'CLIENTE');y-=4*mm;c.setFillColor(NAVY);c.setFont('Helvetica-Bold',9);c.drawString(12*mm,y,sale['customer_name'] or 'Consumidor final');
        if sale['customer_nuit']:c.setFont('Helvetica',8);c.setFillColor(MUTED);c.drawString(75*mm,y,f"NUIT: {sale['customer_nuit']}")
        y-=4*mm
        if sale['customer_phone'] or sale['customer_email']:c.setFont('Helvetica',7);c.setFillColor(MUTED);c.drawString(12*mm,y,'  •  '.join(x for x in [sale['customer_phone'],sale['customer_email']] if x)[:100]);y-=4*mm
        return y-4*mm
    def _a4(self,path,sale,items):
        w,h=A4;c=canvas.Canvas(str(path),pagesize=A4);y=h-22*mm;y=self._header(c,sale,w,y);y=self._customer(c,sale,w,y)
        def columns(y):
            c.setFillColor(colors.HexColor('#F2F5F8'));c.roundRect(12*mm,y-6*mm,w-24*mm,9*mm,2*mm,fill=1,stroke=0);c.setFillColor(MUTED);c.setFont('Helvetica-Bold',7);c.drawString(15*mm,y-2*mm,'DESCRIÇÃO');c.drawRightString(145*mm,y-2*mm,'QTD');c.drawRightString(170*mm,y-2*mm,'PREÇO');c.drawRightString(w-15*mm,y-2*mm,'TOTAL')
        columns(y);y-=12*mm
        for item in items:
            if y<42*mm:c.showPage();y=h-22*mm;y=self._header(c,sale,w,y);columns(y);y-=12*mm
            qty=float(item['quantity'] or 0);line=float(item['line_total'] or 0);unit=float(item['unit_price'] or 0);c.setFillColor(NAVY);c.setFont('Helvetica',8);c.drawString(15*mm,y,(item['product_name'] or '')[:58]);c.setFillColor(MUTED);c.drawRightString(145*mm,y,f'{qty:g}');c.drawRightString(170*mm,y,f'{unit:,.2f} MT');c.setFillColor(NAVY);c.drawRightString(w-15*mm,y,f'{line:,.2f} MT');y-=6*mm;c.setStrokeColor(BORDER);c.line(15*mm,y+2*mm,w-15*mm,y+2*mm)
        subtotal=float(sale['total'] or 0)-float(sale['vat'] or 0);y-=5*mm;c.setFillColor(NAVY);c.setFont('Helvetica-Bold',10);c.drawString(125*mm,y,'SUBTOTAL');c.drawRightString(w-15*mm,y,f'{subtotal:,.2f} MT');y-=6*mm;c.setFillColor(MUTED);c.setFont('Helvetica',8);c.drawString(125*mm,y,'IVA');c.drawRightString(w-15*mm,y,f'{float(sale["vat"] or 0):,.2f} MT');y-=8*mm;c.setFillColor(NAVY);c.setFont('Helvetica-Bold',14);c.drawString(125*mm,y,'TOTAL');c.drawRightString(w-15*mm,y,f'{float(sale["total"] or 0):,.2f} MT');y-=7*mm;c.setFillColor(MUTED);c.setFont('Helvetica',8);c.drawString(15*mm,y,f"Pagamento: {sale['payment_method'] or '-'}  •  Estado: {sale['status']}");c.setFont('Helvetica-Oblique',8);c.drawCentredString(w/2,18*mm,'Documento emitido pelo AyGest • Obrigado pela preferência.');c.save()
    def _thermal(self,path,sale,items):
        w,h=80*mm,max(220*mm,85*mm+len(items)*9*mm);c=canvas.Canvas(str(path),pagesize=(w,h));y=h-10*mm;y=self._header(c,sale,w,y,True);y=self._customer(c,sale,w,y);c.setFillColor(NAVY);c.setFont('Helvetica-Bold',8);c.drawString(12*mm,y,'ITEM');c.drawRightString(w-12*mm,y,'TOTAL');y-=5*mm
        for item in items:qty=float(item['quantity'] or 0);total=float(item['line_total'] or 0);c.setFont('Helvetica',8);c.drawString(12*mm,y,f'{qty:g} x {(item["product_name"] or "")[:28]}');c.drawRightString(w-12*mm,y,f'{total:,.2f}');y-=5*mm
        y-=3*mm;c.setStrokeColor(BORDER);c.line(12*mm,y,w-12*mm,y);y-=7*mm;c.setFillColor(NAVY);c.setFont('Helvetica-Bold',11);c.drawString(12*mm,y,'TOTAL');c.drawRightString(w-12*mm,y,f'{float(sale["total"] or 0):,.2f} MT');y-=6*mm;c.setFillColor(MUTED);c.setFont('Helvetica',8);c.drawString(12*mm,y,f"IVA: {float(sale['vat'] or 0):,.2f} MT");y-=5*mm;c.drawString(12*mm,y,f"Pagamento: {sale['payment_method'] or '-'}");c.setFont('Helvetica-Oblique',7);c.drawCentredString(w/2,8*mm,'AyGest • Obrigado pela preferência');c.save()
