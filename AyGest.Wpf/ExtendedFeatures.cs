using System.Data;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Microsoft.Win32;

namespace AyGest.Wpf;

public partial class MainWindow
{
    readonly Services.ExtendedManagementService extended = new(new Data.AppDb());

    static MainWindow()
    {
        EventManager.RegisterClassHandler(typeof(MainWindow), Window.LoadedEvent, new RoutedEventHandler(InjectAdvancedNavigation));
    }

    static void InjectAdvancedNavigation(object sender, RoutedEventArgs e)
    {
        if (sender is not MainWindow w) return;
        try { w.extended.EnsureSchema(); } catch { return; }
        var root = FindPanels(w.Content as DependencyObject).FirstOrDefault(p => p.Children.OfType<Button>().Any(b => ButtonText(b) == "Relatórios"));
        if (root is null || root.Children.OfType<Button>().Any(b => ButtonText(b) == "Armazéns")) return;
        var report = root.Children.OfType<Button>().First(b => ButtonText(b) == "Relatórios");
        var index = root.Children.IndexOf(report) + 1;
        root.Children.Insert(index++, w.Nav("Armazéns", "\uE8B7", (_,__) => w.Warehouses_Click()));
        root.Children.Insert(index++, w.Nav("Devoluções", "\uE7BA", (_,__) => w.Returns_Click()));
        root.Children.Insert(index++, w.Nav("Contas a receber", "\uE8C8", (_,__) => w.Receivables_Click()));
        root.Children.Insert(index++, w.Nav("Contas a pagar", "\uE8C8", (_,__) => w.Payables_Click()));
        root.Children.Insert(index++, w.Nav("Despesas", "\uE8C8", (_,__) => w.Expenses_Click()));
        var settings = root.Children.OfType<Button>().FirstOrDefault(b => ButtonText(b) == "Configurações");
        if (settings != null) root.Children.Insert(root.Children.IndexOf(settings), w.Nav("Configuração avançada", "\uE713", (_,__) => w.AdvancedSettings_Click(w,new())));
    }

    static IEnumerable<StackPanel> FindPanels(DependencyObject? root)
    {
        if (root is StackPanel p) yield return p;
        if (root is null) yield break;
        for (var i=0;i<VisualTreeHelper.GetChildrenCount(root);i++)
            foreach(var x in FindPanels(VisualTreeHelper.GetChild(root,i))) yield return x;
    }

    static string ButtonText(Button b) => b.Content is StackPanel p ? p.Children.OfType<TextBlock>().LastOrDefault()?.Text ?? "" : b.Content?.ToString() ?? "";

    Button Nav(string text,string icon,RoutedEventHandler click)
    {
        var b=new Button{Style=(Style)FindResource("SidebarButton"),Content=new StackPanel{Orientation=Orientation.Horizontal}};
        var p=(StackPanel)b.Content;
        p.Children.Add(new TextBlock{Text=icon,FontFamily=new FontFamily("Segoe MDL2 Assets"),FontSize=15,Width=28});
        p.Children.Add(new TextBlock{Text=text,VerticalAlignment=VerticalAlignment.Center});
        b.Click+=click; return b;
    }

    void Warehouses_Click()
    {
        var add=B("+ Novo armazém",(_,_)=>AddWarehouse());
        var toggle=Secondary("Activar / desactivar",(_,_)=>ToggleWarehouse());
        var p=Header("Armazéns","Localizações e stock independente por armazém",add,toggle);
        grid=Table("SELECT id,name,code,address,active FROM warehouses WHERE company_id=@c ORDER BY name",("@c",companyId));
        p.Children.Add(grid); Show("Armazéns",p);
    }

    void AddWarehouse()
    {
        var f=Form("Novo armazém",("Nome",""),("Código",""),("Endereço","")); if(f==null)return;
        try{extended.AddWarehouse(companyId,f[0],f[1],f[2]);Warehouses_Click();}catch(Exception ex){Error(ex);}
    }

    void ToggleWarehouse()
    {
        if(grid.SelectedItem is not DataRowView r)return;
        try{svc.Execute("UPDATE warehouses SET active=CASE WHEN active=1 THEN 0 ELSE 1 END WHERE id=@i AND company_id=@c",("@i",Convert.ToInt64(r["id"])),("@c",companyId));Warehouses_Click();}catch(Exception ex){Error(ex);}
    }

    void Returns_Click()
    {
        var p=Header("Devoluções","Registo de devoluções de vendas e reposição de stock");
        p.Children.Add(Table("SELECT r.id,r.number,COALESCE(i.number,'—') factura,r.total,r.status,r.reason,r.created_at FROM sales_returns r LEFT JOIN invoices i ON i.id=r.invoice_id WHERE r.company_id=@c ORDER BY r.id DESC",("@c",companyId)));
        Show("Devoluções",p);
    }

    void Receivables_Click()
    {
        var add=B("+ Novo débito",(_,_)=>AddReceivable());
        var p=Header("Contas a receber","Clientes, crédito e valores pendentes",add);
        p.Children.Add(Table("SELECT r.id,COALESCE(c.name,'Consumidor final') cliente,COALESCE(i.number,'—') factura,r.description,r.due_date,r.amount,r.paid_amount,(r.amount-r.paid_amount) saldo,r.status FROM receivables r LEFT JOIN customers c ON c.id=r.customer_id LEFT JOIN invoices i ON i.id=r.invoice_id WHERE r.company_id=@c ORDER BY r.due_date",("@c",companyId)));
        Show("Contas a receber",p);
    }

    void AddReceivable()
    {
        var f=Form("Novo valor a receber",("ID cliente",""),("Descrição",""),("Vencimento (AAAA-MM-DD)",""),("Valor","0"));if(f==null)return;
        try{long? cid=string.IsNullOrWhiteSpace(f[0])?null:long.Parse(f[0]);DateTime? due=string.IsNullOrWhiteSpace(f[2])?null:DateTime.Parse(f[2]);extended.AddReceivable(companyId,cid,null,f[1],due,D(f[3]));Receivables_Click();}catch(Exception ex){Error(ex);}
    }

    void Payables_Click()
    {
        var add=B("+ Novo débito",(_,_)=>AddPayable());
        var p=Header("Contas a pagar","Fornecedores, compras e compromissos financeiros",add);
        p.Children.Add(Table("SELECT p.id,COALESCE(s.name,'—') fornecedor,COALESCE(po.number,'—') compra,p.description,p.due_date,p.amount,p.paid_amount,(p.amount-p.paid_amount) saldo,p.status FROM payables p LEFT JOIN suppliers s ON s.id=p.supplier_id LEFT JOIN purchases po ON po.id=p.purchase_id WHERE p.company_id=@c ORDER BY p.due_date",("@c",companyId)));
        Show("Contas a pagar",p);
    }

    void AddPayable()
    {
        var f=Form("Novo valor a pagar",("ID fornecedor",""),("Descrição",""),("Vencimento (AAAA-MM-DD)",""),("Valor","0"));if(f==null)return;
        try{long? sid=string.IsNullOrWhiteSpace(f[0])?null:long.Parse(f[0]);DateTime? due=string.IsNullOrWhiteSpace(f[2])?null:DateTime.Parse(f[2]);extended.AddPayable(companyId,sid,null,f[1],due,D(f[3]));Payables_Click();}catch(Exception ex){Error(ex);}
    }

    void Expenses_Click()
    {
        var add=B("+ Nova despesa",(_,_)=>AddExpense());
        var p=Header("Despesas","Custos operacionais e movimentos financeiros",add);
        p.Children.Add(Table("SELECT e.id,e.category,e.description,e.amount,COALESCE(pm.name,'—') pagamento,e.created_at FROM expenses e LEFT JOIN payment_methods pm ON pm.id=e.payment_method_id WHERE e.company_id=@c ORDER BY e.id DESC",("@c",companyId)));
        Show("Despesas",p);
    }

    void AddExpense()
    {
        var f=Form("Nova despesa",("Categoria",""),("Descrição",""),("Valor","0"),("ID método de pagamento",""));if(f==null)return;
        try{long? pm=string.IsNullOrWhiteSpace(f[3])?null:long.Parse(f[3]);extended.AddExpense(companyId,f[0],f[1],D(f[2]),pm);Expenses_Click();}catch(Exception ex){Error(ex);}
    }

    void AdvancedSettings_Click(object s,RoutedEventArgs e)
    {
        var p=Header("Configuração avançada","Descontos, backup, segurança e parâmetros operacionais",
            B("Novo desconto",(_,_)=>AddDiscount()),
            Secondary("Backup agora",(_,_)=>BackupNow()));
        p.Children.Add(Table("SELECT id,name,type,value,active,starts_at,ends_at FROM discounts WHERE company_id=@c ORDER BY name",("@c",companyId)));
        Show("Configuração avançada",p);
    }

    void AddDiscount()
    {
        var f=Form("Novo desconto",("Nome",""),("Tipo (percent/fixed)","percent"),("Valor","0"));if(f==null)return;
        try{if(f[1]!="percent"&&f[1]!="fixed")throw new InvalidOperationException("Tipo inválido. Use percent ou fixed.");extended.AddDiscount(companyId,f[0],f[1],D(f[2]));AdvancedSettings_Click(this,new());}catch(Exception ex){Error(ex);}
    }

    void BackupNow()
    {
        try
        {
            var dlg=new SaveFileDialog{Filter="Base de dados SQLite (*.db)|*.db",FileName=$"AyGest-Backup-{DateTime.Now:yyyyMMdd-HHmmss}.db"};
            if(dlg.ShowDialog()!=true)return;
            File.Copy(new Data.AppDb().Path,dlg.FileName,true);
            var info=new FileInfo(dlg.FileName);
            svc.Execute("INSERT INTO system_backups(company_id,file_path,created_at,size_bytes) VALUES(@c,@p,@d,@s)",("@c",companyId),("@p",dlg.FileName),("@d",DateTime.UtcNow.ToString("O")),("@s",info.Length));
            MessageBox.Show("Backup criado com sucesso.","AyGest",MessageBoxButton.OK,MessageBoxImage.Information);
        }catch(Exception ex){Error(ex);}
    }
}