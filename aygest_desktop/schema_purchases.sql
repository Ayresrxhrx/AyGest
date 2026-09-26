CREATE TABLE IF NOT EXISTS suppliers(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,name TEXT NOT NULL,nuit TEXT,phone TEXT,email TEXT,address TEXT);
CREATE TABLE IF NOT EXISTS purchases(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,document_no TEXT NOT NULL,supplier_id TEXT,total REAL NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'draft',created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS purchase_items(id TEXT PRIMARY KEY,purchase_id TEXT NOT NULL,product_id TEXT NOT NULL,quantity REAL NOT NULL,unit_cost REAL NOT NULL,line_total REAL NOT NULL);
