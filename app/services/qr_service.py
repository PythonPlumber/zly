import io

import qrcode
from qrcode.image.svg import SvgPathFillImage


def generate_qr_png(url: str, box_size: int = 10) -> bytes:
    qr = qrcode.QRCode(box_size=box_size, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_qr_svg(url: str) -> str:
    qr = qrcode.QRCode(image_factory=SvgPathFillImage)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    return img.to_string().decode()
