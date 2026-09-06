from __future__ import annotations

import json
from pathlib import Path

from quireflow.models import DocumentResult, PageResult


class MistralAdapter:
    """Mistral OCR adapter. The API key is supplied at runtime only."""
    name = "mistral"

    def __init__(self, api_key: str, model: str = "mistral-ocr-latest"):
        self.api_key, self.model = api_key, model

    def process_pdf(self, path: str) -> DocumentResult:
        try:
            from mistralai.client import Mistral
            from mistralai.client.utils.retries import BackoffStrategy, RetryConfig
        except ImportError as exc:
            raise RuntimeError("Install with `uv sync --extra mistral`.") from exc
        pdf = Path(path)
        # The SDK handles 429/5xx and honours Retry-After; a one-hour cap is
        # deliberately conservative for costly, long-running OCR jobs.
        retries = RetryConfig("backoff", BackoffStrategy(initial_interval=30_000,
            max_interval=300_000, exponent=2, max_elapsed_time=3_600_000), retry_connection_errors=True)
        with Mistral(api_key=self.api_key) as client:
            with pdf.open("rb") as handle:
                uploaded = client.files.upload(file={"file_name": pdf.name, "content": handle,
                    "content_type": "application/pdf"}, purpose="ocr", retries=retries)
            signed = client.files.get_signed_url(file_id=uploaded.id, retries=retries)
            response = client.ocr.process(model=self.model, include_image_base64=False,
                document={"type": "document_url", "document_url": signed.url}, retries=retries)
        raw = json.loads(response.model_dump_json())
        pages = [PageResult(index=page["index"], markdown=page["markdown"], text=page["markdown"],
                 metadata={k: v for k, v in page.items() if k not in {"index", "markdown"}})
                 for page in raw["pages"]]
        return DocumentResult(pages=pages, raw=raw, metadata={"model": raw.get("model", self.model),
                              "usage_info": raw.get("usage_info")})
