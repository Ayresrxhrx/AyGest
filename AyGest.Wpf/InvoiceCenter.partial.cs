using System.Data;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace AyGest.Wpf;

public partial class MainWindow
{
    void InvoiceMap_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            var root = new StackPanel();
            root.Children.Add(Header("Centro de Facturação", "Visão geral e acesso rápido a todo o ciclo documental", B("+ Nova factura", (_, _) => NewInvoice()), Secondary("Consultar facturas", (_, _) => Invoices_Click(this, new RoutedEventArgs()))));

            var metrics = new UniformGrid { Columns = 4, Margin = new Thickness(0, 16, 0, 18) };
            var today = svc.Query("SELECT COUNT(*), COALESCE(SUM(total),0), COALESCE(SUM(vat),0) FROM invoices WHERE company_id=@c AND status='issued' AND date(created_at)=date('now')", ("@c", companyId)).Rows.FirstOrDefault();
            var pending = svc.Query("SELECT COUNT(*), COALESCE(SUM(total),0) FROM invoices WHERE company_id=@c AND status='issued' AND total>0 AND payment_method IS NULL", ("@c", companyId)).Rows.FirstOrDefault();
            var cancelled = svc.Query("SELECT COUNT(*) FROM invoices WHERE company_id=@c AND status='cancelled'", ("@c", companyId)).Rows.FirstOrDefault();
            metrics.Children.Add(Card("Vendas hoje", Money(today?[1])));
            metrics.Children.Add(Card("Documentos hoje", Convert.ToString(today?[0]) ?? "0"));
            metrics.Children.Add(Card("IVA hoje", Money(today?[2])));
            metrics.Children.Add(Card("Facturas anuladas", Convert.ToString(cancelled?[0]) ?? "0"));
            root.Children.Add(metrics);

            var flow = new Grid { Margin = new Thickness(0, 0, 0, 18) };
            flow.ColumnDefinitions.Add(new ColumnDefinition());
            flow.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(18) });
            flow.ColumnDefinitions.Add(new ColumnDefinition());
            flow.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(18) });
            flow.ColumnDefinitions.Add(new ColumnDefinition());
            flow.Children.Add(FlowCard("01", "Emitir", "Criar uma nova factura, seleccionar cliente, produtos, IVA e pagamento.", "Nova factura", (_, _) => NewInvoice()));
            var arrow1 = new TextBlock { Text = "›", FontSize = 28, Foreground = (Brush)FindResource("SubtleBrush"), HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center }; Grid.SetColumn(arrow1, 1); flow.Children.Add(arrow1);
            var consult = FlowCard("02", "Documentos", "Consultar, filtrar, anular e imprimir documentos emitidos.", "Abrir facturas", (_, _) => Invoices_Click(this, new RoutedEventArgs())); Grid.SetColumn(consult, 2); flow.Children.Add(consult);
            var arrow2 = new TextBlock { Text = "›", FontSize = 28, Foreground = (Brush)FindResource("SubtleBrush"), HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center }; Grid.SetColumn(arrow2, 3); flow.Children.Add(arrow2);
            var cash = FlowCard("03", "Receber", "Acompanhar pagamentos e movimentos do caixa associados às vendas.", "Abrir caixa", (_, _) => Cash_Click(this, new RoutedEventArgs())); Grid.SetColumn(cash, 4); flow.Children.Add(cash);
            root.Children.Add(flow);

            var lower = new Grid { Margin = new Thickness(0, 0, 0, 18) };
            lower.ColumnDefinitions.Add(new ColumnDefinition());
            lower.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(18) });
            lower.ColumnDefinitions.Add(new ColumnDefinition());
            var ops = new Border { Background = Brushes.White, BorderBrush = (Brush)FindResource("BorderBrush"), BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(12), Padding = new Thickness(18) };
            var opStack = new StackPanel();
            opStack.Children.Add(new TextBlock { Text = "Operações", FontSize = 16, FontWeight = FontWeights.SemiBold, Foreground = (Brush)FindResource("TextBrush") });
            opStack.Children.Add(new TextBlock { Text = "Acesso rápido aos processos ligados à facturação.", Style = (Style)FindResource("Caption"), Margin = new Thickness(0, 3, 0, 12) });
            var opGrid = new UniformGrid { Columns = 2 };
            opGrid.Children.Add(ActionTile("Clientes", "Fichas, histórico e saldos", (_, _) => Customers_Click(this, new RoutedEventArgs())));
            opGrid.Children.Add(ActionTile("Produtos", "Preços, IVA e disponibilidade", (_, _) => Products_Click(this, new RoutedEventArgs())));
            opGrid.Children.Add(ActionTile("Stock", "Disponibilidade e movimentos", (_, _) => Stock_Click(this, new RoutedEventArgs())));
            opGrid.Children.Add(ActionTile("Compras", "Entradas e fornecedores", (_, _) => Purchases_Click(this, new RoutedEventArgs())));
            opGrid.Children.Add(ActionTile("Relatórios", "Vendas e indicadores", (_, _) => Reports_Click(this, new RoutedEventArgs())));
            opGrid.Children.Add(ActionTile("Configuração", "Séries e métodos de pagamento", (_, _) => Settings_Click(this, new RoutedEventArgs())));
            opStack.Children.Add(opGrid); ops.Child = opStack; lower.Children.Add(ops);

            var recent = new Border { Background = Brushes.White, BorderBrush = (Brush)FindResource("BorderBrush"), BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(12), Padding = new Thickness(18) }; Grid.SetColumn(recent, 2); lower.Children.Add(recent);
            var recentStack = new StackPanel();
            recentStack.Children.Add(new TextBlock { Text = "Últimos documentos", FontSize = 16, FontWeight = FontWeights.SemiBold, Foreground = (Brush)FindResource("TextBrush") });
            recentStack.Children.Add(new TextBlock { Text = "Actividade recente da facturação.", Style = (Style)FindResource("Caption"), Margin = new Thickness(0, 3, 0, 8) });
            recentStack.Children.Add(Table("SELECT number,status,total,payment_method,created_at FROM invoices WHERE company_id=@c ORDER BY id DESC LIMIT 8", ("@c", companyId)));
            recent.Child = recentStack;
            root.Children.Add(lower);

            if (pending is not null && Convert.ToInt32(pending[0]) > 0)
            {
                root.Children.Add(new Border { Background = (Brush)FindResource("SurfaceBrush"), CornerRadius = new CornerRadius(10), Padding = new Thickness(14), Child = new TextBlock { Text = $"Atenção: existem {pending[0]} documento(s) sem método de pagamento associado.", Foreground = (Brush)FindResource("TextBrush"), FontWeight = FontWeights.SemiBold } });
            }

            Show("Facturação", root);
        }
        catch (Exception ex) { Error(ex); }
    }

    Border FlowCard(string number, string title, string description, string action, RoutedEventHandler click)
    {
        var b = new Button { Content = action, Style = (Style)FindResource("SecondaryButton"), HorizontalAlignment = HorizontalAlignment.Left, Margin = new Thickness(0, 10, 0, 0) };
        b.Click += click;
        var p = new StackPanel();
        p.Children.Add(new TextBlock { Text = number, Foreground = (Brush)FindResource("AccentBrush"), FontSize = 11, FontWeight = FontWeights.Bold });
        p.Children.Add(new TextBlock { Text = title, FontSize = 17, FontWeight = FontWeights.SemiBold, Foreground = (Brush)FindResource("TextBrush"), Margin = new Thickness(0, 3, 0, 2) });
        p.Children.Add(new TextBlock { Text = description, TextWrapping = TextWrapping.Wrap, Foreground = (Brush)FindResource("MutedBrush"), FontSize = 12, MaxWidth = 300 });
        p.Children.Add(b);
        return new Border { Background = Brushes.White, BorderBrush = (Brush)FindResource("BorderBrush"), BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(12), Padding = new Thickness(18), Child = p };
    }

    Button ActionTile(string title, string subtitle, RoutedEventHandler click)
    {
        var b = new Button { Content = new StackPanel { Children = { new TextBlock { Text = title, FontWeight = FontWeights.SemiBold, Foreground = (Brush)FindResource("TextBrush") }, new TextBlock { Text = subtitle, FontSize = 11, Foreground = (Brush)FindResource("MutedBrush"), Margin = new Thickness(0, 3, 0, 0) } } }, Style = (Style)FindResource("GhostButton"), HorizontalContentAlignment = HorizontalAlignment.Left, Padding = new Thickness(10), Margin = new Thickness(0, 0, 8, 8) };
        b.Click += click; return b;
    }
}
