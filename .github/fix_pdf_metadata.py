#!/usr/bin/env python3
"""
Fixes the four PAC "Metadata and Settings" errors that LibreOffice leaves
behind after converting the PPTX to PDF:

  1. XMP Metadata missing            -> writes an XMP packet
  2. PDF/UA identifier missing       -> adds pdfuaid:part = 1 to the XMP
  3. Title in XMP metadata missing   -> sets dc:title
  4. Display of document title       -> sets ViewerPreferences /DisplayDocTitle true

Add to the GitHub Actions workflow AFTER the LibreOffice conversion step:

    - name: Fix PDF/UA metadata
      run: |
        pip install pikepdf
        python fix_pdf_metadata.py output.pdf "Tree Catalog"

(Replace output.pdf with whatever filename the LibreOffice step produces,
and adjust the title text as desired.)
"""
import sys
import pikepdf
from pikepdf import Name, Dictionary


def fix(path: str, title: str) -> None:
    with pikepdf.open(path, allow_overwriting_input=True) as pdf:
        # 1-3: XMP metadata, dc:title, and the PDF/UA identifier.
        with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
            meta["dc:title"] = title
            # PDF/UA identifier namespace + part
            meta["pdfuaid:part"] = "1"

        # Also mirror the title into the classic Info dictionary.
        pdf.docinfo["/Title"] = title

        # 4: tell viewers to show the document title (not the filename)
        # in the window title bar.
        root = pdf.Root
        if "/ViewerPreferences" not in root:
            root.ViewerPreferences = pdf.make_indirect(Dictionary())
        root.ViewerPreferences[Name("/DisplayDocTitle")] = True

        # Belt and braces: make sure the document is marked as tagged and
        # has a language set (LibreOffice usually does both, but if either
        # is missing PAC reports more errors).
        if "/MarkInfo" not in root:
            root.MarkInfo = pdf.make_indirect(Dictionary(Marked=True))
        elif "/Marked" not in root.MarkInfo:
            root.MarkInfo[Name("/Marked")] = True
        if "/Lang" not in root:
            root[Name("/Lang")] = pikepdf.String("en-US")

        pdf.save(path)
    print(f"fix_pdf_metadata: wrote title, XMP, PDF/UA id, and viewer prefs to {path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: fix_pdf_metadata.py <file.pdf> [title]")
    pdf_path = sys.argv[1]
    doc_title = sys.argv[2] if len(sys.argv) > 2 else "Tree Catalog"
    fix(pdf_path, doc_title)
