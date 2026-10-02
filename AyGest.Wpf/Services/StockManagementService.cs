using Microsoft.Data.Sqlite;
namespace AyGest.Wpf.Services;

public sealed class StockManagementService
{
    readonly Data.AppDb db;
    public StockManagementService(Data.AppDb db)=>this.db=db;
    static string Now()=>DateTime.UtcNow.ToString("O");

    public long DefaultWarehouse(long companyId)
    {
        using var c=db.Open(); using var q=c.CreateCommand();
        q.CommandText="SELECT id FROM warehouses WHERE company_id=@c AND active=1 ORDER BY is_default DESC,id LIMIT 1";
        q.Parameters.AddWithValue("@c",companyId);
        var value=q.ExecuteScalar();
        if(value is not null)return Convert.ToInt64(value);
        q.Parameters.Clear(); q.CommandText="INSERT INTO warehouses(company_id,name,code,is_default) VALUES(@c,'Armazém principal','ARM-01',1);SELECT last_insert_rowid();";
        q.Parameters.AddWithValue("@c",companyId); return Convert.ToInt64(q.ExecuteScalar());
    }

    public DataTableData GetStock(long companyId,long? warehouseId=null,string? search=null)
    {
        var warehouse=warehouseId??DefaultWarehouse(companyId);
        var sql="SELECT p.id,p.name,p.sku,p.barcode,COALESCE(w.name,'Armazém principal') warehouse,COALESCE(ws.quantity,0) quantity,p.min_stock,CASE WHEN COALESCE(ws.quantity,0)<=p.min_stock THEN 1 ELSE 0 END low_stock,p.cost,p.price,(COALESCE(ws.quantity,0)*p.cost) stock_cost FROM products p LEFT JOIN warehouse_stock ws ON ws.product_id=p.id AND ws.warehouse_id=@w LEFT JOIN warehouses w ON w.id=ws.warehouse_id WHERE p.company_id=@c AND p.active=1";
        if(!string.IsNullOrWhiteSpace(search))sql+=" AND (p.name LIKE @s OR p.sku LIKE @s OR p.barcode LIKE @s)";
        sql+=" ORDER BY p.name";
        var p=new List<(string,object)> {("@c",companyId),("@w",warehouse)};
        if(!string.IsNullOrWhiteSpace(search))p.Add(("@s",$"%{search.Trim()}%"));
        return new BusinessService(db).Query(sql,p.ToArray());
    }

    public long CreateWarehouse(long companyId,string name,string code,bool isDefault=false)
    {
        if(string.IsNullOrWhiteSpace(name)||string.IsNullOrWhiteSpace(code))throw new InvalidOperationException("Nome e código do armazém são obrigatórios.");
        using var c=db.Open();using var tx=c.BeginTransaction();using var q=c.CreateCommand();q.Transaction=tx;
        if(isDefault){q.CommandText="UPDATE warehouses SET is_default=0 WHERE company_id=@c";q.Parameters.AddWithValue("@c",companyId);q.ExecuteNonQuery();q.Parameters.Clear();}
        q.CommandText="INSERT INTO warehouses(company_id,name,code,is_default) VALUES(@c,@n,@code,@d);SELECT last_insert_rowid();";
        q.Parameters.AddWithValue("@c",companyId);q.Parameters.AddWithValue("@n",name.Trim());q.Parameters.AddWithValue("@code",code.Trim().ToUpperInvariant());q.Parameters.AddWithValue("@d",isDefault?1:0);
        var id=Convert.ToInt64(q.ExecuteScalar());tx.Commit();return id;
    }

    public void Receive(long companyId,long warehouseId,long productId,decimal quantity,decimal unitCost,string reason)
    {
        if(quantity<=0)throw new InvalidOperationException("A quantidade de entrada deve ser maior que zero.");
        using var c=db.Open();using var tx=c.BeginTransaction();using var q=c.CreateCommand();q.Transaction=tx;
        EnsureProductBelongs(q,companyId,productId);EnsureWarehouseBelongs(q,companyId,warehouseId);
        UpsertWarehouseStock(q,warehouseId,productId,quantity);if(IsDefault(q,warehouseId))UpsertLegacyStock(q,productId,quantity);
        q.Parameters.Clear();q.CommandText="INSERT INTO stock_documents(company_id,warehouse_id,type,number,reason,created_at) VALUES(@c,@w,'RECEIPT',@n,@r,@d);SELECT last_insert_rowid();";q.Parameters.AddWithValue("@c",companyId);q.Parameters.AddWithValue("@w",warehouseId);q.Parameters.AddWithValue("@n",$"ENT-{DateTime.Now:yyyyMMddHHmmssfff}");q.Parameters.AddWithValue("@r",reason??"");q.Parameters.AddWithValue("@d",Now());var doc=Convert.ToInt64(q.ExecuteScalar());
        q.Parameters.Clear();q.CommandText="INSERT INTO stock_document_items(document_id,product_id,quantity,unit_cost) VALUES(@d,@p,@q,@u)";q.Parameters.AddWithValue("@d",doc);q.Parameters.AddWithValue("@p",productId);q.Parameters.AddWithValue("@q",quantity);q.Parameters.AddWithValue("@u",unitCost);q.ExecuteNonQuery();
        q.Parameters.Clear();q.CommandText="INSERT INTO stock_movements(product_id,type,quantity,reference,created_at) VALUES(@p,'RECEIPT',@q,@r,@d)";q.Parameters.AddWithValue("@p",productId);q.Parameters.AddWithValue("@q",quantity);q.Parameters.AddWithValue("@r",doc);q.Parameters.AddWithValue("@d",Now());q.ExecuteNonQuery();
        if(unitCost>0){q.Parameters.Clear();q.CommandText="UPDATE products SET cost=@u WHERE id=@p AND company_id=@c";q.Parameters.AddWithValue("@u",unitCost);q.Parameters.AddWithValue("@p",productId);q.Parameters.AddWithValue("@c",companyId);q.ExecuteNonQuery();}
        tx.Commit();
    }

    public void Adjust(long companyId,long warehouseId,long productId,decimal delta,string reason)
    {
        if(delta==0)throw new InvalidOperationException("O ajuste não pode ser zero.");
        using var c=db.Open();using var tx=c.BeginTransaction();using var q=c.CreateCommand();q.Transaction=tx;EnsureProductBelongs(q,companyId,productId);EnsureWarehouseBelongs(q,companyId,warehouseId);var current=WarehouseQuantity(q,warehouseId,productId);if(current+delta<0)throw new InvalidOperationException($"Stock insuficiente. Disponível: {current:0.##}.");UpsertWarehouseStock(q,warehouseId,productId,delta);if(IsDefault(q,warehouseId))UpsertLegacyStock(q,productId,delta);q.Parameters.Clear();q.CommandText="INSERT INTO stock_movements(product_id,type,quantity,reference,created_at) VALUES(@p,'ADJUST',@q,@r,@d)";q.Parameters.AddWithValue("@p",productId);q.Parameters.AddWithValue("@q",delta);q.Parameters.AddWithValue("@r",reason??"");q.Parameters.AddWithValue("@d",Now());q.ExecuteNonQuery();tx.Commit();
    }

    public void Transfer(long companyId,long fromWarehouse,long toWarehouse,long productId,decimal quantity,string reason)
    {
        if(fromWarehouse==toWarehouse)throw new InvalidOperationException("A origem e o destino devem ser diferentes.");if(quantity<=0)throw new InvalidOperationException("A quantidade deve ser maior que zero.");
        using var c=db.Open();using var tx=c.BeginTransaction();using var q=c.CreateCommand();q.Transaction=tx;EnsureProductBelongs(q,companyId,productId);EnsureWarehouseBelongs(q,companyId,fromWarehouse);EnsureWarehouseBelongs(q,companyId,toWarehouse);var current=WarehouseQuantity(q,fromWarehouse,productId);if(current<quantity)throw new InvalidOperationException($"Stock insuficiente na origem. Disponível: {current:0.##}.");UpsertWarehouseStock(q,fromWarehouse,productId,-quantity);UpsertWarehouseStock(q,toWarehouse,productId,quantity);if(IsDefault(q,fromWarehouse))UpsertLegacyStock(q,productId,-quantity);if(IsDefault(q,toWarehouse))UpsertLegacyStock(q,productId,quantity);q.Parameters.Clear();q.CommandText="INSERT INTO stock_transfers(company_id,from_warehouse_id,to_warehouse_id,number,reason,created_at) VALUES(@c,@f,@t,@n,@r,@d);SELECT last_insert_rowid();";q.Parameters.AddWithValue("@c",companyId);q.Parameters.AddWithValue("@f",fromWarehouse);q.Parameters.AddWithValue("@t",toWarehouse);q.Parameters.AddWithValue("@n",$"TR-{DateTime.Now:yyyyMMddHHmmssfff}");q.Parameters.AddWithValue("@r",reason??"");q.Parameters.AddWithValue("@d",Now());var id=Convert.ToInt64(q.ExecuteScalar());q.Parameters.Clear();q.CommandText="INSERT INTO stock_transfer_items(transfer_id,product_id,quantity) VALUES(@i,@p,@q)";q.Parameters.AddWithValue("@i",id);q.Parameters.AddWithValue("@p",productId);q.Parameters.AddWithValue("@q",quantity);q.ExecuteNonQuery();q.Parameters.Clear();q.CommandText="INSERT INTO stock_movements(product_id,type,quantity,reference,created_at) VALUES(@p,'TRANSFER_OUT',@q,@r,@d),(@p,'TRANSFER_IN',@q,@r,@d)";q.Parameters.AddWithValue("@p",productId);q.Parameters.AddWithValue("@q",quantity);q.Parameters.AddWithValue("@r",id);q.Parameters.AddWithValue("@d",Now());q.ExecuteNonQuery();tx.Commit();
    }

    public void InventoryCount(long companyId,long warehouseId,long productId,decimal counted,string reason)
    {
        if(counted<0)throw new InvalidOperationException("A contagem não pode ser negativa.");using var c=db.Open();using var tx=c.BeginTransaction();using var q=c.CreateCommand();q.Transaction=tx;EnsureProductBelongs(q,companyId,productId);EnsureWarehouseBelongs(q,companyId,warehouseId);var system=WarehouseQuantity(q,warehouseId,productId);var difference=counted-system;if(difference!=0){UpsertWarehouseStock(q,warehouseId,productId,difference);if(IsDefault(q,warehouseId))UpsertLegacyStock(q,productId,difference);}q.Parameters.Clear();q.CommandText="INSERT INTO stock_inventory_counts(company_id,warehouse_id,product_id,system_quantity,counted_quantity,difference,reason,created_at) VALUES(@c,@w,@p,@s,@cnt,@d,@r,@x)";q.Parameters.AddWithValue("@c",companyId);q.Parameters.AddWithValue("@w",warehouseId);q.Parameters.AddWithValue("@p",productId);q.Parameters.AddWithValue("@s",system);q.Parameters.AddWithValue("@cnt",counted);q.Parameters.AddWithValue("@d",difference);q.Parameters.AddWithValue("@r",reason??"");q.Parameters.AddWithValue("@x",Now());q.ExecuteNonQuery();if(difference!=0){q.Parameters.Clear();q.CommandText="INSERT INTO stock_movements(product_id,type,quantity,reference,created_at) VALUES(@p,'INVENTORY',@q,@r,@d)";q.Parameters.AddWithValue("@p",productId);q.Parameters.AddWithValue("@q",difference);q.Parameters.AddWithValue("@r",reason??"");q.Parameters.AddWithValue("@d",Now());q.ExecuteNonQuery();}tx.Commit();
    }

    static void EnsureProductBelongs(SqliteCommand q,long company,long product){q.Parameters.Clear();q.CommandText="SELECT COUNT(*) FROM products WHERE id=@p AND company_id=@c AND active=1";q.Parameters.AddWithValue("@p",product);q.Parameters.AddWithValue("@c",company);if(Convert.ToInt32(q.ExecuteScalar())!=1)throw new InvalidOperationException("Produto inválido ou pertencente a outra empresa.");}
    static void EnsureWarehouseBelongs(SqliteCommand q,long company,long warehouse){q.Parameters.Clear();q.CommandText="SELECT COUNT(*) FROM warehouses WHERE id=@w AND company_id=@c AND active=1";q.Parameters.AddWithValue("@w",warehouse);q.Parameters.AddWithValue("@c",company);if(Convert.ToInt32(q.ExecuteScalar())!=1)throw new InvalidOperationException("Armazém inválido ou pertencente a outra empresa.");}
    static decimal WarehouseQuantity(SqliteCommand q,long warehouse,long product){q.Parameters.Clear();q.CommandText="SELECT quantity FROM warehouse_stock WHERE warehouse_id=@w AND product_id=@p";q.Parameters.AddWithValue("@w",warehouse);q.Parameters.AddWithValue("@p",product);return Convert.ToDecimal(q.ExecuteScalar()??0);}
    static bool IsDefault(SqliteCommand q,long warehouse){q.Parameters.Clear();q.CommandText="SELECT is_default FROM warehouses WHERE id=@w";q.Parameters.AddWithValue("@w",warehouse);return Convert.ToInt32(q.ExecuteScalar()??0)==1;}
    static void UpsertWarehouseStock(SqliteCommand q,long warehouse,long product,decimal delta){q.Parameters.Clear();q.CommandText="INSERT INTO warehouse_stock(warehouse_id,product_id,quantity) VALUES(@w,@p,@q) ON CONFLICT(warehouse_id,product_id) DO UPDATE SET quantity=quantity+excluded.quantity";q.Parameters.AddWithValue("@w",warehouse);q.Parameters.AddWithValue("@p",product);q.Parameters.AddWithValue("@q",delta);q.ExecuteNonQuery();}
    static void UpsertLegacyStock(SqliteCommand q,long product,decimal delta){q.Parameters.Clear();q.CommandText="INSERT INTO stock(product_id,quantity) VALUES(@p,@q) ON CONFLICT(product_id) DO UPDATE SET quantity=quantity+excluded.quantity";q.Parameters.AddWithValue("@p",product);q.Parameters.AddWithValue("@q",delta);q.ExecuteNonQuery();}
}
