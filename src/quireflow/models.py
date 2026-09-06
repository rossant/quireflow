from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


@dataclass
class PageResult:
    """Provider-neutral result; ``index`` is zero-based within the input PDF."""
    index: int
    markdown: str
    text: str | None = None
    confidence: float | None = None
    assets: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentResult:
    pages: list[PageResult]
    raw: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


class OcrAdapter(Protocol):
    """An adapter owns provider-specific input, invocation and response parsing."""
    name: str

    def process_pdf(self, path: str) -> DocumentResult: ...


def result_to_dict(result: DocumentResult) -> dict[str, Any]:
    return {"pages": [asdict(page) for page in result.pages], "raw": result.raw,
            "metadata": result.metadata}


def result_from_dict(data: dict[str, Any]) -> DocumentResult:
    return DocumentResult(pages=[PageResult(**page) for page in data["pages"]],
                          raw=data["raw"], metadata=data.get("metadata", {}))
