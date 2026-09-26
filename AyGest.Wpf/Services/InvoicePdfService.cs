using QuestPDF.Fluent;
using QuestPDF.Helpers;
using QuestPDF.Infrastructure;
namespace AyGest.Wpf.Services;
public sealed class InvoicePdfService
{
 public InvoicePdfService(){QuestPDF.Settings.License=LicenseType.Community;}
 public string Generate(string folder,string company,string nuit,string number,string customer,string payment,IEnumerable<(string description,decimal quantity,decimal unit,decimal vat)> lines)
 {
  Directory.CreateDirectory(folder);var path=Path.Combine(folder,$"{number.Replace("/","-")}.pdf");var list=lines.ToList();var subtotal=list.Sum(x=>x.quantity*x.unit);var vat=list.Sum(x=>x.quantity*x.unit*x.vat/100);var total=subtotal+vat;
  Document.Create(doc=>doc.Page(page=>{page.Size(PageSizes.A4);page.Margin(35);page.DefaultTextStyle(x=>x.FontSize(9));page.Header().Column(c=>{c.Item().Text(company).Bold().FontSize(18);c.Item().Text($"NUIT: {nuit}");c.Item().Text($"Factura {number}").Bold().FontSize(14);c.Item().Text(DateTime.Now.ToString("dd/MM/yyyy HH:mm"));});page.Content().PaddingTop(20).Column(c=>{c.Item().Text($"Cliente: {customer}");c.Item().Text($"Pagamento: {payment}");c.Item().PaddingVertical(12).Table(t=>{t.ColumnsDefinition(x=>{x.RelativeColumn(5);x.RelativeColumn(1);x.RelativeColumn(2);x.RelativeColumn(2);});t.Header(h=>{h.Cell().Text("Descrição").Bold();h.Cell().Text("Qtd").Bold();h.Cell().Text("Preço").Bold();h.Cell().Text("Total").Bold();});foreach(var l in list){t.Cell().Text(l.description);t.Cell().Text(l.quantity.ToString("0.##"));t.Cell().Text($"{l.unit:N2} MT");t.Cell().Text($"{l.quantity*l.unit:N2} MT");}});c.Item().AlignRight().Column(x=>{x.Item().Text($"Subtotal: {subtotal:N2} MT");x.Item().Text($"IVA: {vat:N2} MT");x.Item().Text($"TOTAL: {total:N2} MT").Bold().FontSize(14);});});page.Footer().AlignCenter().Text("Documento emitido pelo AyGest");})).GeneratePdf(path);return path;
 }
}