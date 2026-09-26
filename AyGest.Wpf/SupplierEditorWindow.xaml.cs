using System.Windows;using System.Windows.Controls;
namespace AyGest.Wpf;
public partial class SupplierEditorWindow:Window{
 public string Code=>CodeBox.Text.Trim();public string SupplierName=>NameBox.Text.Trim();public string TaxId=>TaxIdBox.Text.Trim();public string Phone=>PhoneBox.Text.Trim();public string Email=>EmailBox.Text.Trim();public string Website=>WebsiteBox.Text.Trim();public string Address=>AddressBox.Text.Trim();public string Contact=>ContactBox.Text.Trim();public string PaymentTerms=>PaymentTermsBox.Text.Trim();public string Bank=>BankBox.Text.Trim();public string Notes=>NotesBox.Text.Trim();public string Status=>(StatusBox.SelectedItem as ComboBoxItem)?.Content?.ToString()??"Activo";
 public SupplierEditorWindow(){InitializeComponent();StatusBox.SelectedIndex=0;}
 public SupplierEditorWindow(SupplierRow x):this(){CodeBox.Text=x.Code;CodeBox.IsEnabled=false;NameBox.Text=x.Name;TaxIdBox.Text=x.TaxId;PhoneBox.Text=x.Phone;EmailBox.Text=x.Email;}
 void Save_Click(object s,RoutedEventArgs e){if(string.IsNullOrWhiteSpace(SupplierName)){MessageBox.Show("O nome do fornecedor é obrigatório.","Validação",MessageBoxButton.OK,MessageBoxImage.Warning);return;}if(!string.IsNullOrWhiteSpace(Email)&&!Email.Contains('@')){MessageBox.Show("Introduza um e-mail válido.","Validação",MessageBoxButton.OK,MessageBoxImage.Warning);return;}DialogResult=true;}
 void Cancel_Click(object s,RoutedEventArgs e)=>DialogResult=false;
 public record SupplierRow(long Id,string Code,string Name,string TaxId,string Phone,string Email,string Website,string Address,string Contact,string PaymentTerms,string Bank,string Notes,string Status,int PurchaseCount,decimal Payable);
}