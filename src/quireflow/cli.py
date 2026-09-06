from __future__ import annotations

import argparse
import os
from pathlib import Path

from quireflow.adapters import MistralAdapter, TesseractAdapter
from quireflow.engine import Run


def main() -> None:
    parser = argparse.ArgumentParser(description="Resumable OCR for large PDFs")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--adapter", choices=("mistral", "tesseract"), required=True)
    parser.add_argument("--chunk-size", type=int, default=100)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--lang", default="eng", help="Tesseract language(s)")
    parser.add_argument("--mistral-key-env", default="MISTRAL_API_KEY")
    args = parser.parse_args()
    if args.adapter == "mistral":
        key = os.environ.get(args.mistral_key_env)
        if not key: parser.error(f"Set {args.mistral_key_env}; Quireflow never stores API keys.")
        adapter = MistralAdapter(key)
    else:
        adapter = TesseractAdapter(args.lang)
    run = Run(args.pdf, args.out, adapter, args.chunk_size)
    run.prepare() if args.prepare_only else run.run()
