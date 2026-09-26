using System.Windows;
namespace AyGest.Wpf;
public partial class MainWindow : Window {
 public MainWindow(){InitializeComponent();}
 void Open(string title,string text){PageTitle.Text=title; ContentFrame.Content=new System.Windows.Controls.Border{Padding=new Thickness(30),Child=new System.Windows.Controls.TextBlock{Text=text,FontSize=22,Foreground=FindResource("TextBrush") as System.Windows.Media.Brush}};}
 void Dashboard_Click(object s,RoutedEventArgs e)=>Open("Dashboard","Visão geral: vendas, caixa, stock, clientes e indicadores.");
 void Invoices_Click(object s,RoutedEventArgs e)=>Open("Facturação","Facturas, documentos, estados, impressão A4/POS e anulações.");
 void Sales_Click(object s,RoutedEventArgs e)=>Open("Vendas / POS","Ponto de venda, carrinho, pagamentos e emissão de factura.");
 void Products_Click(object s,RoutedEventArgs e)=>Open("Produtos","Produtos, categorias, preços, IVA, códigos e margens.");
 void Stock_Click(object s,RoutedEventArgs e)=>Open("Stock","Inventário, entradas, saídas, ajustes e stock mínimo.");
 void Purchases_Click(object s,RoutedEventArgs e)=>Open("Compras","Fornecedores, compras, custos e entrada automática em stock.");
 void Customers_Click(object s,RoutedEventArgs e)=>Open("Clientes","Cadastro, histórico de compras e documentos.");
 void Suppliers_Click(object s,RoutedEventArgs e)=>Open("Fornecedores","Cadastro e histórico de compras.");
 void Cash_Click(object s,RoutedEventArgs e)=>Open("Financeiro / Caixa","Abertura, movimentos, pagamentos, despesas e fecho.");
 void Reports_Click(object s,RoutedEventArgs e)=>Open("Relatórios","Vendas, compras, IVA, margem, stock e desempenho.");
 void Users_Click(object s,RoutedEventArgs e)=>Open("Utilizadores","Utilizadores, perfis e permissões.");
 void Audit_Click(object s,RoutedEventArgs e)=>Open("Auditoria","Histórico de operações e alterações.");
 void License_Click(object s,RoutedEventArgs e)=>Open("Licenciamento","Activação, plano, validade e estado da licença.");
 void Settings_Click(object s,RoutedEventArgs e)=>Open("Configurações","Empresa, impostos, documentos, impressoras e sistema.");
}