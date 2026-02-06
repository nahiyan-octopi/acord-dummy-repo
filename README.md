# ACORD Data Extractor API

API for extracting structured data from ACORD 25 Certificate of Liability Insurance PDFs using PyPDF and OpenAI.

---

## Overview

This API processes fillable ACORD PDFs and returns a standardized JSON response. The pipeline:

1. **Detects ACORD forms** using field-name patterns.
2. **Extracts form fields** from fillable PDFs via PyPDF.
3. **Organizes fields** into a schema using an OpenAI model.
4. **Formats output** for the UI.

### Supported Forms

| Form     | Description                        |
| -------- | ---------------------------------- |
| ACORD 25 | Certificate of Liability Insurance |

---

## Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API key
- pipenv (recommended) or pip

### Installation

```bash
cd acord-dummy-repo
pipenv install
# Or with pip
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4-turbo
OPENAI_TEMPERATURE=0
OPENAI_MAX_TOKENS=4096
```

`OPENAI_MODEL` defaults to `gpt-4-turbo` when not provided.

### Running the Server

```bash
pipenv run python -m app.app
# Or with uvicorn directly
pipenv run uvicorn app.app:app --host 0.0.0.0 --port 8001
```

The API will be available at `http://localhost:8001`.

---

## API Reference

### Base URL

```
http://localhost:8001
```

### Health Check

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "model": "gpt-4-turbo"
}
```

---

### Extract ACORD Data

```http
POST /api/extract-acord
Content-Type: multipart/form-data
```

**Request:**

| Parameter | Type | Required | Description                       |
| --------- | ---- | -------- | --------------------------------- |
| `file`    | File | Yes      | PDF file (ACORD 25 fillable form) |

**Response:**

```json
{
  "success": true,
  "formatted_data": {
    "information": {
      "certificate_date": "01/15/2026",
      "description_of_operations": "General landscaping services...",
      "certificate_holder": "City of Denver"
    },
    "general_liability": {
      "policy_information": {
        "policy_number": "MNI-GL-775231",
        "effective_date": "01/01/2026",
        "expiration_date": "01/01/2027",
        "additional_insured": "Yes",
        "subrogation_waived": "No"
      },
      "policy_options": {
        "claims_made": "No",
        "occurrence": "Yes"
      },
      "policy_limits": {
        "each_occurrence": "1,000,000",
        "general_aggregate": "2,000,000"
      }
    }
  },
  "file_info": {
    "filename": "ACORD25_form.pdf",
    "file_size_kb": 150.4
  },
  "error": null,
  "json_file": "extraction_20260121_160000.json"
}
```

**Error Response:**

```json
{
  "success": false,
  "formatted_data": {},
  "file_info": { "filename": "ACORD25_form.pdf" },
  "error": "PDF is not a fillable form. Use OCR/AI extraction instead."
}
```

---

### Detect ACORD Form

```http
POST /api/detect-acord
Content-Type: multipart/form-data
```

**Response:**

```json
{
  "is_fillable": true,
  "is_acord": true,
  "field_count": 130,
  "acord_pattern_matches": 9,
  "confidence": "high",
  "detected_form_type": "ACORD 25 - Certificate of Liability Insurance",
  "matched_patterns": ["NamedInsured", "Producer_"],
  "filename": "ACORD25_form.pdf"
}
```

---

## Usage Examples

### Python

```python
import requests

url = "http://localhost:8001/api/extract-acord"

with open("acord_form.pdf", "rb") as f:
    response = requests.post(url, files={"file": f})

data = response.json()

if data["success"]:
    formatted = data["formatted_data"]
    print(f"Certificate Holder: {formatted['information']['certificate_holder']}")
    print(f"GL Policy: {formatted['general_liability']['policy_information']['policy_number']}")
else:
    print(f"Error: {data['error']}")
```

### cURL

```bash
curl -X POST "http://localhost:8001/api/extract-acord" \
  -F "file=@acord_form.pdf"
```

---

## Project Structure

```
acord-dummy-repo/
├── .env                           # API keys (not in version control)
├── Pipfile                        # Python dependencies
├── requirements.txt               # Alternative dependency file
├── acord_data_structure/
│   └── acord_field_mappings.json  # PDF field → schema mappings
├── app/
│   ├── app.py                     # FastAPI application entry
│   ├── config.py                  # Configuration loader
│   ├── core/
│   │   └── utils.py               # File utilities
│   ├── routes/
│   │   └── extraction.py          # API endpoints
│   └── services/
│       ├── pypdf_extractor.py     # PDF form extraction
│       ├── acord/
│       │   ├── acord_detector.py  # Form detection
│       │   ├── acord_formatter.py # Output formatting
│       │   ├── acord_organizer.py # OpenAI organization
│       │   └── acord_pipeline.py  # Main pipeline
│       └── ai/
│           └── openai_service.py  # OpenAI API client
├── output/                        # Saved extraction JSON files
└── uploads/                       # Temporary upload storage
```

---

## Security Notes

- Store API keys in `.env` only
- Do not commit `.env` to version control
- Use separate keys for development and production
- Configure CORS origins in `app/config.py` for production

---

## Troubleshooting

| Issue               | Solution                                               |
| ------------------- | ------------------------------------------------------ |
| Port already in use | Change port in `app/app.py` (default: 8001)            |
| OpenAI API error    | Verify API key and model access                        |
| Empty extraction    | Ensure PDF is fillable (not scanned)                   |
| Missing fields      | Check `acord_field_mappings.json` for mapping coverage |
