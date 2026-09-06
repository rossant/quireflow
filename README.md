# Quireflow

**Resumable, page-auditable OCR for large PDFs.** Quireflow owns the reliable filesystem workflow; adapters own OCR engines.

It splits a PDF physically, preserves original page numbers, stores provider-native raw results, writes Markdown one page at a time, maintains a manifest, and creates `full.md` only after every page is complete. PDF content, OCR output, and API keys are never committed by default.

## Engines

- **Mistral OCR** (`mistral-ocr-latest`), for hosted Markdown OCR.
- **Tesseract**, local-only, through Poppler + Tesseract.
- New engines implement the small `OcrAdapter` protocol in `quireflow.models`.

## Quick start

```bash
uv sync --extra mistral
export MISTRAL_API_KEY="..." # do not put this in the repository
uv run quireflow book.pdf --adapter mistral --out runs/book
```

Or entirely locally:

```bash
uv sync
uv run quireflow book.pdf --adapter tesseract --lang fra+eng --out runs/book
```

Prepare chunks without OCR cost:

```bash
uv run quireflow book.pdf --adapter tesseract --out runs/book --prepare-only
```

Output is `chunks/`, `raw/`, `pages/`, `manifest.json`, and `full.md`. A rerun reuses valid raw chunk results. If an adapter fails, Quireflow persists the failure and stops rather than spending calls on later chunks.

## Scope

Quireflow does not claim that OCR engines are interchangeable: layout, assets, tables and confidence differ. It standardizes only the things every engine can share: original page identity, artifacts, resumption, and auditability.

License: MIT.
