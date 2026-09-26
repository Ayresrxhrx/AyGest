using System.Windows;
namespace AyGest.Wpf;
public partial class MainWindow
{
 void OpenSettings_Click(object sender, RoutedEventArgs e)
 {
  var w=new SettingsWindow(db,svc,companyId){Owner=this};
  if(w.ShowDialog()==true) Dashboard_Click(this,new RoutedEventArgs());
 }
}