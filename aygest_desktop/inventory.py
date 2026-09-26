from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone


class InventoryService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def list_products(self, tenant_id: str):
        return self.conn.execute("""
            SELECT p.*, COALESCE(SUM(s.quantity),0) quantity,
                   COALESCE(SUM(s.reserved),0) reserved,
                   COALESCE(SUM(s.quantity-s.reserved),0) available
            FROM products p LEFT JOIN stock s ON s.product_id=p.id AND s.tenant_id=p.tenant_id
            WHERE p.tenant_id=? AND p.active=1 GROUP BY p.id ORDER BY p.name COLLATE NOCASE
        """, (tenant_id,)).fetchall()

    def create_product(self, tenant_id, name, sku, barcode, category, unit, factor, purchase_price, sale_price, vat_rate, min_stock):
        if not name.strip() or not sku.strip():
            raise ValueError("Nome e SKU são obrigatórios.")
        if factor <= 0 or sale_price < 0 or purchase_price < 0 or min_stock < 0:
            raise ValueError("Os valores numéricos devem ser válidos e não negativos.")
        product_id = str(uuid.uuid4())
        self.conn.execute("INSERT INTO products VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,1)", (product_id, tenant_id, sku.strip(), barcode.strip(), name.strip(), category.strip(), unit, factor, purchase_price, sale_price, vat_rate, min_stock))
        self.conn.execute("INSERT INTO stock VALUES(?,?,?,?,?,?,?)", (str(uuid.uuid4()), tenant_id, product_id, "Principal", 0, 0, self.now()))
        return product_id

    def adjust_stock(self, tenant_id, product_id, quantity, movement_type, warehouse="Principal"):
        if quantity == 0:
            raise ValueError("A quantidade não pode ser zero.")
        sign = 1 if movement_type == "IN" else -1
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            row = self.conn.execute("SELECT quantity,reserved FROM stock WHERE tenant_id=? AND product_id=? AND warehouse=?", (tenant_id, product_id, warehouse)).fetchone()
            if not row:
                raise ValueError("Stock do produto não encontrado.")
            new_qty = row["quantity"] + sign * abs(quantity)
            if new_qty < row["reserved"]:
                raise ValueError("O stock físico não pode ficar abaixo do stock reservado.")
            self.conn.execute("UPDATE stock SET quantity=?,updated_at=? WHERE tenant_id=? AND product_id=? AND warehouse=?", (new_qty, self.now(), tenant_id, product_id, warehouse))
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def reserve(self, tenant_id, product_id, quantity, cashier_id, expires_at, warehouse="Principal"):
        if quantity <= 0:
            raise ValueError("A quantidade reservada deve ser maior que zero.")
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            row = self.conn.execute("SELECT quantity,reserved FROM stock WHERE tenant_id=? AND product_id=? AND warehouse=?", (tenant_id, product_id, warehouse)).fetchone()
            if not row or row["quantity"] - row["reserved"] < quantity:
                raise ValueError("Stock livre insuficiente para esta reserva.")
            reservation_id = str(uuid.uuid4())
            self.conn.execute("UPDATE stock SET reserved=reserved+?,updated_at=? WHERE tenant_id=? AND product_id=? AND warehouse=?", (quantity, self.now(), tenant_id, product_id, warehouse))
            self.conn.execute("INSERT INTO reservations VALUES(?,?,?,?,?,?,?,?,?)", (reservation_id, tenant_id, product_id, quantity, cashier_id, "active", expires_at, self.now()))
            self.conn.execute("COMMIT")
            return reservation_id
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def release_expired(self, tenant_id):
        now = self.now()
        rows = self.conn.execute("SELECT id,product_id,quantity FROM reservations WHERE tenant_id=? AND status='active' AND expires_at<=?", (tenant_id, now)).fetchall()
        for row in rows:
            self.conn.execute("UPDATE stock SET reserved=MAX(0,reserved-?),updated_at=? WHERE tenant_id=? AND product_id=?", (row["quantity"], now, tenant_id, row["product_id"]))
            self.conn.execute("UPDATE reservations SET status='expired' WHERE id=?", (row["id"],))
        return len(rows)

    @staticmethod
    def now():
        return datetime.now(timezone.utc).isoformat()
