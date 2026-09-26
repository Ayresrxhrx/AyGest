from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal

class BusinessRuleError(ValueError): pass

def calculate_totals(lines, vat_rate=0):
    subtotal=Decimal('0')
    for line in lines:
        qty=Decimal(str(line.get('quantity',0))); price=Decimal(str(line.get('unit_price',0)))
        if qty<=0: raise BusinessRuleError('A quantidade deve ser maior que zero.')
        if price<0: raise BusinessRuleError('O preço não pode ser negativo.')
        subtotal += qty*price
    vat=(subtotal*Decimal(str(vat_rate))/Decimal('100')).quantize(Decimal('0.01'))
    return subtotal.quantize(Decimal('0.01')),vat,(subtotal+vat).quantize(Decimal('0.01'))

def available_stock(physical,reserved):
    return Decimal(str(physical))-Decimal(str(reserved))

def require_stock(physical,reserved,quantity,product_name='Produto'):
    if Decimal(str(quantity))<=0: raise BusinessRuleError('A quantidade deve ser maior que zero.')
    available=available_stock(physical,reserved)
    if Decimal(str(quantity))>available: raise BusinessRuleError(f'Stock disponível insuficiente para {product_name}. Disponível: {available}.')
    return available

def document_state_transition(current,target):
    allowed={'draft':{'issued','cancelled'},'issued':{'cancelled'},'cancelled':set()}
    if target not in allowed.get(current,set()): raise BusinessRuleError(f'Transição inválida: {current} → {target}.')
    return target

def cancellation_metadata(reason,user_id):
    if not str(reason or '').strip(): raise BusinessRuleError('O motivo da anulação é obrigatório.')
    return {'reason':str(reason).strip(),'user_id':user_id,'cancelled_at':datetime.now(timezone.utc).isoformat()}
