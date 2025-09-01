# Secret Grid Renderer

This repository provides a Python script (`secret_grid.py`) that **renders a grid of glyphs from a published Google Doc table**.  
The table must be structured so that entries are laid out as **three consecutive cells/lines**:

```
<x-coordinate>
<glyph>
<y-coordinate>
```

Repeated down the table. The script downloads the document, parses the entries, and reconstructs the glyph grid directly in the terminal.

---

## Features

- Fetches **published-to-web Google Docs HTML** and cleans it to extract table contents.  
- Parses coordinates (`x`, `y`) with a corresponding glyph.  
- Handles glyphs via **Unicode code points**, ensuring correct rendering of symbols and letters (including complex glyphs).  
- Automatically builds and prints a grid of the glyphs.  
- Provides configurable options for blank cell fillers and safety limits.

---

## Installation

Clone this repository and install the required dependency:

```bash
git clone https://github.com/yourusername/secret-grid-renderer.git
cd secret-grid-renderer
pip install -r requirements.txt
```

Contents of `requirements.txt`:

```
requests
```

---

## Usage

Run the script from the command line:

```bash
python secret_grid.py "{GOOGLE_DOC_PUB_URL}"
```

Example:

```bash
python secret_grid.py "https://docs.google.com/document/d/e/2PACX-1vRPzbNQcx5UriHSbZ-9vmsTow_R6RRe7eyAU60xIF9Dlz-vaHiHNO2TKgDi7jy4ZpTpNqM7EvEcfr_p/pub"
```

---

## Example Output

```
[info] parsed 331 triples, 331 unique cells -> grid 88x7
██░    ███░ ██████░    ███████░     ██░     ██░     ██████████░ ████████░    ████████░  
██░  ███░     ██░    ███░    ██░   ████░   ████░    ██░         ██░     ██░  ██░     ██░
██░███░       ██░   ███░           ██░██░ ██░██░    ██░         ██░      ██░ ██░     ██░
████░         ██░   ██░           ███░ ██░██░ ██░   ████████░   ██░      ██░ ████████░  
██░███░       ██░   ███░          ██░  █████░ ███░  ██░         ██░      ██░ ██░     ██░
██░  ███░     ██░    ███░    ██░ ███░   ███░   ██░  ██░         ██░     ██░  ██░     ██░
██░    ███░ ██████░    ███████░  ██░           ███░ ██████████░ ████████░    ████████░  
```

---

## How It Works

1. **Fetch HTML** – Downloads the published Google Doc HTML.  
2. **Clean & Parse** – Strips unnecessary tags while preserving cell/line boundaries.  
3. **Extract Triples** – Reads the table as (`x`, `glyph`, `y`) entries.  
4. **Build Grid** – Creates an empty grid and fills glyphs at specified coordinates.  
5. **Render** – Prints the glyph grid to stdout.

---

## Notes

- Ensure the Google Doc is published to the web (`File > Share > Publish to web`) and structured correctly with **triplets of cells**.  
- Overwrites of the same `(x, y)` coordinate are allowed (last one wins).  
- The script includes safety checks to avoid accidental huge allocations.  
