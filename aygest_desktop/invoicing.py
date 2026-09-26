from __future__ import annotations
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from .config import APP_DIR

class InvoiceService:
    def __init__(self, conn): self.conn=conn
    def pdf(self, tenant_id, sale_id, thermal=False):
        sale=self.conn.execute('SELECT s.*,t.name company,t.nuit FROM sales s JOIN tenants t ON t.id=s.tenant_id WHERE s.id=? AND s.tenant_id=?',(sale_id,tenant_id)).fetchone()
        if not sale: raise ValueError('Factura não encontrada.')
        items=self.conn.execute('SELECT si.*,p.name FROM sale_items si JOIN products p ON p.id=si.product_id WHERE si.sale_id=? ORDER BY p.name',(sale_id,)).fetchall()
        out=APP_DIR/'documents';out.mkdir(parents=True,exist_ok=True);safe=sale['document_no'].replace('/','-').replace(' ','_');suffix='POS' if thermal else 'A4';path=out/f'{safe}-{suffix}.pdf'
        page=(80*mm,220*mm) if thermal else A4;c=canvas.Canvas(str(path),pagesize=page);w,h=page;y=h-18*mm
        c.setFont('Helvetica-Bold',14 if thermal else 18);c.drawCentredString(w/2,y,sale['company']);y-=7*mm;c.setFont('Helvetica',8 if thermal else 10);c.drawCentredString(w/2,y,f"NUIT: {sale['nuit'] or '-'}");y-=10*mm;c.setFont('Helvetica-Bold',11);c.drawString(12*mm,y,'FACTURA');y-=6*mm;c.setFont('Helvetica',8);c.drawString(12*mm,y,f"Documento: {sale['document_no']}");y-=5*mm;c.drawString(12*mm,y,f"Data: {sale['created_at'][:19].replace('T',' ')}");y-=8*mm
        c.setFont('Helvetica-Bold',8);c.drawString(12*mm,y,'Produto');c.drawRightString(w-12*mm,y,'Total');y-=4*mm;c.line(12*mm,y,w-12*mm,y);y-=5*mm;c.setFont('Helvetica',8)
        for it in items:
            c.drawString(12*mm,y,(it['name'] or '')[:30]);c.drawRightString(w-12*mm,y,f"{it['line_total']:.2f} MT");y-=5*mm
            if y<25*mm:c.showPage();y=h-18*mm;c.setFont('Helvetica',8)
        y-=4*mm;c.line(12*mm,y,w-12*mm,y);y-=7*mm;c.setFont('Helvetica-Bold',10);c.drawString(12*mm,y,'TOTAL');c.drawRightString(w-12*mm,y,f"{sale['total']:.2f} MT");y-=6*mm;c.setFont('Helvetica',8);c.drawString(12*mm,y,f"IVA: {sale['vat']:.2f} MT");y-=5*mm;c.drawString(12*mm,y,f"Pagamento: {sale['payment_method']}");y-=10*mm;c.drawCentredString(w/2,y,'Obrigado pela preferência!');c.save();return str(path)
