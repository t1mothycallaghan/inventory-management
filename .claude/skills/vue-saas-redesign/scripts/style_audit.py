#!/usr/bin/env python3
"""Audit hard-coded style values in a Vue 3 app's <style> blocks and .css files.

Reports, per file, how many raw spacing / radius / shadow / colour / font-size
values are used instead of CSS custom properties (var(--...)), and flags
layout offsets that are probably tied to the height of a top navigation bar
(sticky `top: 70px`, `calc(100vh - 64px)`, etc.) - these break silently when
the top bar is replaced by a sidebar.

Run it before the redesign (to plan the sweep) and after (to confirm the
counts went down and no stale header offsets remain).

Usage:
    python style_audit.py <client_src_dir> [--header-height 70] [--json]

Standard library only.
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

STYLE_BLOCK = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
DECL = re.compile(r"([a-z-]+)\s*:\s*([^;{}]+);", re.I)
COMMENT = re.compile(r"/\*.*?\*/", re.S)

SPACING_PROPS = {
    "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
    "padding-inline", "padding-block", "margin", "margin-top", "margin-right",
    "margin-bottom", "margin-left", "margin-inline", "margin-block",
    "gap", "row-gap", "column-gap",
}
LENGTH = re.compile(r"(?<![\w.-])-?\d*\.?\d+(px|rem|em)\b")
HEX = re.compile(r"#[0-9a-f]{3,8}\b", re.I)
RGB = re.compile(r"\brgba?\([^)]*\)", re.I)
OFFSET_PROPS = {"top", "height", "min-height", "max-height", "scroll-margin-top", "scroll-padding-top"}


def iter_css(path: Path):
    """Yield the CSS text of a .vue file's style blocks, or a whole .css file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".vue":
        for block in STYLE_BLOCK.findall(text):
            yield block
    else:
        yield text


def audit_file(path: Path, header_height: int):
    counts = Counter()
    offsets = []
    colours = Counter()
    for css in iter_css(path):
        css = COMMENT.sub("", css)
        for prop, value in DECL.findall(css):
            prop = prop.lower()
            value = value.strip()
            # Values already expressed through tokens are what we want; skip them.
            raw = re.sub(r"var\([^)]*\)", "", value)
            if prop in SPACING_PROPS and LENGTH.search(raw):
                counts["spacing"] += 1
            elif prop.startswith("border-radius") and LENGTH.search(raw):
                counts["radius"] += 1
            elif prop == "box-shadow" and raw.strip() not in ("none", ""):
                counts["shadow"] += 1
            elif prop == "font-size" and LENGTH.search(raw):
                counts["font_size"] += 1
            for c in HEX.findall(raw) + RGB.findall(raw):
                counts["colour"] += 1
                colours[c.lower()] += 1
            # A px value equal to the old header height in an offset-type
            # property almost always means "sit below the top bar".
            if header_height > 0 and prop in OFFSET_PROPS and re.search(rf"\b{header_height}px\b", value):
                offsets.append(f"{prop}: {value}")
    return counts, offsets, colours


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help="client source directory, e.g. client/src")
    ap.add_argument("--header-height", type=int, default=0,
                    help="height in px of the current top nav, to flag dependent offsets")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    root = Path(args.src)
    if not root.is_dir():
        sys.exit(f"not a directory: {root}")
    files = sorted(p for p in root.rglob("*") if p.suffix in (".vue", ".css")
                   and "node_modules" not in p.parts and "dist" not in p.parts)

    report, totals, all_colours = [], Counter(), Counter()
    for f in files:
        counts, offsets, colours = audit_file(f, args.header_height)
        totals.update(counts)
        all_colours.update(colours)
        if counts or offsets:
            report.append({"file": str(f.relative_to(root)), **counts, "header_offsets": offsets})

    tokens_defined = 0
    for f in files:
        for css in iter_css(f):
            tokens_defined += len(re.findall(r"--[a-z0-9-]+\s*:", css, re.I))

    if args.json:
        print(json.dumps({"totals": totals, "tokens_defined": tokens_defined,
                          "top_colours": all_colours.most_common(25), "files": report}, indent=2))
        return

    cols = ["spacing", "radius", "shadow", "font_size", "colour"]
    print(f"{'file':45} " + " ".join(f"{c:>9}" for c in cols))
    for r in sorted(report, key=lambda r: -sum(r.get(c, 0) for c in cols)):
        print(f"{r['file'][:45]:45} " + " ".join(f"{r.get(c, 0):>9}" for c in cols))
    print(f"{'TOTAL':45} " + " ".join(f"{totals.get(c, 0):>9}" for c in cols))
    print(f"\nCSS custom properties defined: {tokens_defined}")
    print("Most used raw colours:", ", ".join(f"{c} x{n}" for c, n in all_colours.most_common(15)))
    flagged = [(r["file"], o) for r in report for o in r["header_offsets"]]
    if args.header_height:
        print(f"\nOffsets tied to the {args.header_height}px header ({len(flagged)}):")
        for f, o in flagged:
            print(f"  {f}: {o}")


if __name__ == "__main__":
    main()
