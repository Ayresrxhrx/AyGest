using System.Windows;
namespace AyGest.Wpf;
public partial class MainWindow
{
    void InvoiceMap_Click(object sender,RoutedEventArgs e)
    {
        var hub=new InvoiceHubWindow(this,companyId){Owner=this};
        hub.ShowDialog();
    }
}