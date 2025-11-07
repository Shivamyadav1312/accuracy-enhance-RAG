# Quick Start: CSV Reports Ingestion

## 🚀 3 Simple Steps

### Step 1: Run Ingestion Script
```bash
python ingest_csv_reports.py
```
This will upload 31 industry reports to Pinecone namespace `reports`.

### Step 2: Restart Backend
```bash
python app2.py
```

### Step 3: Start Frontend
```bash
streamlit run streamlit_ui_with_upload.py
```

## ✅ What You Get

- **31 Industry Reports** in Pinecone (separate namespace)
- **Toggle in UI** to enable/disable reports
- **No impact** on existing user documents
- **Flexible querying** - combine user docs + industry reports

## 📊 Reports Included

### Travel (16 reports)
- UNWTO Tourism Highlights & Barometer
- OECD Tourism Trends
- WTTC Economic Impact
- Travel & Tourism Competitiveness Index
- And more...

### Real Estate (15 reports)
- CBRE Global & Regional Outlooks
- JLL Market Reports
- Knight Frank Wealth & House Price Index
- Savills Global Outlook
- And more...

## 🎯 Try These Queries

```
"What are the latest tourism trends from UNWTO?"
"Show me luxury real estate insights from CBRE"
"Compare travel statistics across industry reports"
"What do reports say about market outlook for 2025?"
```

## 🔧 UI Controls

In the sidebar, find:
- **📊 Knowledge Base** section
- **📚 Include Industry Reports Database** checkbox
- Toggle on/off per query

## 📁 Files Created/Modified

✅ `ingest_csv_reports.py` - Ingestion script  
✅ `app2.py` - Backend with multi-namespace support  
✅ `streamlit_ui_with_upload.py` - UI with reports toggle  
✅ `CSV_INGESTION_README.md` - Detailed documentation  

That's it! Your RAG system now has access to 30+ authoritative industry reports! 🎉
