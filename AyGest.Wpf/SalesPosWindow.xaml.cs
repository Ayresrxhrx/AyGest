using Microsoft.Data.Sqlite;
using System.Collections.ObjectModel;
using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.IO;

namespace AyGest.Wpf;

public partial class SalesPosWindow : Window
{
    private readonly string _db = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "AyGest", "aygest.db");
    private readonly ObservableCollection<CartRow> _cart = new();
    private readonly List<Product> _products = new();
    private decimal _discount;
    private string _payment = "Dinheiro";
    private bool _loading;

    public SalesPosWindow()
    {
        InitializeComponent();
        Directory.CreateDirectory(Path.GetDirectoryName(_db)!);
        EnsureSchema();
        CartGrid.ItemsSource = _cart;
        Loaded += (_, _) => LoadData();
    }

    private SqliteConnection C() => new($"Data Source={_db};Cache=Shared");

    private void EnsureSchema()
    {
        using var c = C();
        c.Open();
        using var q = c.CreateCommand();
        q.CommandText = @"
CREATE TABLE IF NOT EXISTS sales(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 number TEXT NOT NULL UNIQUE,
 customer_id INTEGER,
 customer_name TEXT,
 subtotal REAL NOT NULL DEFAULT 0,
 discount REAL NOT NULL DEFAULT 0,
 vat REAL NOT NULL DEFAULT 0,
 total REAL NOT NULL DEFAULT 0,
 payment_method TEXT NOT NULL DEFAULT 'Dinheiro',
 status TEXT NOT NULL DEFAULT 'Concluída',
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sale_items(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 sale_id INTEGER NOT NULL,
 product_id INTEGER NOT NULL,
 sku TEXT,
 product_name TEXT NOT NULL,
 quantity REAL NOT NULL,
 unit_price REAL NOT NULL,
 discount REAL NOT NULL DEFAULT 0,
 vat REAL NOT NULL DEFAULT 0,
 total REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS suspended_sales(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 number TEXT NOT NULL UNIQUE,
 customer_name TEXT,
 payload TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cash_sessions(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 opened_at TEXT NOT NULL,
 closed_at TEXT,
 opening_balance REAL NOT NULL DEFAULT 0,
 closing_balance REAL,
 expected_balance REAL,
 status TEXT NOT NULL DEFAULT 'Aberto',
 notes TEXT
);
CREATE TABLE IF NOT EXISTS cash_movements(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 session_id INTEGER NOT NULL,
 type TEXT NOT NULL,
 description TEXT,
 reference TEXT,
 method TEXT,
 amount REAL NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pos_stock_movements(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 product_id INTEGER NOT NULL,
 type TEXT NOT NULL,
 quantity REAL NOT NULL,
 reference TEXT,
 notes TEXT,
 created_at TEXT NOT NULL
);";
        q.ExecuteNonQuery();

        EnsureColumn(c, "sales", "customer_id", "INTEGER");
        EnsureColumn(c, "sales", "customer_name", "TEXT");
        EnsureColumn(c, "sales", "subtotal", "REAL NOT NULL DEFAULT 0");
        EnsureColumn(c, "sales", "discount", "REAL NOT NULL DEFAULT 0");
        EnsureColumn(c, "sales", "vat", "REAL NOT NULL DEFAULT 0");
        EnsureColumn(c, "sales", "total", "REAL NOT NULL DEFAULT 0");
        EnsureColumn(c, "sales", "payment_method", "TEXT NOT NULL DEFAULT 'Dinheiro'");
        EnsureColumn(c, "sales", "status", "TEXT NOT NULL DEFAULT 'Concluída'");
        EnsureColumn(c, "sales", "created_at", "TEXT NOT NULL DEFAULT ''");

        EnsureColumn(c, "sale_items", "discount", "REAL NOT NULL DEFAULT 0");
        EnsureColumn(c, "sale_items", "vat", "REAL NOT NULL DEFAULT 0");
    }

    private static void EnsureColumn(SqliteConnection c, string table, string column, string definition)
    {
        using var check = c.CreateCommand();
        check.CommandText = $"PRAGMA table_info([{table}])";
        using var r = check.ExecuteReader();
        while (r.Read())
            if (string.Equals(r.GetString(1), column, StringComparison.OrdinalIgnoreCase))
                return;

        using var alter = c.CreateCommand();
        alter.CommandText = $"ALTER TABLE [{table}] ADD COLUMN [{column}] {definition}";
        alter.ExecuteNonQuery();
    }

    private void LoadData()
    {
        try
        {
            _loading = true;
            LoadProducts();
            LoadCustomers();
            LoadSuspendedCount();
            RefreshTotals();
            CheckCash();
            UpdateSaleNumber();
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Não foi possível carregar o POS.\n\n{ex.Message}", "AyGest POS", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally
        {
            _loading = false;
        }
    }

    private void LoadProducts()
    {
        _products.Clear();
        using var c = C();
        c.Open();
        using var q = c.CreateCommand();
        q.CommandText = "SELECT id, COALESCE(sku,''), COALESCE(name,''), COALESCE(category,''), COALESCE(sale_price,0), COALESCE(stock,0), COALESCE(vat,0) FROM products WHERE COALESCE(status,'Activo')='Activo' ORDER BY name COLLATE NOCASE";
        using var r = q.ExecuteReader();
        while (r.Read())
        {
            _products.Add(new Product(
                r.GetInt64(0),
                r.GetString(1),
                r.GetString(2),
                r.GetString(3),
                ToDecimal(r.GetValue(4)),
                ToDecimal(r.GetValue(5)),
                ToDecimal(r.GetValue(6))));
        }

        CategoryBox.Items.Clear();
        CategoryBox.Items.Add(new ComboBoxItem { Content = "Todas categorias" });
        foreach (var category in _products.Select(x => x.Category).Where(x => !string.IsNullOrWhiteSpace(x)).Distinct().OrderBy(x => x))
            CategoryBox.Items.Add(new ComboBoxItem { Content = category });
        CategoryBox.SelectedIndex = 0;
        RenderProducts();
    }

    private void LoadCustomers()
    {
        CustomerBox.Items.Clear();
        CustomerBox.Items.Add("Consumidor final");

        using var c = C();
        c.Open();
        if (!TableExists(c, "clientes"))
        {
            CustomerBox.SelectedIndex = 0;
            return;
        }

        using var q = c.CreateCommand();
        q.CommandText = "SELECT name FROM clientes WHERE COALESCE(name,'')<>'' ORDER BY name COLLATE NOCASE";
        using var r = q.ExecuteReader();
        while (r.Read()) CustomerBox.Items.Add(r.GetString(0));
        CustomerBox.SelectedIndex = 0;
    }

    private void RenderProducts()
    {
        if (ProductsPanel == null) return;
        ProductsPanel.Children.Clear();
        var text = (SearchBox.Text ?? "").Trim().ToLowerInvariant();
        var category = (CategoryBox.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Todas categorias";

        foreach (var p in _products.Where(p =>
                     (text.Length == 0 || $"{p.Sku} {p.Name}".ToLowerInvariant().Contains(text)) &&
                     (category == "Todas categorias" || p.Category.Equals(category, StringComparison.OrdinalIgnoreCase))))
        {
            var stockText = p.Stock <= 0 ? "SEM STOCK" : $"Stock: {p.Stock:N2}";
            var b = new Button
            {
                Width = 190,
                Height = 115,
                Margin = new Thickness(6),
                Tag = p,
                ToolTip = $"Adicionar {p.Name}",
                Content = new StackPanel
                {
                    Children =
                    {
                        new TextBlock { Text = p.Name, FontWeight = FontWeights.SemiBold, TextWrapping = TextWrapping.Wrap, FontSize = 15 },
                        new TextBlock { Text = p.Sku, Foreground = Brushes.Gray },
                        new TextBlock { Text = $"{p.SalePrice:N2} MT", FontSize = 18, FontWeight = FontWeights.Bold },
                        new TextBlock { Text = stockText, FontSize = 11, Foreground = p.Stock <= 0 ? Brushes.IndianRed : Brushes.Gray }
                    }
                }
            };
            b.Click += Product_Click;
            b.IsEnabled = p.Stock > 0;
            ProductsPanel.Children.Add(b);
        }
    }

    private void Product_Click(object sender, RoutedEventArgs e)
    {
        if ((sender as Button)?.Tag is Product p) Add(p, 1);
    }

    private void Add(Product p, decimal quantity)
    {
        if (quantity <= 0 || p.Stock <= 0) return;
        var current = _cart.FirstOrDefault(x => x.ProductId == p.Id);
        var newQuantity = (current?.Quantity ?? 0) + quantity;
        if (newQuantity > p.Stock)
        {
            MessageBox.Show($"Stock insuficiente para {p.Name}.\nDisponível: {p.Stock:N2}", "Stock", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (current != null)
            _cart[_cart.IndexOf(current)] = current with { Quantity = newQuantity, Total = newQuantity * p.SalePrice };
        else
            _cart.Add(new CartRow(p.Id, p.Sku, p.Name, quantity, p.SalePrice, quantity * p.SalePrice, p.Vat));

        RefreshTotals();
    }

    private void SearchChanged(object sender, EventArgs e)
    {
        if (_loading) return;
        RenderProducts();
    }

    private void Clear_Click(object sender, RoutedEventArgs e)
    {
        _cart.Clear();
        _discount = 0;
        _payment = "Dinheiro";
        RefreshTotals();
        UpdateSaleNumber();
    }

    private void RefreshTotals()
    {
        var subtotal = _cart.Sum(x => x.Total);
        var vat = _cart.Sum(x => Math.Max(0, x.Total - x.Discount) * x.Vat / 100m);
        var total = Math.Max(0, subtotal - _discount + vat);

        SubtotalText.Text = $"Subtotal: {subtotal:N2} MT";
        DiscountText.Text = $"Desconto: {_discount:N2} MT";
        VatText.Text = $"IVA: {vat:N2} MT";
        TotalText.Text = $"Total: {total:N2} MT";
        ItemsText.Content = _cart.Sum(x => x.Quantity).ToString("N2");

        using var c = C();
        c.Open();
        using var q = c.CreateCommand();
        q.CommandText = "SELECT COUNT(*), COALESCE(SUM(total),0) FROM sales WHERE date(created_at)=date('now','localtime') AND status='Concluída'";
        using var r = q.ExecuteReader();
        if (r.Read())
        {
            SalesTodayText.Content = r.GetInt32(0);
            SalesTotalText.Content = $"{ToDecimal(r.GetValue(1)):N2} MT";
        }
    }

    private void CheckCash()
    {
        using var c = C();
        c.Open();
        using var q = c.CreateCommand();
        q.CommandText = "SELECT COUNT(*) FROM cash_sessions WHERE status='Aberto'";
        var open = Convert.ToInt32(q.ExecuteScalar()) > 0;
        CashStatusText.Text = open ? "● Caixa aberto" : "○ Caixa fechado";
        CashStatusText.Foreground = open ? Brushes.SeaGreen : Brushes.IndianRed;
    }

    private void Cash_Click(object sender, RoutedEventArgs e) { _payment = "Dinheiro"; Checkout_Click(sender, e); }
    private void Mpesa_Click(object sender, RoutedEventArgs e) { _payment = "M-Pesa"; Checkout_Click(sender, e); }
    private void Card_Click(object sender, RoutedEventArgs e) { _payment = "Cartão"; Checkout_Click(sender, e); }

    private void Checkout_Click(object sender, RoutedEventArgs e)
    {
        if (!_cart.Any())
        {
            MessageBox.Show("Adicione pelo menos um produto ao carrinho.", "Venda", MessageBoxButton.OK, MessageBoxImage.Information);
            return;
        }

        using var c = C();
        c.Open();
        using var cash = c.CreateCommand();
        cash.CommandText = "SELECT id FROM cash_sessions WHERE status='Aberto' ORDER BY id DESC LIMIT 1";
        var sessionValue = cash.ExecuteScalar();
        if (sessionValue == null || sessionValue == DBNull.Value)
        {
            MessageBox.Show("Abra o caixa antes de finalizar a venda.", "Caixa fechado", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var subtotal = _cart.Sum(x => x.Total);
        var vat = _cart.Sum(x => Math.Max(0, x.Total - x.Discount) * x.Vat / 100m);
        var total = Math.Max(0, subtotal - _discount + vat);

        decimal received = total;
        if (_payment == "Dinheiro")
        {
            var input = Prompt("Pagamento em dinheiro", $"Total: {total:N2} MT\nValor recebido:", total.ToString("N2"));
            if (input == null) return;
            if (!TryMoney(input, out received) || received < total)
            {
                MessageBox.Show("O valor recebido é inferior ao total da venda.", "Pagamento", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }
        }

        var number = GenerateSaleNumber(c);
        using var tx = c.BeginTransaction();
        try
        {
            using var q = c.CreateCommand();
            q.Transaction = tx;
            q.CommandText = @"INSERT INTO sales(number,customer_name,subtotal,discount,vat,total,payment_method,status,created_at)
VALUES($n,$customer,$sub,$disc,$vat,$total,$method,'Concluída',$d);
SELECT last_insert_rowid();";
            q.Parameters.AddWithValue("$n", number);
            q.Parameters.AddWithValue("$customer", CustomerBox.SelectedItem?.ToString() ?? "Consumidor final");
            q.Parameters.AddWithValue("$sub", subtotal);
            q.Parameters.AddWithValue("$disc", _discount);
            q.Parameters.AddWithValue("$vat", vat);
            q.Parameters.AddWithValue("$total", total);
            q.Parameters.AddWithValue("$method", _payment);
            q.Parameters.AddWithValue("$d", DateTime.UtcNow.ToString("O"));
            var saleId = Convert.ToInt64(q.ExecuteScalar());

            foreach (var item in _cart)
            {
                using var check = c.CreateCommand();
                check.Transaction = tx;
                check.CommandText = "SELECT stock FROM products WHERE id=$id";
                check.Parameters.AddWithValue("$id", item.ProductId);
                var stockValue = check.ExecuteScalar();
                var currentStock = stockValue == null || stockValue == DBNull.Value ? 0m : ToDecimal(stockValue);
                if (currentStock < item.Quantity)
                    throw new InvalidOperationException($"Stock insuficiente para {item.Product}. Disponível: {currentStock:N2}.");

                using var insert = c.CreateCommand();
                insert.Transaction = tx;
                insert.CommandText = @"INSERT INTO sale_items(sale_id,product_id,sku,product_name,quantity,unit_price,discount,vat,total)
VALUES($sid,$pid,$sku,$name,$qty,$price,$discount,$vat,$total)";
                insert.Parameters.AddWithValue("$sid", saleId);
                insert.Parameters.AddWithValue("$pid", item.ProductId);
                insert.Parameters.AddWithValue("$sku", item.Sku);
                insert.Parameters.AddWithValue("$name", item.Product);
                insert.Parameters.AddWithValue("$qty", item.Quantity);
                insert.Parameters.AddWithValue("$price", item.UnitPrice);
                insert.Parameters.AddWithValue("$discount", item.Discount);
                insert.Parameters.AddWithValue("$vat", item.Vat);
                insert.Parameters.AddWithValue("$total", item.Total);
                insert.ExecuteNonQuery();

                using var update = c.CreateCommand();
                update.Transaction = tx;
                update.CommandText = "UPDATE products SET stock=stock-$qty, updated_at=$d WHERE id=$id AND stock >= $qty";
                update.Parameters.AddWithValue("$qty", item.Quantity);
                update.Parameters.AddWithValue("$id", item.ProductId);
                update.Parameters.AddWithValue("$d", DateTime.UtcNow.ToString("O"));
                if (update.ExecuteNonQuery() != 1)
                    throw new InvalidOperationException($"O stock de {item.Product} foi alterado durante a venda.");

                RecordPosStockMovement(c, tx, item, number);
            }

            using var movement = c.CreateCommand();
            movement.Transaction = tx;
            movement.CommandText = @"INSERT INTO cash_movements(session_id,type,description,reference,method,amount,created_at)
VALUES($sid,'Recebimento','Venda POS',$ref,$method,$amount,$d)";
            movement.Parameters.AddWithValue("$sid", Convert.ToInt64(sessionValue));
            movement.Parameters.AddWithValue("$ref", number);
            movement.Parameters.AddWithValue("$method", _payment);
            movement.Parameters.AddWithValue("$amount", total);
            movement.Parameters.AddWithValue("$d", DateTime.UtcNow.ToString("O"));
            movement.ExecuteNonQuery();

            tx.Commit();

            var change = Math.Max(0, received - total);
            MessageBox.Show(
                $"Venda {number} concluída.\n\nTotal: {total:N2} MT\nPagamento: {_payment}" + (_payment == "Dinheiro" ? $"\nRecebido: {received:N2} MT\nTroco: {change:N2} MT" : ""),
                "Venda concluída", MessageBoxButton.OK, MessageBoxImage.Information);

            _cart.Clear();
            _discount = 0;
            LoadData();
        }
        catch (Exception ex)
        {
            try { tx.Rollback(); } catch { }
            MessageBox.Show($"A venda não foi concluída e nenhuma alteração foi confirmada.\n\n{ex.Message}", "Erro ao finalizar venda", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private static void RecordPosStockMovement(SqliteConnection c, SqliteTransaction tx, CartRow item, string reference)
    {
        using var m = c.CreateCommand();
        m.Transaction = tx;
        m.CommandText = @"INSERT INTO pos_stock_movements(product_id,type,quantity,reference,notes,created_at)
VALUES($id,'Venda',$qty,$ref,'Baixa automática do POS',$d)";
        m.Parameters.AddWithValue("$id", item.ProductId);
        m.Parameters.AddWithValue("$qty", -item.Quantity);
        m.Parameters.AddWithValue("$ref", reference);
        m.Parameters.AddWithValue("$d", DateTime.UtcNow.ToString("O"));
        m.ExecuteNonQuery();
    }

    private string GenerateSaleNumber(SqliteConnection c)
    {
        using var q = c.CreateCommand();
        q.CommandText = "SELECT COALESCE(MAX(id),0)+1 FROM sales";
        var next = Convert.ToInt64(q.ExecuteScalar());
        return $"FT-{DateTime.Now:yyyyMMdd}-{next:000000}";
    }

    private void UpdateSaleNumber()
    {
        try
        {
            using var c = C();
            c.Open();
            SaleNumberText.Text = $"Nova venda · {GenerateSaleNumber(c)}";
        }
        catch { SaleNumberText.Text = "Nova venda"; }
    }

    private void Barcode_Click(object sender, RoutedEventArgs e)
    {
        var code = Prompt("Pesquisar produto", "Introduza o SKU ou código de barras:");
        if (string.IsNullOrWhiteSpace(code)) return;
        var product = _products.FirstOrDefault(x => x.Sku.Equals(code.Trim(), StringComparison.OrdinalIgnoreCase));
        if (product == null)
        {
            MessageBox.Show("Produto não encontrado.", "Pesquisa", MessageBoxButton.OK, MessageBoxImage.Information);
            return;
        }
        Add(product, 1);
    }

    private void Suspend_Click(object sender, RoutedEventArgs e)
    {
        if (!_cart.Any())
        {
            MessageBox.Show("Não há itens para suspender.");
            return;
        }

        var name = CustomerBox.SelectedItem?.ToString() ?? "Consumidor final";
        var number = $"SUS-{DateTime.Now:yyyyMMddHHmmssfff}";
        var payload = JsonSerializer.Serialize(_cart.ToList());
        using var c = C();
        c.Open();
        using var q = c.CreateCommand();
        q.CommandText = "INSERT INTO suspended_sales(number,customer_name,payload,created_at) VALUES($n,$c,$p,$d)";
        q.Parameters.AddWithValue("$n", number);
        q.Parameters.AddWithValue("$c", name);
        q.Parameters.AddWithValue("$p", payload);
        q.Parameters.AddWithValue("$d", DateTime.UtcNow.ToString("O"));
        q.ExecuteNonQuery();

        _cart.Clear();
        RefreshTotals();
        LoadSuspendedCount();
        MessageBox.Show($"Venda {number} suspensa com sucesso.", "Venda suspensa", MessageBoxButton.OK, MessageBoxImage.Information);
    }

    private void Suspended_Click(object sender, RoutedEventArgs e)
    {
        using var c = C();
        c.Open();
        using var q = c.CreateCommand();
        q.CommandText = "SELECT id,number,customer_name,created_at FROM suspended_sales ORDER BY id DESC";
        using var r = q.ExecuteReader();
        var sb = new StringBuilder("Vendas suspensas\n\n");
        var found = false;
        while (r.Read())
        {
            found = true;
            sb.AppendLine($"{r.GetInt64(0)} · {r.GetString(1)} · {r.GetString(2)} · {r.GetString(3)}");
        }
        MessageBox.Show(found ? sb.ToString() : "Não existem vendas suspensas.", "Suspensas", MessageBoxButton.OK, MessageBoxImage.Information);
    }

    private void LoadSuspendedCount()
    {
        try
        {
            using var c = C();
            c.Open();
            using var q = c.CreateCommand();
            q.CommandText = "SELECT COUNT(*) FROM suspended_sales";
            var count = Convert.ToInt32(q.ExecuteScalar());
            if (SuspendedButtonExists()) { }
            Title = count > 0 ? $"Vendas / POS — {count} suspensa(s)" : "Vendas / POS — AyGest";
        }
        catch { }
    }

    private bool SuspendedButtonExists() => true;

    private void NewSale_Click(object sender, RoutedEventArgs e) => Clear_Click(sender, e);

    private void History_Click(object sender, RoutedEventArgs e)
    {
        using var c = C();
        c.Open();
        using var q = c.CreateCommand();
        q.CommandText = "SELECT number,COALESCE(customer_name,'Consumidor final'),total,payment_method,created_at,status FROM sales ORDER BY id DESC LIMIT 30";
        using var r = q.ExecuteReader();
        var sb = new StringBuilder("Últimas 30 vendas\n\n");
        while (r.Read())
            sb.AppendLine($"{r.GetString(0)} | {r.GetString(1)} | {ToDecimal(r.GetValue(2)):N2} MT | {r.GetString(3)} | {r.GetString(4)} | {r.GetString(5)}");
        MessageBox.Show(sb.ToString(), "Histórico de vendas", MessageBoxButton.OK, MessageBoxImage.Information);
    }

    private static bool TableExists(SqliteConnection c, string table)
    {
        using var q = c.CreateCommand();
        q.CommandText = "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=$name";
        q.Parameters.AddWithValue("$name", table);
        return Convert.ToInt32(q.ExecuteScalar()) > 0;
    }

    private static decimal ToDecimal(object value)
    {
        if (value == null || value == DBNull.Value) return 0m;
        return Convert.ToDecimal(value, CultureInfo.InvariantCulture);
    }

    private static bool TryMoney(string text, out decimal value)
    {
        text = text.Trim().Replace(" ", "");
        return decimal.TryParse(text, NumberStyles.Number, CultureInfo.CurrentCulture, out value) ||
               decimal.TryParse(text.Replace(',', '.'), NumberStyles.Number, CultureInfo.InvariantCulture, out value);
    }

    private static string? Prompt(string title, string label, string initial = "")
    {
        var window = new Window
        {
            Title = title,
            Width = 460,
            Height = 210,
            WindowStartupLocation = WindowStartupLocation.CenterOwner,
            ResizeMode = ResizeMode.NoResize,
            Background = Brushes.White
        };
        var panel = new StackPanel { Margin = new Thickness(22) };
        panel.Children.Add(new TextBlock { Text = label, TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 0, 0, 10), FontSize = 15 });
        var box = new TextBox { Text = initial, Height = 34, VerticalContentAlignment = VerticalAlignment.Center };
        panel.Children.Add(box);
        var buttons = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 16, 0, 0) };
        var cancel = new Button { Content = "Cancelar", Width = 95, Height = 34, Margin = new Thickness(0, 0, 8, 0) };
        var ok = new Button { Content = "OK", Width = 95, Height = 34 };
        cancel.Click += (_, _) => { window.DialogResult = false; window.Close(); };
        ok.Click += (_, _) => { window.DialogResult = true; window.Close(); };
        buttons.Children.Add(cancel); buttons.Children.Add(ok); panel.Children.Add(buttons);
        window.Content = panel;
        window.Loaded += (_, _) => { box.Focus(); box.SelectAll(); };
        return window.ShowDialog() == true ? box.Text : null;
    }

    public record Product(long Id, string Sku, string Name, string Category, decimal SalePrice, decimal Stock, decimal Vat);
    public record CartRow(long ProductId, string Sku, string Product, decimal Quantity, decimal UnitPrice, decimal Total, decimal Vat, decimal Discount = 0);
}
