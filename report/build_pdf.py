"""Render a Markdown file to a self-contained, styled PDF (no LaTeX needed).

Pipeline: Markdown -> HTML (python-markdown) -> headless Chrome/Edge --print-to-pdf.
Local images are inlined as base64 data URIs so the intermediate HTML and the PDF
are fully self-contained.

Usage:
    python report/build_pdf.py report/Report.md report/Report.pdf
    python report/build_pdf.py report/Declaration.md report/Declaration.pdf

Requires the `markdown` package (``pip install markdown``) and either Microsoft
Edge or Google Chrome installed (standard on Windows 11).
"""

from __future__ import annotations

import base64
import mimetypes
import pathlib
import re
import subprocess
import sys

import markdown

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]

CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body { font: 10.8pt/1.55 Georgia, "Times New Roman", serif; color: #16181d; }
h1, h2, h3, h4 { font-family: "Segoe UI", Arial, sans-serif; color: #0f1117; line-height: 1.25; }
h1 { font-size: 19pt; border-bottom: 2px solid #2563eb; padding-bottom: 4px; margin-top: 26px; }
h2 { font-size: 15pt; margin-top: 22px; border-bottom: 1px solid #d4d8e0; padding-bottom: 3px; }
h3 { font-size: 12.5pt; margin-top: 16px; color: #2b3140; }
h4 { font-size: 11pt; margin-top: 12px; color: #3a4150; }
p { margin: 7px 0; text-align: justify; }
code { font-family: "Consolas", "Courier New", monospace; font-size: 9.4pt;
       background: #f1f3f8; padding: 1px 5px; border-radius: 4px; }
pre { background: #0f1117; color: #e6e9f0; padding: 11px 14px; border-radius: 8px;
      overflow-x: auto; font-size: 8.9pt; line-height: 1.45; }
pre code { background: none; color: inherit; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 9.6pt; }
th, td { border: 1px solid #c7ccd6; padding: 5px 9px; text-align: left; }
th { background: #eef2fb; font-family: "Segoe UI", sans-serif; }
tr:nth-child(even) td { background: #f7f9fc; }
img { max-width: 100%; height: auto; display: block; margin: 10px auto; border: 1px solid #e3e6ee; border-radius: 6px; }
blockquote { border-left: 4px solid #f5a623; background: #fff8ec; margin: 10px 0;
             padding: 6px 14px; color: #5a4a23; }
hr { border: none; border-top: 1px solid #d4d8e0; margin: 18px 0; }
a { color: #2563eb; text-decoration: none; }
strong { color: #0f1117; }
ul, ol { margin: 7px 0 7px 4px; padding-left: 22px; }
li { margin: 3px 0; }
.page-break { page-break-before: always; }
h1, h2, h3 { page-break-after: avoid; }
table, pre, img { page-break-inside: avoid; }
"""


def inline_images(html: str, base_dir: pathlib.Path) -> str:
    """Replace local <img src=...> with base64 data URIs."""
    def repl(match: re.Match) -> str:
        src = match.group(1)
        if src.startswith(("http://", "https://", "data:")):
            return match.group(0)
        path = (base_dir / src).resolve()
        if not path.exists():
            return match.group(0)
        mime = mimetypes.guess_type(str(path))[0] or "image/png"
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f'src="data:{mime};base64,{data}"'

    return re.sub(r'src="([^"]+)"', repl, html)


def build(md_path: pathlib.Path, pdf_path: pathlib.Path) -> None:
    text = md_path.read_text(encoding="utf-8")
    body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "toc", "attr_list", "sane_lists"],
    )
    body = inline_images(body, md_path.parent)
    html = (
        f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )
    html_path = pdf_path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")

    browser = next((b for b in BROWSERS if pathlib.Path(b).exists()), None)
    if browser is None:
        sys.exit("No Chrome/Edge found; cannot render PDF. Intermediate HTML written: "
                 f"{html_path}")

    subprocess.run(
        [browser, "--headless", "--disable-gpu", "--no-sandbox",
         "--print-to-pdf-no-header", f"--print-to-pdf={pdf_path}",
         html_path.as_uri()],
        check=True, timeout=120,
    )
    print(f"wrote {pdf_path}  ({pdf_path.stat().st_size // 1024} KB)")


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: python report/build_pdf.py <input.md> <output.pdf>")
    build(pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve())


if __name__ == "__main__":
    main()
