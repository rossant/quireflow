from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from quireflow.models import DocumentResult, PageResult


class TesseractAdapter:
    """Local adapter using pdftoppm and Tesseract; no data leaves the machine."""
    name = "tesseract"

    def __init__(self, language: str = "eng", dpi: int = 300):
        self.language, self.dpi = language, dpi

    def process_pdf(self, path: str) -> DocumentResult:
        if not shutil.which("pdftoppm") or not shutil.which("tesseract"):
            raise RuntimeError("Tesseract adapter requires pdftoppm (Poppler) and tesseract on PATH.")
        with tempfile.TemporaryDirectory(prefix="quireflow-") as temp:
            prefix = str(Path(temp) / "page")
            subprocess.run(["pdftoppm", "-r", str(self.dpi), "-png", path, prefix], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            images = sorted(Path(temp).glob("page-*.png"))
            pages = []
            for index, image in enumerate(images):
                text = subprocess.check_output(["tesseract", str(image), "stdout", "-l", self.language], text=True)
                pages.append(PageResult(index=index, markdown=text, text=text,
                    metadata={"language": self.language, "dpi": self.dpi}))
        return DocumentResult(pages=pages, raw={"engine": "tesseract", "language": self.language,
                              "dpi": self.dpi}, metadata={"local": True})
