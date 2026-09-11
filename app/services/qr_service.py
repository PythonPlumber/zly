import io
import re

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, SquareModuleDrawer
from qrcode.image.svg import SvgPathFillImage

_COLOR_PATTERN = re.compile(r"^#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})$")
_NAMED_COLORS = {"black", "white", "red", "green", "blue", "yellow", "cyan", "magenta", "gray", "grey", "orange", "purple", "transparent"}

_ERROR_LEVELS = {
    "L": qrcode.constants.ERROR_CORRECT_L,
    "M": qrcode.constants.ERROR_CORRECT_M,
    "Q": qrcode.constants.ERROR_CORRECT_Q,
    "H": qrcode.constants.ERROR_CORRECT_H,
}


def _sanitize_color(value: str, default: str) -> str:
    value = (value or "").strip()
    if _COLOR_PATTERN.match(value) or value.lower() in _NAMED_COLORS:
        return value
    return default


def generate_qr_png(
    url: str,
    box_size: int = 10,
    fill_color: str = "black",
    back_color: str = "white",
    error_correction: str = "M",
    style: str = "square",
    border: int = 4,
) -> bytes:
    ec = _ERROR_LEVELS.get(error_correction.upper(), qrcode.constants.ERROR_CORRECT_M)
    qr = qrcode.QRCode(version=None, error_correction=ec, box_size=box_size, border=border)
    qr.add_data(url)
    qr.make(fit=True)
    drawer = RoundedModuleDrawer() if style == "rounded" else SquareModuleDrawer()
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=drawer,
        fill_color=_sanitize_color(fill_color, "black"),
        back_color=_sanitize_color(back_color, "white"),
    )
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_qr_svg(url: str, fill_color: str = "black", back_color: str = "white", error_correction: str = "M") -> str:
    ec = _ERROR_LEVELS.get(error_correction.upper(), qrcode.constants.ERROR_CORRECT_M)
    qr = qrcode.QRCode(image_factory=SvgPathFillImage, error_correction=ec)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=_sanitize_color(fill_color, "black"), back_color=_sanitize_color(back_color, "white"))
    return img.to_string().decode()
