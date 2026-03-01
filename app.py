#!/usr/bin/env python3
"""
PyMuPDF extraction HTTP service.
POST /extract with JSON {filename, document_id} -> extracts PDF, returns manifest.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from extract_pdf import extract

app = FastAPI()

DATA_DIR = Path(os.environ.get("PYMUPDF_DATA_DIR", "/data"))
OUTPUT_DIR = Path(os.environ.get("PYMUPDF_OUTPUT_DIR", "/output"))


class ExtractRequest(BaseModel):
    filename: str
    document_id: int


@app.post("/extract")
def extract_endpoint(req: ExtractRequest) -> dict:
    pdf_path = DATA_DIR / req.filename
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"PDF not found: {req.filename}")

    output_dir = OUTPUT_DIR / str(req.document_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = extract(str(pdf_path), str(output_dir))
    manifest_path = output_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())

    return manifest


@app.get("/health")
def health():
    return {"status": "ok"}
