from pathlib import Path

from pypdf import PdfWriter

from quireflow.engine import Run
from quireflow.models import DocumentResult, PageResult


class FakeAdapter:
    name = "fake"
    def process_pdf(self, path):
        from quireflow.engine import page_count
        return DocumentResult([PageResult(i, f"text {i}") for i in range(page_count(Path(path)))], {"fake": True})


def test_run_is_page_ordered_and_resumable(tmp_path):
    source = tmp_path / "source.pdf"; writer = PdfWriter()
    for _ in range(3): writer.add_blank_page(width=100, height=100)
    with source.open("wb") as out: writer.write(out)
    run = Run(source, tmp_path / "run", FakeAdapter(), chunk_size=2)
    run.run(); run.run()
    assert (tmp_path / "run" / "full.md").read_text().count("<!-- PAGE ") == 3
    assert (tmp_path / "run" / "pages" / "page_0003.md").read_text().startswith("<!-- PAGE 0003 -->")
