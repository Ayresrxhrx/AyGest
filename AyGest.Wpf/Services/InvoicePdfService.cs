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
  Document.Create(doc=>doc.Page(page=>{page.Size(PageSizes.A4);page.Margin(36);page.DefaultTextStyle(x=>x.FontFamily(Fonts.Arial).FontSize(9).FontColor(Colors.Grey.Darken3));
   page.Header().Column(c=>{c.Item().Row(r=>{r.RelativeItem().Column(x=>{x.Item().Text(company).Bold().FontSize(22).FontColor(Colors.Blue.Darken3);x.Item().Text($"NUIT: {nuit}").FontSize(9).FontColor(Colors.Grey.Darken1);});r.ConstantItem(180).AlignRight().Column(x=>{x.Item().Text("FACTURA").Bold().FontSize(19).FontColor(Colors.Blue.Darken3);x.Item().Text(number).Bold().FontSize(11);x.Item().Text(DateTime.Now.ToString("dd/MM/yyyy HH:mm")).FontSize(9);});});c.Item().PaddingTop(14).LineHorizontal(1).LineColor(Colors.Grey.Lighten2);});
   page.Content().PaddingTop(16).Column(c=>{c.Item().Row(r=>{r.RelativeItem().Background(Colors.Grey.Lighten4).Padding(12).Column(x=>{x.Item().Text("CLIENTE").Bold().FontSize(8).FontColor(Colors.Grey.Darken1);x.Item().PaddingTop(3).Text(customer).Bold().FontSize(11);});r.ConstantItem(165).Background(Colors.Grey.Lighten4).Padding(12).Column(x=>{x.Item().Text("PAGAMENTO").Bold().FontSize(8).FontColor(Colors.Grey.Darken1);x.Item().PaddingTop(3).Text(payment).Bold().FontSize(11);});});
    c.Item().PaddingTop(18).Table(t=>{t.ColumnsDefinition(x=>{x.RelativeColumn(5);x.RelativeColumn(1);x.RelativeColumn(1.7f);x.RelativeColumn(1.2f);x.RelativeColumn(2);});t.Header(h=>{foreach(var title in new[]{"Descrição","Qtd.","Preço","IVA","Total"})h.Cell().Background(Colors.Blue.Darken3).Padding(7).Text(title).Bold().FontColor(Colors.White);});foreach(var l in list){var line=l.quantity*l.unit;var cells=new[]{l.description,l.quantity.ToString("0.##"),$"{l.unit:N2} MT",$"{l.vat:N0}%",$"{line:N2} MT"};for(var i=0;i<cells.Length;i++)t.Cell().BorderBottom(1).BorderColor(Colors.Grey.Lighten2).Padding(7).Text(cells[i]);}});
    c.Item().PaddingTop(18).AlignRight().Width(235).Column(x=>{x.Item().Row(r=>{r.RelativeItem().Text("Subtotal");r.ConstantItem(90).AlignRight().Text($"{subtotal:N2} MT");});x.Item().PaddingTop(5).Row(r=>{r.RelativeItem().Text("IVA");r.ConstantItem(90).AlignRight().Text($"{vat:N2} MT");});x.Item().PaddingTop(9).BorderTop(1).BorderColor(Colors.Grey.Lighten2).PaddingTop(9).Row(r=>{r.RelativeItem().Text("TOTAL").Bold().FontSize(13);r.ConstantItem(90).AlignRight().Text($"{total:N2} MT").Bold().FontSize(13).FontColor(Colors.Blue.Darken3);});});
    c.Item().PaddingTop(28).Background(Colors.Grey.Lighten4).Padding(10).Text("Documento emitido pelo AyGest. Guarde este documento para referência contabilística.").FontSize(8).FontColor(Colors.Grey.Darken1);});
   page.Footer().PaddingTop(10).Row(r=>{r.RelativeItem().Text("AyGest · Gestão empresarial").FontSize(8);r.ConstantItem(150).AlignRight().Text(x=>{x.Span("Página ");x.CurrentPageNumber();x.Span(" de ");x.TotalPages();}).FontSize(8);});
  })).GeneratePdf(path);return path;
 }
}