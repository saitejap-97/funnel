"""Extraction: chained fallback + empty-PDF flag path."""
from pathlib import Path

from funnel.extraction.base import ExtractedPage, ExtractionResult
from funnel.extraction.factory import ChainedExtractor


class _Empty:
    def extract(self, path: Path) -> ExtractionResult:
        return ExtractionResult(source_file=str(path), pages=[], full_text="")


class _Good:
    def extract(self, path: Path) -> ExtractionResult:
        return ExtractionResult(
            source_file=str(path),
            pages=[ExtractedPage(page_no=1, text="Jane Doe Python", char_count=15)],
            full_text="Jane Doe Python",
        )


class _Boom:
    def extract(self, path: Path):
        raise RuntimeError("pdf lib exploded")


def test_fallback_used_when_primary_empty(tmp_path):
    ext = ChainedExtractor(primary=_Empty(), fallback=_Good())
    res = ext.extract(tmp_path / "a.pdf")
    assert "Python" in res.full_text


def test_empty_when_both_empty(tmp_path):
    ext = ChainedExtractor(primary=_Empty(), fallback=_Empty())
    res = ext.extract(tmp_path / "a.pdf")
    assert res.full_text == ""  # caller flags needs_ocr


def test_fallback_used_on_exception(tmp_path):
    ext = ChainedExtractor(primary=_Boom(), fallback=_Good())
    assert "Python" in ext.extract(tmp_path / "a.pdf").full_text


def test_cid_artifacts_cleaned(tmp_path):
    class _Cid:
        def extract(self, path: Path) -> ExtractionResult:
            from funnel.extraction.base import ExtractedPage
            return ExtractionResult(
                source_file=str(path),
                pages=[ExtractedPage(page_no=1, text="(cid:127) shipped X",
                                     char_count=100)],
                full_text="(cid:127) shipped X, " + "detail " * 20,
            )

    ext = ChainedExtractor(primary=_Cid(), fallback=_Empty())
    res = ext.extract(tmp_path / "a.pdf")
    assert "(cid:" not in res.full_text
    assert "• shipped X" in res.full_text
