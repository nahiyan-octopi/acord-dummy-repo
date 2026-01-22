# ACORD Data Extractor API

A production-ready API for extracting structured data from ACORD 25 Certificate of Liability Insurance PDFs using Groq (Llama 3.3-70B).

---

## Overview

This API processes fillable ACORD PDF forms and extracts insurance certificate data into a standardized JSON format. The extraction pipeline uses:

1. **PyPDF** - Extracts raw form fields with 100% accuracy from fillable PDFs
2. **Groq (Llama 3.3-70B)** - Organizes and maps extracted fields to a standardized schema
3. **Field Mappings** - Uses explicit ACORD field mappings for consistent results

### Supported Form Types

| Form | Description |
|------|-------------|
| ACORD 25 | Certificate of Liability Insurance |

### Model Performance

This API uses **Groq (Llama 3.3-70B)** for intelligent field organization. Performance characteristics:

| Metric | Value |
|--------|-------|
| **Model** | llama-3.3-70b-versatile |
| **Average Response Time** | 1-2 seconds |
| **Token Usage** | ~2,000-3,000 tokens per extraction |
| **Field Mapping Accuracy** | 95%+ (with explicit mappings) |
| **Temperature** | 0 (deterministic output) |

**Why Groq?**

- **Ultra-fast inference** - Powered by LPU™ (Language Processing Unit) for blazing speed
- **Superior instruction following** - Accurately maps complex ACORD field names to schema
- **JSON mode support** - Guarantees valid JSON output
- **Large context window** - Handles PDFs with 100+ form fields
- **Consistent results** - Temperature 0 ensures reproducible extractions

---

## Quick Start

### Prerequisites

- Python 3.10+
- Groq API key
- pipenv (recommended) or pip

### Installation

```bash
# Clone and navigate to project
cd Acord_Final

# Install dependencies
pipenv install

# Or with pip
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
# Required
GROQ_API_KEY=your-api-key-here

### Running the Server

```bash
# Start the API server
pipenv run python -m backend.app

# Or with uvicorn directly
pipenv run uvicorn backend.app:app --host 0.0.0.0 --port 8001
```

The API will be available at `http://localhost:8001`

---

## API Reference

### Base URL

```
http://localhost:8001
```

### Endpoints

#### Health Check

```http
GET /health
```

Returns API status and configuration.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model": "llama-3.3-70b-versatile"
}
```

---

#### Extract ACORD Data

```http
POST /api/extract-acord
Content-Type: multipart/form-data
```

Extracts and organizes data from an ACORD PDF form.

**Request:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | PDF file (ACORD 25 fillable form) |

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
        "each_occurrence": "$1,000,000",
        "general_aggregate": "$2,000,000"
      }
    },
    "automobile_liability": { ... },
    "umbrella_liability": { ... },
    "workers_comp": { ... },
    "other_data": {
      "insured": { "name": "...", "address": "..." },
      "producer": { "name": "...", "phone": "...", "email": "..." },
      "certificate_holder": { "name": "...", "address": "..." }
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
  "error": "PDF is not a fillable form. Use OCR/AI extraction instead.",
  "file_info": { ... }
}
```

---

#### Detect ACORD Form

```http
POST /api/detect-acord
Content-Type: multipart/form-data
```

Checks if a PDF is a fillable ACORD form without performing full extraction.

**Request:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | PDF file to analyze |

**Response:**

```json
{
  "is_fillable": true,
  "is_acord": true,
  "field_count": 130,
  "confidence": "high",
  "detected_form_type": "ACORD 25 - Certificate of Liability Insurance",
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

### Postman

1. Create a new **POST** request to `http://localhost:8001/api/extract-acord`
2. Go to **Body** → **form-data**
3. Add key `file` with type **File**
4. Select your ACORD PDF
5. Click **Send**

---

## Project Structure

```
Acord_Final/
├── .env                           # API keys (not in version control)
├── .gitignore                     # Excludes sensitive files
├── Pipfile                        # Python dependencies
├── requirements.txt               # Alternative dependency file
├── acord_data_structure/
│   └── acord_field_mappings.json  # PDF field → schema mappings
├── backend/
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
│       │   ├── acord_organizer.py # GPT-4 organization
│       │   └── acord_pipeline.py  # Main pipeline
│       └── ai/
│           └── groq_service.py    # Groq API client
├── output/                        # Saved extraction JSON files
└── uploads/                       # Temporary upload storage
```

---

## Security Considerations

### API Keys

- Store API keys in `.env` file only
- Never hardcode keys in source code
- Rotate keys periodically
- Use separate keys for development and production

### File Handling

- Uploaded files are automatically cleaned up after processing
- Files are stored temporarily in `uploads/` directory
- Output JSON files are saved to `output/` directory

### Production Deployment

For production environments:

1. Use environment variables instead of `.env` files
2. Enable HTTPS/TLS
3. Configure proper CORS origins in `config.py`
4. Add authentication/authorization as needed
5. Set `FLASK_DEBUG=False`

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port already in use | Change port in `backend/app.py` (default: 8001) |
| Groq API error | Verify API key is valid and has access |
| Empty extraction | Ensure PDF is a fillable form (not scanned) |
| Missing fields | Check `acord_field_mappings.json` for mapping coverage |

---

## License

Proprietary - Internal Use Only
