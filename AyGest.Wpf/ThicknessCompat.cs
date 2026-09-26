global using Thickness = AyGest.Wpf.ThicknessCompat;

namespace AyGest.Wpf;

public readonly struct ThicknessCompat
{
    public double Left { get; }
    public double Top { get; }
    public double Right { get; }
    public double Bottom { get; }

    public ThicknessCompat(double uniform) => Left = Top = Right = Bottom = uniform;
    public ThicknessCompat(double horizontal, double vertical) => (Left, Top, Right, Bottom) = (horizontal, vertical, horizontal, vertical);
    public ThicknessCompat(double left, double top, double right, double bottom) => (Left, Top, Right, Bottom) = (left, top, right, bottom);
    public static implicit operator System.Windows.Thickness(ThicknessCompat value) => new(value.Left, value.Top, value.Right, value.Bottom);
}
