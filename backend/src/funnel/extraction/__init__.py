"""PDF extraction wrapper. Library details stay behind PdfTextExtractor."""
from funnel.extraction.base import ExtractedPage, ExtractionResult, PdfTextExtractor
from funnel.extraction.factory import build_extractor

__all__ = ["ExtractedPage", "ExtractionResult", "PdfTextExtractor", "build_extractor"]
