using Microsoft.Data.Sqlite;
namespace AyGest.Wpf.Services;

public sealed class ExtendedManagementService
{
    readonly Data.AppDb db;
    public ExtendedManagementService(Data.AppDb db) => this.db = db;

    public void EnsureSchema()
    {
        using var c = db.Open();
        using var q = c.CreateCommand();
        q.CommandText = @"
CREATE TABLE IF NOT EXISTS warehouses(
 id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER NOT NULL, name TEXT NOT NULL,
 code TEXT NOT NULL, address TEXT, active INTEGER NOT NULL DEFAULT 1,
 UNIQUE(company_id,name), UNIQUE(company_id,code), FOREIGN KEY(company_id) REFERENCES companies(id));
CREATE TABLE IF NOT EXISTS warehouse_stock(
 id INTEGER PRIMARY KEY AUTOINCREMENT, warehouse_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
 quantity REAL NOT NULL DEFAULT 0, UNIQUE(warehouse_id,product_id),
 FOREIGN KEY(warehouse_id) REFERENCES warehouses(id), FOREIGN KEY(product_id) REFERENCES products(id));
CREATE TABLE IF NOT EXISTS stock_transfers(
 id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER NOT NULL, from_warehouse_id INTEGER NOT NULL,
 to_warehouse_id INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'completed', notes TEXT,
 created_at TEXT NOT NULL, FOREIGN KEY(company_id) REFERENCES companies(id));
CREATE TABLE IF NOT EXISTS stock_transfer_items(
 id INTEGER PRIMARY KEY AUTOINCREMENT, transfer_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
 quantity REAL NOT NULL, FOREIGN KEY(transfer_id) REFERENCES stock_transfers(id) ON DELETE CASCADE,
 FOREIGN KEY(product_id) REFERENCES products(id));
CREATE TABLE IF NOT EXISTS receivables(
 id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER NOT NULL, customer_id INTEGER,
 invoice_id INTEGER, description TEXT, due_date TEXT, amount REAL NOT NULL,
 paid_amount REAL NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL,
 FOREIGN KEY(company_id) REFERENCES companies(id), FOREIGN KEY(customer_id) REFERENCES customers(id),
 FOREIGN KEY(invoice_id) REFERENCES invoices(id));
CREATE TABLE IF NOT EXISTS receivable_payments(
 id INTEGER PRIMARY KEY AUTOINCREMENT, receivable_id INTEGER NOT NULL, amount REAL NOT NULL,
 payment_method_id INTEGER, reference TEXT, created_at TEXT NOT NULL,
 FOREIGN KEY(receivable_id) REFERENCES receivables(id) ON DELETE CASCADE,
 FOREIGN KEY(payment_method_id) REFERENCES payment_methods(id));
CREATE TABLE IF NOT EXISTS payables(
 id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER NOT NULL, supplier_id INTEGER,
 purchase_id INTEGER, description TEXT, due_date TEXT, amount REAL NOT NULL,
 paid_amount REAL NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL,
 FOREIGN KEY(company_id) REFERENCES companies(id), FOREIGN KEY(supplier_id) REFERENCES suppliers(id),
 FOREIGN KEY(purchase_id) REFERENCES purchases(id));
CREATE TABLE IF NOT EXISTS payable_payments(
 id INTEGER PRIMARY KEY AUTOINCREMENT, payable_id INTEGER NOT NULL, amount REAL NOT NULL,
 payment_method_id INTEGER, reference TEXT, created_at TEXT NOT NULL,
 FOREIGN KEY(payable_id) REFERENCES payables(id) ON DELETE CASCADE,
 FOREIGN KEY(payment_method_id) REFERENCES payment_methods(id));
CREATE TABLE IF NOT EXISTS sales_returns(
 id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER NOT NULL, invoice_id INTEGER,
 number TEXT NOT NULL, reason TEXT, total REAL NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'issued',
 created_at TEXT NOT NULL, FOREIGN KEY(company_id) REFERENCES companies(id), FOREIGN KEY(invoice_id) REFERENCES invoices(id));
CREATE TABLE IF NOT EXISTS sales_return_items(
 id INTEGER PRIMARY KEY AUTOINCREMENT, return_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
 quantity REAL NOT NULL, unit_price REAL NOT NULL, line_total REAL NOT NULL,
 FOREIGN KEY(return_id) REFERENCES sales_returns(id) ON DELETE CASCADE, FOREIGN KEY(product_id) REFERENCES products(id));
CREATE TABLE IF NOT EXISTS expenses(
 id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER NOT NULL, category TEXT NOT NULL,
 description TEXT, amount REAL NOT NULL, payment_method_id INTEGER, created_at TEXT NOT NULL,
 FOREIGN KEY(company_id) REFERENCES companies(id), FOREIGN KEY(payment_method_id) REFERENCES payment_methods(id));
CREATE TABLE IF NOT EXISTS discounts(
 id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER NOT NULL, name TEXT NOT NULL,
 type TEXT NOT NULL DEFAULT 'percent', value REAL NOT NULL, active INTEGER NOT NULL DEFAULT 1,
 starts_at TEXT, ends_at TEXT, UNIQUE(company_id,name), FOREIGN KEY(company_id) REFERENCES companies(id));
CREATE TABLE IF NOT EXISTS product_barcodes(
 id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL, barcode TEXT NOT NULL UNIQUE,
 FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS system_backups(
 id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER NOT NULL, file_path TEXT NOT NULL,
 created_at TEXT NOT NULL, size_bytes INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(company_id) REFERENCES companies(id));
CREATE TABLE IF NOT EXISTS app_permissions(
 id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER NOT NULL, role TEXT NOT NULL,
 permission TEXT NOT NULL, allowed INTEGER NOT NULL DEFAULT 1, UNIQUE(company_id,role,permission),
 FOREIGN KEY(company_id) REFERENCES companies(id));
CREATE INDEX IF NOT EXISTS idx_invoices_company_date ON invoices(company_id,created_at);
CREATE INDEX IF NOT EXISTS idx_products_company_active ON products(company_id,active);
CREATE INDEX IF NOT EXISTS idx_stock_movements_product_date ON stock_movements(product_id,created_at);
CREATE INDEX IF NOT EXISTS idx_receivables_company_status ON receivables(company_id,status);
CREATE INDEX IF NOT EXISTS idx_payables_company_status ON payables(company_id,status);
";
        q.ExecuteNonQuery();
    }

    public long AddWarehouse(long companyId,string name,string code,string address="")
    {
        if(string.IsNullOrWhiteSpace(name)||string.IsNullOrWhiteSpace(code)) throw new InvalidOperationException("Nome e código do armazém são obrigatórios.");
        using var c=db.Open(); using var q=c.CreateCommand();
        q.CommandText="INSERT INTO warehouses(company_id,name,code,address) VALUES(@c,@n,@co,@a);SELECT last_insert_rowid();";
        q.Parameters.AddWithValue("@c",companyId);q.Parameters.AddWithValue("@n",name.Trim());q.Parameters.AddWithValue("@co",code.Trim().ToUpperInvariant());q.Parameters.AddWithValue("@a",address??"");
        return Convert.ToInt64(q.ExecuteScalar());
    }

    public void AddExpense(long companyId,string category,string description,decimal amount,long? paymentMethodId)
    {
        if(amount<=0) throw new InvalidOperationException("O valor da despesa deve ser maior que zero.");
        Execute("INSERT INTO expenses(company_id,category,description,amount,payment_method_id,created_at) VALUES(@c,@cat,@d,@a,@p,@x)",("@c",companyId),("@cat",category),("@d",description),("@a",amount),("@p",paymentMethodId??(object)DBNull.Value),("@x",DateTime.UtcNow.ToString("O")));
    }

    public void AddReceivable(long companyId,long? customerId,long? invoiceId,string description,DateTime? dueDate,decimal amount)
    {
        if(amount<=0) throw new InvalidOperationException("O valor a receber deve ser maior que zero.");
        Execute("INSERT INTO receivables(company_id,customer_id,invoice_id,description,due_date,amount,created_at) VALUES(@c,@u,@i,@d,@due,@a,@x)",("@c",companyId),("@u",customerId??(object)DBNull.Value),("@i",invoiceId??(object)DBNull.Value),("@d",description),("@due",dueDate?.ToString("yyyy-MM-dd")??(object)DBNull.Value),("@a",amount),("@x",DateTime.UtcNow.ToString("O")));
    }

    public void AddPayable(long companyId,long? supplierId,long? purchaseId,string description,DateTime? dueDate,decimal amount)
    {
        if(amount<=0) throw new InvalidOperationException("O valor a pagar deve ser maior que zero.");
        Execute("INSERT INTO payables(company_id,supplier_id,purchase_id,description,due_date,amount,created_at) VALUES(@c,@s,@i,@d,@due,@a,@x)",("@c",companyId),("@s",supplierId??(object)DBNull.Value),("@i",purchaseId??(object)DBNull.Value),("@d",description),("@due",dueDate?.ToString("yyyy-MM-dd")??(object)DBNull.Value),("@a",amount),("@x",DateTime.UtcNow.ToString("O")));
    }

    public void AddDiscount(long companyId,string name,string type,decimal value)
    {
        if(value<0) throw new InvalidOperationException("O desconto não pode ser negativo.");
        if(type=="percent"&&value>100) throw new InvalidOperationException("Um desconto percentual não pode exceder 100%.");
        Execute("INSERT INTO discounts(company_id,name,type,value) VALUES(@c,@n,@t,@v)",("@c",companyId),("@n",name),("@t",type),("@v",value));
    }

    void Execute(string sql,params (string,object)[] p){using var c=db.Open();using var q=c.CreateCommand();q.CommandText=sql;foreach(var x in p)q.Parameters.AddWithValue(x.Item1,x.Item2??DBNull.Value);q.ExecuteNonQuery();}
}