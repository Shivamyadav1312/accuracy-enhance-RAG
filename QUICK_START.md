# 🚀 Quick Start - Ingest Documents into Pinecone

## ⚡ One Command to Rule Them All

```bash
python domain_document_collector.py
```

**That's it!** This will:
1. ✅ Scan 99 downloaded documents
2. ✅ Show you what will be ingested
3. ✅ Ask for confirmation
4. ✅ Ingest into Pinecone with progress bar
5. ✅ Show success statistics

---

## 📋 What Gets Ingested

- **86 Travel documents** (city guides + transportation data)
- **13 Real Estate documents** (Zillow + FRED + Realtor.com)
- **Total: 99 documents** → ~500-1000 searchable chunks

---

## ⏱️ Time Required

- **Scanning:** 5 seconds
- **Ingestion:** 5-10 minutes
- **Total:** ~10 minutes

---

## ✅ After Ingestion

### Test Queries
```bash
python interactive_query.py
```

**Try these:**
- "What are the top attractions in Paris?"
- "What is the current mortgage rate?"
- "Compare home prices in New York vs Los Angeles"
- "Tell me about flights from Tokyo to Singapore"

### Check Data
```bash
python check_pinecone_data.py
```

### Launch UI
```bash
streamlit run streamlit_ui_with_upload.py
```

---

## 🚨 If Something Goes Wrong

### No documents found?
```bash
# Download documents first
python auto_document_downloader.py
```

### Pinecone error?
```bash
# Check .env file has:
PINECONE_API_KEY=your_key_here
```

### Import error?
```bash
# Install dependencies
pip install -r requirements.txt
```

---

## 📊 Expected Output

```
🚀 DOMAIN DOCUMENT COLLECTOR
============================================================
Ingesting documents downloaded by auto_document_downloader.py
Source: ./downloaded_docs
============================================================

🔍 Scanning for documents...
📁 Found 99 documents

Documents by domain:
  ✈️  Travel: 86 files
  🏠 Real Estate: 13 files

📂 Travel Documents:
  - destinations: 83 files
  - transportation: 3 files

📂 Real Estate Documents:
  - price_prediction: 4 files
  - economic_factors: 7 files
  - market_intelligence: 2 files

============================================================
Proceed with ingestion of 99 documents into Pinecone? (yes/no): yes

🚀 Starting ingestion...

Ingesting: 100%|████████████████████████| 99/99 [05:23<00:00,  3.27s/doc]

============================================================
📊 DOMAIN DOCUMENT INGESTION SUMMARY
============================================================
Total Files Processed: 99
✅ Successful: 99
❌ Failed: 0
📦 Total Chunks Created: 847
⏱️  Duration: 323.45 seconds
⚡ Average: 3.27 sec/file

By Domain:
  🏠 Real Estate: 13 documents
  ✈️  Travel: 86 documents
============================================================

✅ INGESTION COMPLETE!
============================================================

📊 Your Pinecone vector database now contains:
  - 86 Travel documents
  - 13 Real Estate documents
  - Total: 99 documents with 847 chunks

🎯 Next Steps:
  1. Test queries: python interactive_query.py
  2. Check Pinecone data: python check_pinecone_data.py
  3. Start UI: streamlit run streamlit_ui_with_upload.py
============================================================
```

---

## 🎯 What You Can Ask After Ingestion

### Travel Queries
- "Best places to visit in Paris"
- "How to get from London to Paris"
- "What airlines fly from Singapore to Tokyo?"
- "Tell me about Dubai attractions"
- "Compare Bangkok and Hong Kong for tourism"

### Real Estate Queries
- "What is the current mortgage rate?"
- "Show me home price trends in New York"
- "Compare rental prices across major metros"
- "What economic factors affect housing prices?"
- "Is the housing market hot or cold right now?"

### Mixed Queries
- "Best cities to invest in real estate"
- "Travel destinations with affordable housing"
- "Economic conditions in major tourist cities"

---

## 📈 Next Steps After Testing

1. **Add more documents** (to reach 500+)
2. **Expand coverage** (hotels, visas, international markets)
3. **Test with real users**
4. **Monitor query quality**
5. **Scale to 2000+ documents**

---

## 💡 Pro Tips

- Start with `--dry-run` to preview: `python domain_document_collector.py --dry-run`
- Check logs: `domain_ingestion.log`
- Monitor Pinecone dashboard for vector count
- Test queries immediately after ingestion
- Add documents incrementally (100-200 at a time)

---

**Ready?** Run this now:
```bash
python domain_document_collector.py
```
