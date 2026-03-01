#!/usr/bin/env python3
"""
PyMuPDF PDF extraction service.
Renders each page as PNG, extracts text/metadata, embedded images.
Tesseract OCR for scanned pages (when page has little/no extractable text).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pymupdf

try:
    import pymupdf.layout  # noqa: F401
    import pymupdf4llm
    HAS_LAYOUT = True
except ImportError:
    HAS_LAYOUT = False

# Tesseract OCR: enabled, and run only when page text is empty/short (scanned pages)
OCR_ENABLED = os.environ.get("PYMUPDF_OCR_ENABLED", "true").lower() in ("1", "true", "yes")
OCR_WHEN_EMPTY = os.environ.get("PYMUPDF_OCR_WHEN_EMPTY", "true").lower() in ("1", "true", "yes")
OCR_EMPTY_THRESHOLD = int(os.environ.get("PYMUPDF_OCR_EMPTY_THRESHOLD", "50"))


def extract(pdf_path: str, output_dir: str, dpi: int = 150) -> dict:
    """Extract all data from PDF. Writes page PNGs to output_dir."""
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(exist_ok=True)
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)

    doc = pymupdf.open(pdf_path)
    result = {
        "metadata": doc.metadata,
        "outline": doc.get_toc(),
        "embedded_files": list(doc.embfile_names()) if doc.embfile_count() else [],
        "page_count": len(doc),
        "pages": [],
        "embedded_images": [],
    }

    for i, page in enumerate(doc):
        page_num = i + 1
        page_data = {"page_number": page_num}

        # Page pixmap (screenshot) - primary output
        pix = page.get_pixmap(dpi=dpi)
        png_path = pages_dir / f"page_{page_num:04d}.png"
        pix.save(str(png_path))
        page_data["pixmap_path"] = str(png_path.relative_to(output_dir))

        # Text extractions
        page_data["pymupdf_text"] = page.get_text("text", sort=True)
        page_data["pymupdf_blocks"] = page.get_text("blocks", sort=True)
        page_data["pymupdf_words"] = page.get_text("words", sort=True)
        page_data["pymupdf_html"] = page.get_text("html")
        page_data["pymupdf_xhtml"] = page.get_text("xhtml")
        page_data["pymupdf_dict"] = page.get_text("dict", sort=True)
        page_data["pymupdf_rawdict"] = page.get_text("rawdict", sort=True)
        page_data["pymupdf_xml"] = page.get_text("xml")
        page_data["pymupdf_links"] = [dict(link) for link in page.get_links()]
        page_data["pymupdf_drawings"] = page.get_drawings()

        # Layout-enhanced markdown (if pymupdf4llm available)
        if HAS_LAYOUT:
            page_data["pymupdf_markdown"] = pymupdf4llm.to_markdown(doc, pages=[i])
            page_data["pymupdf_layout_json"] = pymupdf4llm.to_json(doc, pages=[i])
            page_data["pymupdf_layout_text"] = pymupdf4llm.to_text(doc, pages=[i])
        else:
            page_data["pymupdf_markdown"] = page.get_text("text", sort=True)
            page_data["pymupdf_layout_json"] = None
            page_data["pymupdf_layout_text"] = None

        # Tesseract OCR (when page has little/no extractable text — scanned pages)
        page_data["pymupdf_ocr_text"] = None
        if OCR_ENABLED:
            text_len = len((page_data.get("pymupdf_text") or "").strip())
            run_ocr = not OCR_WHEN_EMPTY or text_len < OCR_EMPTY_THRESHOLD
            if run_ocr:
                try:
                    tp = page.get_textpage_ocr(dpi=dpi)
                    page_data["pymupdf_ocr_text"] = (tp.extractText(sort=True) or "").strip() or None
                except Exception:
                    page_data["pymupdf_ocr_text"] = None

        # Annotations
        try:
            page_data["pymupdf_annotations"] = [
                {k: str(v) for k, v in a.info.items()} for a in page.annots()
            ]
        except Exception:
            page_data["pymupdf_annotations"] = []

        # SVG
        try:
            page_data["pymupdf_svg"] = page.get_svg_image()
        except Exception:
            page_data["pymupdf_svg"] = None

        result["pages"].append(page_data)

        # Embedded images from this page
        for img_info in page.get_images():
            xref = img_info[0]
            try:
                base_img = doc.extract_image(xref)
                ext = base_img["ext"]
                img_bytes = base_img["image"]
                img_path = images_dir / f"page{page_num}_xref{xref}.{ext}"
                img_path.write_bytes(img_bytes)
                result["embedded_images"].append({
                    "document_page_number": page_num,
                    "xref": xref,
                    "path": str(img_path.relative_to(output_dir)),
                })
            except Exception:
                pass

    doc.close()

    # Write manifest
    manifest_path = output_dir / "manifest.json"

    def to_json_safe(obj):
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        if isinstance(obj, dict):
            return {k: to_json_safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [to_json_safe(v) for v in obj]
        return str(obj)

    manifest = {
        "metadata": to_json_safe(result["metadata"]),
        "outline": result["outline"],
        "embedded_files": result["embedded_files"],
        "page_count": result["page_count"],
        "pages": [{k: to_json_safe(v) for k, v in p.items()} for p in result["pages"]],
        "embedded_images": result["embedded_images"],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str))

    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: extract_pdf.py <pdf_path> <output_dir> [dpi]", file=sys.stderr)
        sys.exit(1)
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2]
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 150
    extract(pdf_path, output_dir, dpi=dpi)
    print(f"Extracted to {output_dir}")
