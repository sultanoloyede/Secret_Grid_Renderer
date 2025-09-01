"""
Render a glyph grid from a published Google Doc table where entries are laid out as
three consecutive cells/lines:  <x> , <glyph> , <y>  (repeated down the table).

Usage:
    python secret_grid.py "{LINK}"
"""

from __future__ import annotations

import argparse
import html as ihtml
import re
import sys
import unicodedata
from typing import Dict, Iterable, List, Tuple

import requests


# ----------------------------- Fetch & Clean -----------------------------

def fetch_html(url: str) -> str:
    """Download the published-to-web Google Doc HTML (raises on failure)."""
    headers = {
        "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
    }
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.text


def clean_html_preserve_lines(html: str) -> List[str]:
    """
    Strip tags while preserving table/paragraph boundaries as line breaks so each
    cell ends up as its own line. Return a list of non-empty, stripped lines.
    """
    # Remove script/style blocks
    html = re.sub(r"(?is)<script.*?</script>", "", html)
    html = re.sub(r"(?is)<style.*?</style>", "", html)

    # Convert logical boundaries to newlines
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    html = re.sub(r"(?i)</(p|div|tr|td|th|li|h\d)\s*>", "\n", html)

    # Strip remaining tags
    text = re.sub(r"(?s)<[^>]+>", " ", html)

    # Unescape HTML entities (e.g., &#9608; -> '█')
    text = ihtml.unescape(text)

    # Normalize spacing but KEEP our newlines
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)

    # Return non-empty lines
    return [ln.strip() for ln in text.split("\n") if ln.strip()]


# ----------------------------- Unicode Helpers -----------------------------

def to_codepoints(s: str) -> Tuple[int, ...]:
    """
    Convert a (glyph) string to a tuple of Unicode code points.
    We typically expect a single user-visible glyph; if multiple code points
    form one glyph (e.g., with variation selectors), we keep them all.
    """
    return tuple(ord(ch) for ch in s)


def from_codepoints(cps: Tuple[int, ...]) -> str:
    """Convert a tuple of Unicode code points back to a string."""
    return "".join(chr(cp) for cp in cps)


def first_symbol_or_letter(s: str) -> str | None:
    """
    From a line, extract the first character that is a Unicode Letter (L*)
    or Symbol (S*) category. This avoids picking punctuation like '/' or ','.
    Returns None if none found.
    """
    for ch in s:
        cat = unicodedata.category(ch)
        if cat.startswith("L") or cat.startswith("S"):
            return ch
    return None


def line_is_int(s: str) -> bool:
    """True if the entire line is a non-negative integer."""
    return bool(re.fullmatch(r"\d+", s))


# ----------------------------- Parsing -----------------------------

def parse_triples_from_lines(lines: List[str]) -> Tuple[Dict[Tuple[int, int], Tuple[int, ...]], int, int, int]:
    """
    Parse consecutive triplets of lines as (x, glyph, y).
    Returns:
      cells: {(x, y): codepoints_tuple}
      hits:  total triples recognized (including overwrites)
      max_x, max_y: maximum coordinates seen, or (-1, -1) if none
    """
    cells: Dict[Tuple[int, int], Tuple[int, ...]] = {}
    hits = 0
    max_x = max_y = -1

    i = 0
    n = len(lines)
    while i + 2 < n:
        x_line, glyph_line, y_line = lines[i], lines[i + 1], lines[i + 2]

        if line_is_int(x_line) and line_is_int(y_line):
            # Pick the first symbol/letter from the glyph line
            glyph_char = first_symbol_or_letter(glyph_line)
            if glyph_char is None:
                # If no symbol/letter, as a fallback, allow ANY single character line
                # (rarely needed; still avoids pulling punctuation from longer strings)
                if len(glyph_line) == 1:
                    glyph_char = glyph_line
            if glyph_char is not None:
                x = int(x_line)
                y = int(y_line)
                if x >= 0 and y >= 0:
                    cells[(x, y)] = to_codepoints(glyph_char)
                    hits += 1
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                i += 3
                continue

        # If this group didn't match, advance by 1 and keep scanning
        i += 1

    return cells, hits, max_x, max_y


# ----------------------------- Grid & Render -----------------------------

def build_grid(width: int, height: int, blank: str = " ") -> List[List[str]]:
    """Create an empty width×height grid filled with `blank`."""
    return [[blank for _ in range(width)] for _ in range(height)]


def render_cells_into_grid(
    grid: List[List[str]],
    cells: Dict[Tuple[int, int], Tuple[int, ...]]
) -> None:
    """Place decoded glyphs into the grid at their (x, y) positions."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    for (x, y), cps in cells.items():
        if 0 <= x < width and 0 <= y < height:
            grid[y][x] = from_codepoints(cps)


def print_grid(grid: List[List[str]]) -> None:
    """Print the grid row-by-row."""
    out = sys.stdout
    for row in grid:
        out.write("".join(row) + "\n")


# ----------------------------- Main -----------------------------

def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Render a glyph grid from a published Google Doc (no hard-coded glyphs)."
    )
    ap.add_argument("url", help="Published-to-web Google Doc URL ending with /pub")
    ap.add_argument("--blank", default=" ", help="Fill character for empty cells (default: space)")
    ap.add_argument("--max-cells", type=int, default=1_000_000,
                    help="Safety cap on width*height (default: 1,000,000)")
    args = ap.parse_args(list(argv) if argv is not None else None)

    try:
        html = fetch_html(args.url)
    except Exception as e:
        print(f"[error] failed to download: {e}")
        return 1

    lines = clean_html_preserve_lines(html)
    cells, hits, max_x, max_y = parse_triples_from_lines(lines)

    if max_x < 0 or max_y < 0:
        print("[warn] parsed 0 triples — ensure the Doc uses three-cell groups: x, glyph, y.")
        return 2

    width, height = max_x + 1, max_y + 1
    if width * height > args.max_cells or width > 5000 or height > 5000:
        print(f"[warn] suspicious grid {width}x{height} from {len(cells)} cells; refusing to allocate.")
        # Show a few samples to help debug
        for i, ((sx, sy), cps) in enumerate(list(cells.items())[:10]):
            print(f"  sample {i+1}: {from_codepoints(cps)} {sx} {sy}  (cp={cps})")
        return 3

    print(f"[info] parsed {hits} triples, {len(cells)} unique cells -> grid {width}x{height}")
    grid = build_grid(width, height, blank=args.blank)
    render_cells_into_grid(grid, cells)
    print_grid(grid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
