"""Print extracted PDF text to screen. Pure extraction test, no LLM, no store.

Usage (from backend/):
    source .venv/bin/activate
    PYTHONPATH=src python show_text.py ../data/resumes/01_aarav_patel_senior_software_engineer.pdf
    PYTHONPATH=src python show_text.py 01_aarav   # substring match also works
"""
import sys
from pathlib import Path

from funnel.extraction.factory import build_extractor

REPO_ROOT = Path(__file__).resolve().parent.parent
RESUME_DIR = REPO_ROOT / "data" / "resumes"


def resolve_target(arg: str) -> Path:
    p = Path(arg)
    if p.is_file():
        return p
    matches = sorted(RESUME_DIR.glob(f"*{arg}*.pdf"))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print(f"Multiple matches for {arg!r}:")
        for m in matches:
            print(f"  {m.name}")
        sys.exit(1)
    print(f"No PDF found for {arg!r} in {RESUME_DIR}")
    sys.exit(1)


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    target = resolve_target(sys.argv[1])
    result = build_extractor().extract(target)
    print(f"file:  {target.name}")
    print(f"pages: {len(result.pages)}  chars: {result.total_chars}")
    print("=" * 60)
    print(result.full_text or "(empty — likely scanned, needs OCR)")


if __name__ == "__main__":
    main()
