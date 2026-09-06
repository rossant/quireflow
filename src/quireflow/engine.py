from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from quireflow.models import OcrAdapter, result_from_dict, result_to_dict


def atomic_json(path: Path, value: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def page_count(pdf: Path) -> int:
    return len(PdfReader(str(pdf)).pages)


def split(source: Path, destination: Path, start: int, end: int) -> None:
    if destination.exists() and page_count(destination) == end - start + 1:
        return
    writer, reader = PdfWriter(), PdfReader(str(source))
    for index in range(start - 1, end):
        writer.add_page(reader.pages[index])
    with destination.open("wb") as handle:
        writer.write(handle)


class Run:
    """Filesystem-native, idempotent execution of one adapter over a PDF."""
    def __init__(self, source: Path, output: Path, adapter: OcrAdapter, chunk_size: int = 100):
        self.source, self.output, self.adapter, self.chunk_size = source.resolve(), output.resolve(), adapter, chunk_size
        self.chunks, self.raw, self.pages = output / "chunks", output / "raw", output / "pages"
        for directory in (self.chunks, self.raw, self.pages): directory.mkdir(parents=True, exist_ok=True)
        self.manifest_path = output / "manifest.json"
        self.total = page_count(self.source)
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> dict:
        if self.manifest_path.exists():
            data = json.loads(self.manifest_path.read_text())
            if data["source"]["path"] != str(self.source) or data["source"]["pages"] != self.total:
                raise RuntimeError("Output directory belongs to another source PDF.")
            return data
        return {"version": 1, "source": {"path": str(self.source), "pages": self.total},
                "adapter": self.adapter.name, "chunks": [], "pages": {}}

    def _save(self) -> None:
        self.manifest["chunks"].sort(key=lambda item: item["start"])
        atomic_json(self.manifest_path, self.manifest)

    def prepare(self) -> None:
        for start in range(1, self.total + 1, self.chunk_size):
            end = min(self.total, start + self.chunk_size - 1)
            name = f"pages_{start:04d}_{end:04d}"
            pdf = self.chunks / f"{name}.pdf"
            split(self.source, pdf, start, end)
            if not any(c["start"] == start for c in self.manifest["chunks"]):
                self.manifest["chunks"].append({"start": start, "end": end, "pdf": str(pdf),
                    "raw": str(self.raw / f"{name}.json"), "status": "prepared", "error": None})
        self._save()

    def run(self) -> None:
        self.prepare()
        for chunk in self.manifest["chunks"]:
            expected = chunk["end"] - chunk["start"] + 1
            raw_path = Path(chunk["raw"])
            if raw_path.exists():
                try:
                    result = result_from_dict(json.loads(raw_path.read_text()))
                    if [page.index for page in result.pages] != list(range(expected)):
                        raise ValueError("bad page indexes")
                except Exception:
                    chunk.update(status="error", error="Invalid existing raw result; preserved without overwrite.")
                    self._save(); return
            else:
                try:
                    result = self.adapter.process_pdf(chunk["pdf"])
                    if [page.index for page in result.pages] != list(range(expected)):
                        raise RuntimeError("Adapter returned missing, duplicate, or unordered page indexes.")
                    atomic_json(raw_path, result_to_dict(result))
                except Exception as exc:
                    chunk.update(status="error", error=str(exc)); self._save(); return
            for offset, page in enumerate(result.pages):
                number = chunk["start"] + offset
                target = self.pages / f"page_{number:04d}.md"
                target.write_text(f"<!-- PAGE {number:04d} -->\n\n{page.markdown.rstrip()}\n", encoding="utf-8")
                self.manifest["pages"][f"{number:04d}"] = {"status": "complete", "file": str(target),
                    "chunk": [chunk["start"], chunk["end"]]}
            chunk.update(status="complete", error=None); self._save()
        if len(self.manifest["pages"]) == self.total and all(c["status"] == "complete" for c in self.manifest["chunks"]):
            full = "\n".join((self.pages / f"page_{n:04d}.md").read_text(encoding="utf-8").rstrip()
                             for n in range(1, self.total + 1)) + "\n"
            (self.output / "full.md").write_text(full, encoding="utf-8")
