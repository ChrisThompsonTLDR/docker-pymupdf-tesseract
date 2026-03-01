# PyMuPDF + Tesseract OCR - PDF extraction API
# POST /extract with JSON {filename, document_id}
# Expects PDF at DATA_DIR/filename, writes output to OUTPUT_DIR/document_id
FROM python:3.12-slim

WORKDIR /app

# Tesseract OCR for PyMuPDF get_textpage_ocr (scanned pages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pymupdf pymupdf4llm fastapi uvicorn

COPY extract_pdf.py app.py /app/

EXPOSE 8000

ENV PYMUPDF_DATA_DIR=/data
ENV PYMUPDF_OUTPUT_DIR=/output

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
