from __future__ import annotations
import re
from decimal import Decimal, InvalidOperation

class ValidationError(ValueError):
    pass

def required(value, label):
    value=str(value or '').strip()
    if not value: raise ValidationError(f'{label} é obrigatório.')
    return value

def positive(value, label, allow_zero=False):
    try: n=Decimal(str(value).replace(',','.'))
    except (InvalidOperation,ValueError): raise ValidationError(f'{label} deve ser numérico.')
    if n<0 or (n==0 and not allow_zero): raise ValidationError(f'{label} deve ser maior que zero.')
    return n

def email(value):
    value=str(value or '').strip()
    if value and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',value): raise ValidationError('E-mail inválido.')
    return value

def nuit(value):
    value=str(value or '').strip()
    if value and not re.fullmatch(r'\d{9,14}',value): raise ValidationError('NUIT inválido. Use apenas números.')
    return value

def phone(value):
    value=str(value or '').strip()
    if value and not re.fullmatch(r'[+\d][\d\s-]{7,19}',value): raise ValidationError('Telefone inválido.')
    return value
