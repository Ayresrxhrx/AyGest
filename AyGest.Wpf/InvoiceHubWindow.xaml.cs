using System.Data;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using AyGest.Wpf.Services;
namespace AyGest.Wpf;
public partial class InvoiceHubWindow : Window
{
 readonly long companyId; readonly BusinessService svc; readonly MainWindow owner;
 public InvoiceHubWindow(MainWindow owner,long companyId){this.owner=owner;this.companyId=companyId;svc=new BusinessService(new Data.AppDb());InitializeComponent();LoadMetrics();}
 void LoadMetrics(){try{var today=svc.Query("SELECT COUNT(*),COALESCE(SUM(total),0) FROM invoices WHERE company_id=@c AND status='issued' AND date(created_at)=date('now')",("@c",companyId)).Rows.FirstOrDefault();SalesCount.Text=$"{Convert.ToInt32(today?[0]??0)} documentos";SalesToday.Text=$"{Convert.ToDecimal(today?[1]??0):N2} MT";var cancelled=svc.Query("SELECT COUNT(*) FROM invoices WHERE company_id=@c AND status='cancelled'",("@c",companyId)).Rows.FirstOrDefault();CancelledCount.Text=Convert.ToString(cancelled?[0])??"0";var pending=svc.Query("SELECT COUNT(*) FROM invoices WHERE company_id=@c AND status IN ('draft','pending')",("@c",companyId)).Rows.FirstOrDefault();PendingCount.Text=Convert.ToString(pending?[0])??"0";}catch(Exception ex){MessageBox.Show(ex.Message,"AyGest",MessageBoxButton.OK,MessageBoxImage.Error);}}
 void NewInvoice_Click(object s,RoutedEventArgs e){owner.GetType().GetMethod("NewInvoice",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.Invoke(owner,null);LoadMetrics();}
 void OpenInvoices_Click(object s,RoutedEventArgs e){Close();owner.GetType().GetMethod("Invoices_Click",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.Invoke(owner,new object[]{owner,new RoutedEventArgs()});}
 void OpenPos_Click(object s,RoutedEventArgs e){Close();owner.GetType().GetMethod("Sales_Click",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.Invoke(owner,new object[]{owner,new RoutedEventArgs()});}
 void OpenCash_Click(object s,RoutedEventArgs e){Close();owner.GetType().GetMethod("Cash_Click",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.Invoke(owner,new object[]{owner,new RoutedEventArgs()});}
 void OpenReports_Click(object s,RoutedEventArgs e){Close();owner.GetType().GetMethod("Reports_Click",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.Invoke(owner,new object[]{owner,new RoutedEventArgs()});}
 void OpenSettings_Click(object s,RoutedEventArgs e){Close();owner.GetType().GetMethod("Settings_Click",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.Invoke(owner,new object[]{owner,new RoutedEventArgs()});}
 void OpenCustomers_Click(object s,RoutedEventArgs e){Close();owner.GetType().GetMethod("Customers_Click",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.Invoke(owner,new object[]{owner,new RoutedEventArgs()});}
}