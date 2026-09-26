using System.Windows;using System.Windows.Controls;
namespace AyGest.Wpf;
public partial class UserEditorWindow:Window{
 public string Username=>UsernameBox.Text.Trim();public string FullName=>NameBox.Text.Trim();public string Email=>EmailBox.Text.Trim();public string Role=>(RoleBox.SelectedItem as ComboBoxItem)?.Content?.ToString()??"Consulta";public string Status=>(StatusBox.SelectedItem as ComboBoxItem)?.Content?.ToString()??"Activo";public string Password=>PasswordBox.Password;
 public UserEditorWindow(){InitializeComponent();RoleBox.SelectedIndex=0;StatusBox.SelectedIndex=0;}
 public UserEditorWindow(UsersWindow.UserRow u):this(){UsernameBox.Text=u.Username;UsernameBox.IsEnabled=false;NameBox.Text=u.FullName;EmailBox.Text=u.Email;RoleBox.SelectedIndex=Math.Max(0,RoleBox.Items.IndexOf(RoleBox.Items.OfType<ComboBoxItem>().FirstOrDefault(x=>x.Content?.ToString()==u.Role)));StatusBox.SelectedIndex=u.Status=="Activo"?0:1;}
 void Save_Click(object s,RoutedEventArgs e){if(string.IsNullOrWhiteSpace(Username)||string.IsNullOrWhiteSpace(FullName)){MessageBox.Show("Utilizador e nome completo são obrigatórios.","Validação",MessageBoxButton.OK,MessageBoxImage.Warning);return;}if(!UsernameBox.IsEnabled==false&&Password.Length<8){MessageBox.Show("A password deve ter pelo menos 8 caracteres.","Validação",MessageBoxButton.OK,MessageBoxImage.Warning);return;}DialogResult=true;}
 void Cancel_Click(object s,RoutedEventArgs e)=>DialogResult=false;
}
