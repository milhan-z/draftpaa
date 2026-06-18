"""Build the submission ZIP: exactly Report.pdf + Declaration.pdf.

The ZIP name uses PLACEHOLDER student IDs/names. Rename the output with your real
IDs/names before emailing it (see SUBMISSION_CHECKLIST.md):

    EF234405_DAA_FIN_StudentID1_Name1[_StudentID2_Name2].ZIP

Usage:
    python dist/make_zip.py
"""

from __future__ import annotations

import pathlib
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPORT = ROOT / "report" / "Report.pdf"
DECLARATION = ROOT / "report" / "Declaration.pdf"
# PLACEHOLDER name -- rename with real Student IDs and names before sending.
OUT = ROOT / "dist" / "EF234405_DAA_FIN_StudentID1_Name1.ZIP"


def main() -> None:
    missing = [p.name for p in (REPORT, DECLARATION) if not p.exists()]
    if missing:
        sys.exit(f"missing {missing}; build the PDFs first "
                 f"(python report/build_pdf.py ...)")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(REPORT, "Report.pdf")
        z.write(DECLARATION, "Declaration.pdf")
    print(f"wrote {OUT.name}  ({OUT.stat().st_size // 1024} KB)")
    print("NOTE: placeholder filename -- rename with real Student IDs/names before sending.")
    print("      The ZIP contains exactly: Report.pdf, Declaration.pdf")


if __name__ == "__main__":
    main()
