#!/usr/bin/env python
"""Verify each downloaded PDF is the paper its filename claims.

Extracts the first ~400 chars of page 1 and checks that the filename slug's
tokens actually appear. A MISMATCH means the arXiv ID resolved but points at a
different paper — the citation is wrong and must not be used.

Usage: python scripts/verify_literature.py [--titles]
"""

from __future__ import annotations

import pathlib
import re
import sys

from pypdf import PdfReader

LIT = pathlib.Path(__file__).parent.parent / "papers" / "literature"

# Slug tokens too generic to be evidence of a match.
STOPWORDS = {
    "cad", "bench", "the", "for", "and", "of", "a", "to", "in", "on", "loss",
    "model", "models", "data", "learning", "deep", "neural", "review",
    "generation", "generative", "sr", "llm", "vlm", "2024", "2026",
}


def _ascii(s: str) -> str:
    """Windows consoles default to cp1252; strip anything it cannot encode."""
    return s.encode("ascii", "replace").decode("ascii")


def first_page_text(path: pathlib.Path) -> str:
    try:
        reader = PdfReader(str(path))
        if not reader.pages:
            return ""
        return " ".join(reader.pages[0].extract_text().split())[:600]
    except Exception as exc:  # noqa: BLE001
        return f"<<UNREADABLE: {exc}>>"


def main() -> int:
    show_titles = "--titles" in sys.argv
    pdfs = sorted(LIT.glob("*.pdf"))
    if not pdfs:
        print("no PDFs found — run scripts/fetch_literature.sh first")
        return 1

    matched, suspect, unreadable = [], [], []

    for pdf in pdfs:
        stem = pdf.stem
        arxiv_id, _, slug = stem.partition("_")
        text = first_page_text(pdf)

        if text.startswith("<<UNREADABLE"):
            unreadable.append((stem, text))
            continue

        # Collapse ALL non-alphanumerics, including spaces: PDF extraction often
        # letter-spaces styled titles ("D y n Scal i ng"), which would otherwise
        # register as a false mismatch.
        norm = re.sub(r"[^a-z0-9]+", "", text.lower())
        tokens = [t for t in slug.split("-") if t not in STOPWORDS and len(t) > 2]

        if not tokens:
            matched.append((stem, text))  # slug carried no checkable signal
            continue

        hits = sum(1 for t in tokens if t in norm)
        if hits >= max(1, len(tokens) // 2):
            matched.append((stem, text))
        else:
            suspect.append((stem, tokens, hits, text[:200]))

        if show_titles:
            print(f"{arxiv_id}  {_ascii(text[:110])}")

    print(f"\nmatched={len(matched)}  suspect={len(suspect)}  unreadable={len(unreadable)}")

    if suspect:
        print("\n=== SUSPECT (slug tokens not found on page 1 — verify manually) ===")
        for stem, tokens, hits, head in suspect:
            print(f"\n  {stem}")
            print(f"    tokens={tokens} hits={hits}")
            print(f"    page1: {_ascii(head)}")

    if unreadable:
        print("\n=== UNREADABLE ===")
        for stem, err in unreadable:
            print(f"  {stem}: {err}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
