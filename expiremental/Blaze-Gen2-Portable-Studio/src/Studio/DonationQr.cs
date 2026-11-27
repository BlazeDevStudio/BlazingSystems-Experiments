using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
namespace BlazeGen2Studio;
/// <summary>QR re-encoded from the user-provided PayPal QR; no network images or telemetry.</summary>
public static class DonationQr {
    public const string PayPalUrl="https://www.paypal.com/qrcodes/p2pqrc/AEBWES36GX9K2";
    const int Side=41;
    const string Bits="AAAAAAAAAAAAAAAAAAAAAAAAAAAA/pxmP4BBW1pQQC6rwyugF0hXxdALr5hq6AQQLpkEA/qqqv4AAJsHAACfuOBLgFhnuIeADPlA6+ARCYZKUABx1cOYB6cT45ABOh1YiAEZ1TCtAO+dC/gAHBesdcAUtd5N4BQucGXwASrKyVAExfDBUAKu4ZWuATl6pNcA+4aJ+YAAT+bFAD+8VeqAEFe8ceALrB2fkAXXd0K8Aujs2nYBBFB3/wD+9cH4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==";
    public static Image CreateImage() {
        var bits=Convert.FromBase64String(Bits);
        var pixels=new byte[Side*Side*4];
        for(int i=0;i<Side*Side;i++) {
            bool on=(bits[i/8] & (1 << (7-i%8)))!=0;
            byte color=on?(byte)10:(byte)255;
            pixels[i*4]=color;pixels[i*4+1]=color;pixels[i*4+2]=color;pixels[i*4+3]=255;
        }
        var bitmap=BitmapSource.Create(Side,Side,96,96,PixelFormats.Bgra32,null,pixels,Side*4);
        bitmap.Freeze();
        return new Image{Source=bitmap,Width=288,Height=288,Stretch=Stretch.Fill,
            SnapsToDevicePixels=true,UseLayoutRounding=true,HorizontalAlignment=HorizontalAlignment.Left,
            Margin=new Thickness(0,12,0,12)};
    }
}

