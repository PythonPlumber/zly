import io

import qrcode
from qrcode.image.svg import SvgPathFillImage


def generate_qr_png(url: str, box_size: int = 10, fill_color: str = "black", back_color: str = "white") -> bytes:
    qr = qrcode.QRCode(box_size=box_size, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_qr_svg(url: str, fill_color: str = "black", back_color: str = "white") -> str:
    qr = qrcode.QRCode(image_factory=SvgPathFillImage)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    return img.to_string().decode()
