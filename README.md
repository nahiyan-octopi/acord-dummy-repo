# ACORD Data Extractor API

A high-performance API for extracting structured data from PDF documents using a hybrid approach: **direct field mapping** for speed and **AI-powered organization** for intelligence. Optimized for ACORD insurance forms with support for universal document types.

---

## ✨ Key Features

| Feature                  | Description                                                       |
| ------------------------ | ----------------------------------------------------------------- |
| ⚡ **Hybrid Extraction** | 85% direct mapping (instant) + 15% AI (intelligent structuring)   |
| 🎯 **Smart Detection**   | Automatically detects ACORD forms vs general documents            |
| 🚀 **Ultra-Fast**        | ~3-5 seconds total (vs 10-12s traditional AI-only)                |
| 🧠 **AI-Powered**        | GPT-4o/GPT-4o-mini for unformatted data organization              |
| 🧬 **Vectorization API** | Vectorize uploaded PDFs into chunk embeddings + vectorize queries |
| 📊 **Structured Output** | Clean, tabbed JSON ready for UI consumption                       |
| 💰 **Cost-Efficient**    | 70% fewer tokens vs full AI extraction                            |

---

## 🏗️ Hybrid Architecture

```
PDF Upload
    ↓
┌─── Smart Detection ──────────────────────────┐
│  Is this a fillable ACORD form?              │
└───────────────────────────────────────────────┘
    ↓                           ↓
  YES (ACORD)                NO (Universal)
    ↓                           ↓
┌──────────────────────┐     ┌─────────────────────────┐
│ HYBRID PIPELINE      │     │ UNIVERSAL PIPELINE      │
│ ⏱️ ~3-5 seconds      │     │ • PyPDF + OCR           │
│                      │     │ • AI organize all       │
│ 1. PyPDF Extract     │     └─────────────────────────┘
│ 2. Direct Map (85%)  │              ↓
│    → Coverage data   │         JSON Response
│ 3. AI Organize (15%) │
│    → Contacts, etc.  │
│ 4. Merge & Format    │
└──────────────────────┘
         ↓
    JSON Response
```

### Why Hybrid?

**Traditional AI-Only Approach:**

- Sends all 112 fields to AI
- 10-12 seconds per extraction
- High token usage ($$$)

**Our Hybrid Approach:**

- Direct maps 85 coverage fields (deterministic, instant)
- AI only processes 27 unformatted fields (contacts, insurers)
- 3-5 seconds total
- 70% cost reduction

---

## 📁 Project Structure

```
├── app/
│   ├── app.py                      # FastAPI application entry
│   ├── config/                     # Configuration
│   ├── constants/
│   │   └── acord_field_mappings.json  # Direct mapping rules
│   ├── modules/
│   │   ├── extraction/             # Main extraction controller
│   │   └── universal/              # Universal PDF extractor
│   ├── services/
│   │   ├── acord/
│   │   │   ├── acord_pipeline.py   # Hybrid orchestration
│   │   │   ├── direct_mapper.py    # Direct field mapping
│   │   │   ├── acord_organizer.py  # AI for unformatted data
│   │   │   ├── acord_formatter.py  # Output formatting
│   │   │   └── acord_detector.py   # Form detection
│   │   ├── ai/
│   │   │   └── openai_service.py   # OpenAI GPT integration
│   │   └── pypdf_extractor.py      # PDF form field extraction
│   └── utils/                      # Utilities
├── output/                         # Extracted JSON outputs
├── uploads/                        # Temporary uploads
├── .env.example                    # Environment template
└── requirements.txt                # Dependencies
```

---

## 🚀 Installation

### Prerequisites

- **Python 3.10+**
- **Pipenv** (recommended) or pip
- **OpenAI API Key** (GPT-4o or GPT-4o-mini recommended)

#### For Universal Extraction (OCR):

- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
- [Poppler](https://github.com/oschwartz10612/poppler-windows/releases) (Windows)

### Setup Steps

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd DCN-Ai
   ```

2. **Create environment file**

   ```bash
   cp .env.example .env
   ```

   **Edit `.env` and set:**

   ```env
   OPENAI_API_KEY=your-api-key-here
   OPENAI_MODEL=gpt-4o-mini
   OPENAI_TEMPERATURE=0
   ```

3. **Install dependencies**

   ```bash
   # Using Pipenv (recommended)
   pipenv install

   # Or using pip
   pip install -r requirements.txt
   ```

---

## ▶️ Running the Application

```bash
# Using Pipenv
pipenv run uvicorn app.app:app --reload --port 8001

# Or direct Python
python -m uvicorn app.app:app --reload --port 8001
```

The API will be available at: `http://localhost:8001`

### Interactive Documentation

| Interface      | URL                         |
| -------------- | --------------------------- |
| **Swagger UI** | http://localhost:8001/docs  |
| **ReDoc**      | http://localhost:8001/redoc |

---

## 📡 API Reference

### Base Endpoints

| Method | Endpoint  | Description                |
| ------ | --------- | -------------------------- |
| `GET`  | `/`       | API information and status |
| `GET`  | `/health` | Health check endpoint      |

### Extraction Endpoints

| Method | Endpoint             | Description                                    | Status                     |
| ------ | -------------------- | ---------------------------------------------- | -------------------------- |
| `POST` | `/api/extract-data`  | **Unified extraction** - auto-detects & routes | ✅ Primary                 |
| `POST` | `/api/detect-acord`  | Detect if PDF is fillable ACORD form           | ✅ Active                  |
| `POST` | `/api/extract`       | Legacy endpoint (deprecated)                   | ⚠️ Use `/api/extract-data` |
| `POST` | `/api/extract-acord` | Legacy endpoint (deprecated)                   | ⚠️ Use `/api/extract-data` |

### Vectorization Endpoint

| Method | Endpoint               | Description                                   | Status    |
| ------ | ---------------------- | --------------------------------------------- | --------- |
| `POST` | `/api/vectorize`       | Upload single PDF and return chunk embeddings | ✅ Active |
| `POST` | `/api/vectorize-query` | Vectorize query text for downstream systems   | ✅ Active |

---

## ✅ API Usage (Body Guide)

This section shows exactly what to send in each API request body.

### 1) `GET /`

- Content-Type: none
- Body: none

### 2) `GET /health`

- Content-Type: none
- Body: none

### 3) `POST /api/extract-data`

- Content-Type: `multipart/form-data`
- Body: file upload with key `file` **or** `File`

```bash
curl -X POST "http://localhost:8001/api/extract-data" \
  -F "file=@your-document.pdf"
```

### 4) `POST /api/detect-acord`

- Content-Type: `multipart/form-data`
- Body: file upload with key `file` **or** `File`

```bash
curl -X POST "http://localhost:8001/api/detect-acord" \
  -F "file=@your-document.pdf"
```

### 5) `POST /api/extract` (deprecated)

- Content-Type: `multipart/form-data`
- Body: same as `/api/extract-data`

### 6) `POST /api/extract-acord` (deprecated)

- Content-Type: `multipart/form-data`
- Body: same as `/api/extract-data`

### 7) `POST /api/vectorize`

- Content-Type: `multipart/form-data`
- Body: file upload with key `file`

```bash
curl -X POST "http://localhost:8001/api/vectorize" \
  -F "file=@your-document.pdf"
```

### 8) `POST /api/vectorize-query`

- Content-Type: `application/json`
- Body:

```json
{
  "query": "rezwn"
}
```

---

### `POST /api/extract-data`

**Unified extraction endpoint** - automatically detects ACORD forms and routes to the optimal pipeline.

**Request:**

```bash
curl -X POST "http://localhost:8001/api/extract-data" \
  -F "file=@your-document.pdf"
```

**Request Configuration:**

| Component     | Setting        | Description                     |
| ------------- | -------------- | ------------------------------- |
| **Method**    | `POST`         |                                 |
| **Body Type** | `form-data`    | Select `form-data` in Postman   |
| **Key**       | `file`         | Set type to **File** (not Text) |
| **Value**     | `[Binary PDF]` | Upload your `.pdf` document     |

**Success Response (ACORD):**

```json
{
  "success": true,
  "formatted_data": {
    "information": {
      "certificate_date": "01/15/2026",
      "certificate_number": "00254891",
      "description_of_operations": "..."
    },
    "general_liability": {
      "policy_information": { ... },
      "policy_options": { ... },
      "policy_limits": { ... }
    },
    "automobile_liability": { ... },
    "umbrella_liability": { ... },
    "workers_comp": { ... },
    "other_coverage": { ... },
    "unformatted_data": {
      "insured": { "name": "...", "address": "..." },
      "producer": { "name": "...", "phone": "...", "email": "..." },
      "certificate_holder": { ... },
      "insurers": [ ... ],
      "additional_fields": { ... }
    }
  },
  "document_type": "ACORD Form",
  "extraction_method": "acord_hybrid",
  "tokens_used": {
    "prompt_tokens": 632,
    "completion_tokens": 483,
    "total_tokens": 1115
  },
  "file_info": {
    "filename": "certificate.pdf",
    "file_size": 144652,
    "file_size_kb": 141.26
  }
}
```

**Error Response:**

```json
{
  "success": false,
  "error": "Error description"
}
```

---

### `POST /api/detect-acord`

Detects whether a PDF is a fillable ACORD form without extracting data.

**Request:**

```bash
curl -X POST "http://localhost:8001/api/detect-acord" \
  -F "file=@document.pdf"
```

**Response:**

```json
{
  "is_fillable": true,
  "is_acord": true,
  "confidence": "high",
  "form_type": "ACORD 25"
}
```

---

### `POST /api/vectorize`

Extracts text from an uploaded PDF, applies chunking, and returns chunk-level embeddings.

**Request:**

```bash
curl -X POST "http://localhost:8001/api/vectorize" \
  -F "file=@sample.pdf"
```

**Chunking behavior**

- `chunk_size = 1200`
- `chunk_overlap = 150`
- One output document per chunk with stable fields for downstream storage/search systems.

**Response:**

```json
{
  "success": true,
  "doc_id": "36d3c8f1d6b824f07dff7d2a",
  "embedding_model": "text-embedding-3-small",
  "embedding_dimensions": 1024,
  "chunk_size": 1200,
  "chunk_overlap": 150,
  "total_chunks": 3,
  "embedded_chunks": 3,
  "failed_chunks": 0,
  "file_info": {
    "filename": "sample.pdf",
    "file_size": 210340
  },
  "chunks": [
    {
      "doc_id": "36d3c8f1d6b824f07dff7d2a",
      "chunk_id": "36d3c8f1d6b824f07dff7d2a:0",
      "chunk_index": 0,
      "text": "...",
      "embedding": [0.001, -0.003, "..."],
      "created_at": "2026-02-18T10:30:00+00:00",
      "has_embedding": true,
      "metadata": {
        "filename": "sample.pdf",
        "file_size": 210340,
        "page_count": 3,
        "extraction_method": "pypdf",
        "extraction_strategy": "form_fields_plus_page_text",
        "form_field_count": 128
      }
    }
  ]
}
```

---

### `POST /api/vectorize-query`

Generates a query embedding with the same model and dimensions as `/api/vectorize`.

**Request:**

```json
{
  "query": "Rezwn"
}
```

**Response:**

```json
{
  "success": true,
  "query": "Rezwn",
  "embedding": [0.001, -0.003, "..."],
  "embedding_model": "text-embedding-3-small",
  "embedding_dimensions": 1024,
  "created_at": "2026-02-18T10:35:00+00:00",
  "has_embedding": true,
  "timestamp": "2026-02-18T10:35:00+00:00"
}
```

---

## ⚙️ Configuration

Create a `.env` file with these key variables:

| Variable             | Description              | Recommended                                        |
| -------------------- | ------------------------ | -------------------------------------------------- |
| `OPENAI_API_KEY`     | Your OpenAI API key      | _Required_                                         |
| `OPENAI_MODEL`       | GPT model to use         | `gpt-4o-mini` (fast & cheap) or `gpt-4o` (fastest) |
| `OPENAI_TEMPERATURE` | Model temperature (0-1)  | `0` (deterministic)                                |
| `OPENAI_MAX_TOKENS`  | Maximum response tokens  | `2000`                                             |
| `PDF_DPI`            | OCR resolution           | `300`                                              |
| `MAX_PAGES`          | Maximum pages to process | `50`                                               |

### Model Comparison

| Model           | Speed       | Quality    | Cost | Best For        |
| --------------- | ----------- | ---------- | ---- | --------------- |
| `gpt-4o`        | ⚡⚡⚡ 2-3s | ⭐⭐⭐⭐⭐ | $$$  | Production      |
| `gpt-4o-mini`   | ⚡⚡ 3-5s   | ⭐⭐⭐⭐   | $    | **Recommended** |
| `gpt-3.5-turbo` | 🐌 8-11s    | ⭐⭐⭐     | $$   | Legacy          |

---

## 📊 Performance Metrics

### Hybrid ACORD Extraction

| Metric               | Value              |
| -------------------- | ------------------ |
| **Total Time**       | 3-5 seconds        |
| **Detection**        | ~0.2s              |
| **PyPDF Extraction** | ~0.2s              |
| **Direct Mapping**   | <0.01s (85 fields) |
| **AI Organization**  | ~3-4s (27 fields)  |
| **Format & Merge**   | <0.01s             |
| **Token Usage**      | ~1000-1200 tokens  |

**Improvement over AI-only:** 60-70% faster, 70% fewer tokens

---

## 📋 Supported Document Types

### ACORD Forms (Hybrid Pipeline - Optimized)

- ✅ ACORD 25 - Certificate of Liability Insurance
- ✅ Other fillable ACORD forms with form fields

### Universal Documents (AI Pipeline)

- Resumes / CVs
- Invoices
- Contracts
- Reports
- Any other PDF document

---

## 🔧 How It Works: Hybrid Extraction

### 1. **Detection** (0.2s)

Checks if PDF is a fillable ACORD form using PyPDF

### 2. **PyPDF Extraction** (0.2s)

Extracts all 112 form fields with 100% accuracy

### 3. **Direct Mapping** (<0.01s)

Uses `acord_field_mappings.json` to instantly map:

- General Liability coverage
- Auto Liability coverage
- Umbrella/Excess coverage
- Workers Compensation
- Other coverage
- All policy limits, dates, numbers

**85 fields mapped deterministically - no AI needed!**

### 4. **AI Organization** (3-4s)

AI processes only unmapped fields:

- Insured name & address
- Producer/agent details
- Certificate holder
- Insurer companies (A-F)
- Additional unexpected fields

**Only 27 fields sent to AI - fast & cost-effective!**

### 5. **Merge & Format** (<0.01s)

Combines direct-mapped coverage data with AI-organized contacts into final JSON structure

---

## 🎯 Output Structure

```json
{
  "formatted_data": {
    "information": {
      /* cert date, number, description */
    },
    "general_liability": {
      /* policy info, options, limits */
    },
    "automobile_liability": {
      /* auto coverage details */
    },
    "umbrella_liability": {
      /* umbrella coverage */
    },
    "workers_comp": {
      /* workers comp coverage */
    },
    "other_coverage": {
      /* other policies */
    },
    "unformatted_data": {
      "insured": {
        /* AI-structured */
      },
      "producer": {
        /* AI-structured */
      },
      "certificate_holder": {
        /* AI-structured */
      },
      "insurers": [
        /* AI-structured */
      ],
      "additional_fields": {
        /* Unexpected fields with human-readable labels */
      }
    }
  }
}
```

---

## 📝 License

[Your License Here]

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

---

**Built with ⚡ by the DCN-AI Team**
