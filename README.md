# docker-pymupdf-tesseract

PyMuPDF PDF extraction API with Tesseract OCR. FastAPI service that extracts text, layout markdown, page pixmaps, embedded images, and runs Tesseract OCR on scanned pages.

## API

- **POST /extract** – JSON body `{filename, document_id}`. Expects PDF at `DATA_DIR/filename`, writes output to `OUTPUT_DIR/document_id`.
- **GET /health** – Health check.

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `PYMUPDF_DATA_DIR` | `/data` | Directory containing PDFs (mount volume here) |
| `PYMUPDF_OUTPUT_DIR` | `/output` | Output directory for manifests and page images |
| `PYMUPDF_OCR_ENABLED` | `true` | Enable Tesseract OCR |
| `PYMUPDF_OCR_WHEN_EMPTY` | `true` | Run OCR only when page text is empty/short |
| `PYMUPDF_OCR_EMPTY_THRESHOLD` | `50` | Character threshold for "empty" page |

## Build

```bash
docker build --platform linux/amd64 -t christhompsontldr/docker-pymupdf-tesseract:latest .
```

## Run (local)

```bash
docker run -p 8000:8000 \
  -v /path/to/pdfs:/data:ro \
  -v /path/to/output:/output \
  christhompsontldr/docker-pymupdf-tesseract:latest
```

## License

MIT
