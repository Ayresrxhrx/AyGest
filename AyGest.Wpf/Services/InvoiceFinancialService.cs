using Microsoft.Data.Sqlite;

namespace AyGest.Wpf.Services;

public sealed class InvoiceFinancialService
{
    readonly Data.AppDb db;
    public InvoiceFinancialService(Data.AppDb db)=>this.db=db;
    static string Now()=>DateTime.UtcNow.ToString("O");

    public decimal GetBalance(long companyId,long invoiceId)
    {
        using var c=db.Open();using var q=c.CreateCommand();
        q.CommandText="SELECT total,paid_amount,status FROM invoices WHERE id=@i AND company_id=@c";
        q.Parameters.AddWithValue("@i",invoiceId);q.Parameters.AddWithValue("@c",companyId);
        using var r=q.ExecuteReader();
        if(!r.Read())throw new InvalidOperationException("Factura não encontrada.");
        if(r.GetString(2)=="cancelled")return 0;
        return Math.Max(0,Convert.ToDecimal(r.GetValue(0))-Convert.ToDecimal(r.GetValue(1)));
    }

    public void RegisterPayment(long companyId,long invoiceId,decimal amount,string method,string? reference=null,string? notes=null)
    {
        if(amount<=0)throw new InvalidOperationException("O valor do pagamento deve ser maior que zero.");
        if(string.IsNullOrWhiteSpace(method))throw new InvalidOperationException("Seleccione o método de pagamento.");
        using var c=db.Open();using var tx=c.BeginTransaction();using var q=c.CreateCommand();q.Transaction=tx;
        q.CommandText="SELECT total,paid_amount,status,number FROM invoices WHERE id=@i AND company_id=@c";q.Parameters.AddWithValue("@i",invoiceId);q.Parameters.AddWithValue("@c",companyId);
        using var r=q.ExecuteReader();if(!r.Read())throw new InvalidOperationException("Factura não encontrada.");
        var total=Convert.ToDecimal(r.GetValue(0));var paid=Convert.ToDecimal(r.GetValue(1));var status=r.GetString(2);var number=r.GetString(3);r.Close();
        if(status=="cancelled")throw new InvalidOperationException("Não é possível receber uma factura anulada.");
        var balance=total-paid;if(amount>balance)throw new InvalidOperationException($"O pagamento excede o saldo da factura. Saldo: {balance:N2} MT.");
        q.Parameters.Clear();q.CommandText="SELECT id,affects_cash FROM payment_methods WHERE company_id=@c AND active=1 AND (code=@m OR name=@m) LIMIT 1";q.Parameters.AddWithValue("@c",companyId);q.Parameters.AddWithValue("@m",method);using var pm=q.ExecuteReader();if(!pm.Read())throw new InvalidOperationException("Método de pagamento inválido ou inactivo.");var paymentMethodId=Convert.ToInt64(pm.GetValue(0));var affectsCash=Convert.ToInt32(pm.GetValue(1))==1;pm.Close();
        q.Parameters.Clear();q.CommandText="INSERT INTO invoice_payments(invoice_id,company_id,payment_method_id,payment_method,amount,reference,notes,paid_at) VALUES(@i,@c,@p,@m,@a,@r,@n,@d)";q.Parameters.AddWithValue("@i",invoiceId);q.Parameters.AddWithValue("@c",companyId);q.Parameters.AddWithValue("@p",paymentMethodId);q.Parameters.AddWithValue("@m",method);q.Parameters.AddWithValue("@a",amount);q.Parameters.AddWithValue("@r",reference??"");q.Parameters.AddWithValue("@n",notes??"");q.Parameters.AddWithValue("@d",Now());q.ExecuteNonQuery();
        var newPaid=paid+amount;var newStatus=newPaid>=total?"paid":"partial";q.Parameters.Clear();q.CommandText="UPDATE invoices SET paid_amount=@p,payment_status=@s WHERE id=@i AND company_id=@c";q.Parameters.AddWithValue("@p",newPaid);q.Parameters.AddWithValue("@s",newStatus);q.Parameters.AddWithValue("@i",invoiceId);q.Parameters.AddWithValue("@c",companyId);q.ExecuteNonQuery();
        if(affectsCash){q.Parameters.Clear();q.CommandText="INSERT INTO cash_movements(session_id,type,description,amount,payment_method,created_at) SELECT id,'IN',@d,@a,@m,@x FROM cash_sessions WHERE company_id=@c AND status='open'";q.Parameters.AddWithValue("@d",$"Pagamento {number}");q.Parameters.AddWithValue("@a",amount);q.Parameters.AddWithValue("@m",method);q.Parameters.AddWithValue("@x",Now());q.Parameters.AddWithValue("@c",companyId);q.ExecuteNonQuery();}
        q.Parameters.Clear();q.CommandText="INSERT INTO audit_log(company_id,action,entity,entity_id,details,created_at) VALUES(@c,'PAYMENT','invoice',@i,@d,@x)";q.Parameters.AddWithValue("@c",companyId);q.Parameters.AddWithValue("@i",invoiceId);q.Parameters.AddWithValue("@d",$"Pagamento {amount:N2} MT; método {method}; estado {newStatus}");q.Parameters.AddWithValue("@x",Now());q.ExecuteNonQuery();tx.Commit();
    }

    public IReadOnlyList<(long id,string method,decimal amount,string reference,string paidAt)> Payments(long companyId,long invoiceId)
    {
        using var c=db.Open();using var q=c.CreateCommand();q.CommandText="SELECT id,payment_method,amount,COALESCE(reference,''),paid_at FROM invoice_payments WHERE company_id=@c AND invoice_id=@i ORDER BY id DESC";q.Parameters.AddWithValue("@c",companyId);q.Parameters.AddWithValue("@i",invoiceId);using var r=q.ExecuteReader();var result=new List<(long,string,decimal,string,string)>();while(r.Read())result.Add((Convert.ToInt64(r.GetValue(0)),Convert.ToString(r.GetValue(1))??"",Convert.ToDecimal(r.GetValue(2)),Convert.ToString(r.GetValue(3))??"",Convert.ToString(r.GetValue(4))??""));return result;
    }

    public DataTableData Receivables(long companyId)
    {
        using var c=db.Open();using var q=c.CreateCommand();q.CommandText="SELECT i.id,i.number,COALESCE(cu.name,'Consumidor final') cliente,i.total,i.paid_amount,(i.total-i.paid_amount) saldo,i.payment_status,i.due_date,i.created_at FROM invoices i LEFT JOIN customers cu ON cu.id=i.customer_id WHERE i.company_id=@c AND i.status!='cancelled' AND i.total-i.paid_amount>0 ORDER BY CASE WHEN i.due_date IS NULL THEN 1 ELSE 0 END,i.due_date,i.id DESC";q.Parameters.AddWithValue("@c",companyId);using var r=q.ExecuteReader();var t=new DataTableData();for(int i=0;i<r.FieldCount;i++)t.Columns.Add(r.GetName(i));while(r.Read()){var row=new object[r.FieldCount];for(int i=0;i<r.FieldCount;i++)row[i]=r.IsDBNull(i)?null!:r.GetValue(i);t.Rows.Add(row);}return t;
    }
}