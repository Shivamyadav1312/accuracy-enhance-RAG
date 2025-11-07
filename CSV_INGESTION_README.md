# CSV Reports Ingestion Guide

## Overview

This guide explains how to ingest industry reports from CSV files into your Pinecone vector database using a separate namespace called `reports`.

## What's Been Added

### 1. **CSV File Structure**
Your CSV file (`travel_real_estate_reports_sources.csv`) contains:
- **31 industry reports** (16 travel + 15 real estate)
- Columns: `domain`, `title`, `url`
- Sources: UNWTO, CBRE, JLL, Knight Frank, Savills, PwC, World Bank, IMF, etc.

### 2. **Ingestion Script** (`ingest_csv_reports.py`)
A standalone script that:
- ✅ Reads CSV file
- ✅ Creates embeddings from report metadata (title + domain + URL)
- ✅ Uploads to Pinecone in `reports` namespace (separate from user documents)
- ✅ Verifies ingestion with test queries
- ✅ Provides detailed logging

### 3. **Backend API Updates** (`app2.py`)
Enhanced to support multi-namespace querying:
- ✅ New parameter: `include_reports` (default: `True`)
- ✅ Queries both default namespace (user docs) and `reports` namespace
- ✅ Merges and ranks results by relevance score
- ✅ Maintains document diversity across namespaces

### 4. **UI Updates** (`streamlit_ui_with_upload.py`)
New toggle in sidebar:
- ✅ "📚 Include Industry Reports Database" checkbox
- ✅ Shows status: "✅ Reports database enabled (30+ industry reports)"
- ✅ Users can enable/disable reports per query

## How to Use

### Step 1: Ingest CSV Reports

Run the ingestion script:

```bash
python ingest_csv_reports.py
```

**Expected Output:**
```
================================================================================
CSV REPORTS INGESTION TO PINECONE
================================================================================
Reading CSV file: travel_real_estate_reports_sources.csv
Found 31 reports to ingest
Domains: ['travel', 'real_estate']

Prepared: [travel] UNWTO International Tourism Highlights 2024
Prepared: [travel] World Tourism Barometer May 2025
...
Prepared: [real_estate] CBRE Luxury Real Estate Report 2024
...

Upserting 31 vectors to Pinecone...
Index: documents-index
Namespace: reports
Upserted batch 1/1

✅ Successfully ingested 31 reports!

Index Statistics:
Total vectors: 1234
Namespaces: {'': {'vector_count': 1203}, 'reports': {'vector_count': 31}}

================================================================================
VERIFICATION TESTS
================================================================================
🔍 Testing retrieval with query: 'luxury real estate market trends'

Found 5 matches:
1. [real_estate] CBRE Luxury Real Estate Report 2024 (score: 0.8234)
2. [real_estate] Knight Frank Wealth Report 2024 (score: 0.7891)
...

================================================================================
✅ INGESTION COMPLETE!
================================================================================
Total reports ingested: 31
Namespace: 'reports'
Index: 'documents-index'
```

### Step 2: Query with Reports

**In Streamlit UI:**
1. Start the app: `streamlit run streamlit_ui_with_upload.py`
2. In sidebar, find "📊 Knowledge Base" section
3. Check "📚 Include Industry Reports Database" (enabled by default)
4. Ask questions like:
   - "What are the latest tourism trends according to UNWTO?"
   - "Show me luxury real estate market insights"
   - "Compare travel statistics from industry reports"

**Via API:**
```python
import requests

payload = {
    "query": "What are the latest tourism trends?",
    "domain": "travel",
    "top_k": 5,
    "include_reports": True,  # Include CSV reports
    "llm_provider": "together"
}

response = requests.post("http://localhost:8000/query", json=payload)
print(response.json()["answer"])
```

## Architecture

### Namespace Strategy

```
Pinecone Index: "documents-index"
├── Default Namespace ("") 
│   ├── User uploaded documents (PDFs, DOCX, TXT)
│   ├── Chunked content with embeddings
│   └── Metadata: user_id, source, domain, chunk_index
│
└── Reports Namespace ("reports")
    ├── CSV industry reports (metadata only)
    ├── Full report metadata as embedding
    └── Metadata: title, url, domain, source_type
```

### Query Flow

```
User Query
    ↓
Generate Embedding
    ↓
Query Default Namespace (top_k results)
    ↓
Query Reports Namespace (top_k/2 results) ← if include_reports=True
    ↓
Merge & Sort by Score
    ↓
Diversify by Source
    ↓
Generate Answer with LLM
```

## Benefits

### 1. **Separation of Concerns**
- User documents in default namespace
- Industry reports in separate namespace
- Easy to manage and update independently

### 2. **Flexible Querying**
- Users can toggle reports on/off
- No interference with personal documents
- Better control over information sources

### 3. **Rich Context**
- Access to 30+ authoritative industry reports
- Combines user data with industry knowledge
- More comprehensive answers

### 4. **Scalability**
- Easy to add more reports (just update CSV and re-run script)
- No need to re-ingest user documents
- Namespace isolation prevents conflicts

## CSV Format

Your CSV should follow this structure:

```csv
domain,title,url
travel,Report Title,https://example.com/report.pdf
real_estate,Another Report,https://example.com/report2.pdf
```

**Fields:**
- `domain`: Category (travel, real_estate, etc.)
- `title`: Full report title
- `url`: Direct link to report (for reference)

## Example Queries

### Travel Reports
```
"What are the latest tourism statistics from UNWTO?"
"Show me adventure tourism trends"
"What does WTTC say about economic impact?"
"Compare tourism policies across regions"
```

### Real Estate Reports
```
"What are luxury real estate trends according to CBRE?"
"Show me global house price indices"
"What are emerging trends in real estate?"
"Compare real estate outlooks from JLL and Knight Frank"
```

### Combined Queries
```
"How do travel trends affect real estate markets?"
"Compare my documents with industry reports"
"What do industry reports say about [topic]?"
```

## Monitoring & Verification

### Check Namespace Stats
```python
from pinecone import Pinecone
import os

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("documents-index")

stats = index.describe_index_stats()
print(f"Total vectors: {stats['total_vector_count']}")
print(f"Namespaces: {stats['namespaces']}")
```

### Test Query
```python
# Query reports namespace directly
results = index.query(
    vector=[0.1] * 384,  # dummy embedding
    top_k=5,
    namespace="reports",
    include_metadata=True
)

for match in results['matches']:
    print(f"{match['metadata']['title']}")
```

## Troubleshooting

### Issue: No reports in results
**Solution:** Check if `include_reports=True` in your query

### Issue: Ingestion failed
**Solution:** 
1. Verify Pinecone API key in `.env`
2. Check CSV file path
3. Ensure CSV has correct columns

### Issue: Reports not showing in UI
**Solution:**
1. Restart backend: `python app2.py`
2. Restart frontend: `streamlit run streamlit_ui_with_upload.py`
3. Check "Include Industry Reports Database" is checked

## Files Modified

1. **`ingest_csv_reports.py`** (NEW)
   - Standalone ingestion script
   - Reads CSV and uploads to Pinecone

2. **`app2.py`**
   - Line 99: Added `include_reports` parameter to QueryRequest
   - Lines 354-398: Updated `retrieve_documents()` for multi-namespace querying
   - Line 782: Pass `include_reports` to retrieval function

3. **`streamlit_ui_with_upload.py`**
   - Lines 182-192: Updated `query_api()` with `include_reports` parameter
   - Lines 388-401: Added "Knowledge Base" section with toggle
   - Line 475: Pass `include_reports` to API call

## Next Steps

1. **Run ingestion:** `python ingest_csv_reports.py`
2. **Restart services:**
   - Backend: `python app2.py`
   - Frontend: `streamlit run streamlit_ui_with_upload.py`
3. **Test queries** with reports enabled/disabled
4. **Add more reports:** Update CSV and re-run ingestion

## Summary

✅ **31 industry reports** ingested into separate namespace  
✅ **Multi-namespace querying** enabled in backend  
✅ **User toggle** added to UI for flexible control  
✅ **No impact** on existing user documents  
✅ **Easy to expand** by adding more reports to CSV  

Your RAG system now has access to authoritative industry reports while maintaining separation from user-uploaded documents! 🚀
