"""
Service for generating PDF posters (cartazes) for partners.
"""
import io
import logging

import qrcode
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from src.api.schemas.parceiro import ParceiroResponse

logger = logging.getLogger(__name__)


class CartazService:
    """
    Service to generate PDF posters for partners.
    """

    def __init__(self):
        """Initialize the service."""
        pass

    def _generate_qr_code(self, parceiro_id: str) -> Image.Image:
        """
        Generates a QR code image for the given partner ID.
        """
        # Using the placeholder URL as discussed
        url = f"https://qr-saude-alpha.web.app/solicitacao?card_id={parceiro_id}"
        qr_img = qrcode.make(url, error_correction=qrcode.constants.ERROR_CORRECT_L)
        return qr_img.convert("RGB")

    def generate_cartaz_pdf(self, parceiro: ParceiroResponse) -> bytes:
        """
        Generates a visually appealing PDF poster for a single partner.
        """
        from pathlib import Path
        from PIL import Image, ImageEnhance, ImageFilter
        from reportlab.lib.utils import ImageReader

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # ==========================================================
        # Colors
        # ==========================================================
        primary_color = HexColor("#1a237e")
        light_bg_color = HexColor("#e8eaf6")
        text_color = colors.black
        white_text = colors.white
        light_gray = HexColor("#757575")

        # ==========================================================
        # Page background
        # ==========================================================
        p.setFillColor(light_bg_color)
        p.rect(0, 0, width, height, fill=1, stroke=0)

        # ==========================================================
        # Header
        # ==========================================================
        header_height = 4 * cm

        p.setFillColor(primary_color)
        p.rect(
            0,
            height - header_height,
            width,
            header_height,
            fill=1,
            stroke=0,
        )

        # Logo placeholder
        logo_size = 3 * cm

        p.setFillColor(white_text)
        p.circle(
            logo_size / 2 + 2 * cm,
            height - header_height / 2,
            logo_size / 2 - 5,
            fill=1,
        )

        p.setFont("Helvetica-Bold", 12)
        p.setFillColor(primary_color)
        p.drawCentredString(
            logo_size / 2 + 2 * cm,
            height - header_height / 2 - 4,
            "LOGO",
        )

        # Título
        p.setFillColor(white_text)
        p.setFont("Helvetica-Bold", 32)
        p.drawCentredString(
            width / 2,
            height - header_height / 2 + 0.5 * cm,
            "Plano de Saúde",
        )

        p.setFont("Helvetica", 16)
        p.drawCentredString(
            width / 2,
            height - header_height / 2 - 0.5 * cm,
            "Simulação Rápida e Gratuita",
        )

        # ==========================================================
        # Main card
        # ==========================================================
        margin = 2 * cm

        content_x = margin
        content_y = margin
        content_width = width - (2 * margin)
        content_height = height - header_height - (2 * margin)

        p.setFillColor(colors.white)
        p.roundRect(
            content_x,
            content_y,
            content_width,
            content_height,
            10,
            fill=1,
            stroke=0,
        )

        # ==========================================================
        # Hero image (top banner)
        # ==========================================================
        hero_height = 6.5 * cm

        bg_path = Path("static/public/lp-header.jpg")

        if bg_path.exists():
            try:
                bg = Image.open(bg_path)

                bg = bg.filter(
                    ImageFilter.GaussianBlur(radius=1.2)
                )

                enhancer = ImageEnhance.Brightness(bg)
                bg = enhancer.enhance(0.75)

                bg_reader = ImageReader(bg)

                p.drawImage(
                    bg_reader,
                    content_x,
                    content_y + content_height - hero_height,
                    width=content_width,
                    height=hero_height,
                    mask="auto",
                )

            except Exception:
                logger.exception(
                    "Erro carregando imagem de fundo."
                )

        # ==========================================================
        # White box for partner name
        # ==========================================================
        name_box_w = 12 * cm
        name_box_h = 2 * cm

        name_box_x = (width - name_box_w) / 2
        name_box_y = (
            content_y
            + content_height
            - hero_height
            + 1.8 * cm
        )

        p.setFillColor(colors.white)
        p.roundRect(
            name_box_x,
            name_box_y,
            name_box_w,
            name_box_h,
            10,
            fill=1,
            stroke=0,
        )

        p.setFillColor(text_color)
        p.setFont("Helvetica", 12)
        p.drawCentredString(
            width / 2,
            name_box_y + 1.25 * cm,
            "Parceiro:"
        )

        p.setFont("Helvetica-Bold", 20)
        p.drawCentredString(
            width / 2,
            name_box_y + 0.55 * cm,
            parceiro.nome.upper(),
        )

        # ==========================================================
        # QR card with shadow
        # ==========================================================
        qr_size = 9 * cm
        qr_x = (width - qr_size) / 2

        qr_y = content_y + 6 * cm

        qr_padding = 12

        # Shadow
        p.setFillColor(HexColor("#d0d0d0"))
        p.roundRect(
            qr_x - qr_padding + 4,
            qr_y - qr_padding - 4,
            qr_size + qr_padding * 2,
            qr_size + qr_padding * 2,
            12,
            fill=1,
            stroke=0,
        )

        # White card
        p.setFillColor(colors.white)
        p.roundRect(
            qr_x - qr_padding,
            qr_y - qr_padding,
            qr_size + qr_padding * 2,
            qr_size + qr_padding * 2,
            12,
            fill=1,
            stroke=0,
        )

        qr_img = self._generate_qr_code(
            parceiro.id
        )

        p.drawInlineImage(
            qr_img,
            qr_x,
            qr_y,
            width=qr_size,
            height=qr_size,
        )

        # ==========================================================
        # Footer white area
        # ==========================================================
        footer_height = 3.3 * cm

        p.setFillColor(colors.white)
        p.rect(
            content_x,
            content_y,
            content_width,
            footer_height,
            fill=1,
            stroke=0,
        )

        footer_y = content_y + 2.0 * cm

        p.setFont("Helvetica-Bold", 18)
        p.setFillColor(primary_color)
        p.drawCentredString(
            width / 2,
            footer_y,
            "Escaneie e faça uma cotação gratuita"
        )

        p.setFont("Helvetica", 12)
        p.setFillColor(text_color)
        p.drawCentredString(
            width / 2,
            footer_y - 0.8 * cm,
            "Atendimento rápido e sem compromisso"
        )

        # ==========================================================
        # Card code
        # ==========================================================
        card_footer_y = content_y + 0.7 * cm

        p.setStrokeColor(HexColor("#d9d9d9"))
        p.line(
            content_x + 1.5 * cm,
            card_footer_y + 0.5 * cm,
            content_x + content_width - 1.5 * cm,
            card_footer_y + 0.5 * cm,
        )

        p.setFillColor(light_gray)
        p.setFont("Helvetica", 9)
        p.drawCentredString(
            width / 2,
            card_footer_y,
            f"Código do cartão: {parceiro.codigo_cartao or ''}",
        )

        # ==========================================================
        # Finalize
        # ==========================================================
        p.showPage()
        p.save()

        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info(
            "Generated PDF poster for partner %s",
            parceiro.id,
        )

        return pdf_bytes


def get_cartaz_service() -> CartazService:
    """
    Dependency injector for CartazService.
    """
    return CartazService()
