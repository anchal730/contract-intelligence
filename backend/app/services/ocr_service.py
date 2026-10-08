from io import BytesIO

import pytesseract
from PIL import Image

import pymupdf


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_text_with_ocr(page) -> str:
    """
    Convert a PDF page into an image
    and extract text using Tesseract OCR.
    """

    matrix = pymupdf.Matrix(2, 2)

    pixmap = page.get_pixmap(
        matrix=matrix,
        alpha=False
    )

    image_bytes = pixmap.tobytes("png")

    image = Image.open(BytesIO(image_bytes))

    text = pytesseract.image_to_string(
        image,
        lang="eng"
    )

    return text.strip()