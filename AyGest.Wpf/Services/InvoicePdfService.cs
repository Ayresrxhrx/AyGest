using QuestPDF.Fluent;
using QuestPDF.Helpers;
using QuestPDF.Infrastructure;
namespace AyGest.Wpf.Services;
public sealed class InvoicePdfService
{
 public InvoicePdfService(){QuestPDF.Settings.License=LicenseType.Community;}
 public string Generate(string folder,string company,string nuit,string number,string customer,string payment,IEnumerable<(string description,decimal quantity,decimal unit,decimal vat)> lines)
 {
  Directory.CreateDirectory(folder);
  var path=Path.Combine(folder,$"{number.Replace("/","-")}.pdf");
  var list=lines.ToList();
  var subtotal=list.Sum(x=>x.quantity*x.unit);
  var vat=list.Sum(x=>x.quantity*x.unit*x.vat/100);
  var total=subtotal+vat;
  Document.Create(doc=>doc.Page(page=>{
   page.Size(PageSizes.A4); page.Margin(40); page.DefaultTextStyle(x=>x.FontSize(9));
   page.Header().Column(c=>{c.Item().Text(company).Bold().FontSize(22).FontColor(Colors.Blue.Darken3);c.Item().Text($"NUIT: {nuit}");c.Item().PaddingTop(6).Text($"FACTURA · {number}").Bold().FontSize(14);c.Item().Text(DateTime.Now.ToString("dd/MM/yyyy HH:mm"));});
   page.Content().PaddingTop(18).Column(c=>{c.Item().Background(Colors.Grey.Lighten4).Padding(10).Text($"Cliente: {customer}\nPagamento: {payment}").FontSize(10);c.Item().PaddingVertical(14).Table(t=>{t.ColumnsDefinition(x=>{x.RelativeColumn(5);x.RelativeColumn(1);x.RelativeColumn(2);x.RelativeColumn(2);});t.Header(h=>{h.Cell().Background(Colors.Blue.Darken3).Padding(6).Text("Descrição").Bold().FontColor(Colors.White);h.Cell().Background(Colors.Blue.Darken3).Padding(6).Text("Qtd").Bold().FontColor(Colors.White);h.Cell().Background(Colors.Blue.Darken3).Padding(6).Text("Preço").Bold().FontColor(Colors.White);h.Cell().Background(Colors.Blue.Darken3).Padding(6).Text("Total").Bold().FontColor(Colors.White);});foreach(var l in list){t.Cell().BorderBottom(1).BorderColor(Colors.Grey.Lighten2).Padding(7).Text(l.description);t.Cell().BorderBottom(1).BorderColor(Colors.Grey.Lighten2).Padding(7).Text(l.quantity.ToString("0.##"));t.Cell().BorderBottom(1).BorderColor(Colors.Grey.Lighten2).Padding(7).Text($"{l.unit:N2} MT");t.Cell().BorderBottom(1).BorderColor(Colors.Grey.Lighten2).Padding(7).Text($"{l.quantity*l.unit:N2} MT");}});c.Item().AlignRight().Column(x=>{x.Item().Text($"Subtotal: {subtotal:N2} MT");x.Item().Text($"IVA: {vat:N2} MT");x.Item().PaddingTop(6).Text($"TOTAL: {total:N2} MT").Bold().FontSize(15).FontColor(Colors.Blue.Darken3);});});
   page.Footer().AlignCenter().Text("AyGest · Documento emitido automaticamente").FontSize(8);
  })).GeneratePdf(path);
  return path;
 }
}