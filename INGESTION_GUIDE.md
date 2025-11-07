# 📚 Document Ingestion Guide

## Quick Start - Ingest Downloaded Documents

### Step 1: Verify Documents are Downloaded
```bash
# Check if documents exist
ls downloaded_docs/travel/
ls downloaded_docs/real_estate/
```

**Expected:**
- Travel: 86 documents (83 city guides + 3 OpenFlights datasets)
- Real Estate: 13 documents (4 Zillow + 7 FRED + 2 Realtor.com)

---

### Step 2: Run Ingestion Script

**Preview what will be ingested (dry run):**
```bash
python domain_document_collector.py --dry-run
```

**Ingest all documents into Pinecone:**
```bash
python domain_document_collector.py
```

**What happens:**
1. ✅ Scans `downloaded_docs/` folder
2. ✅ Shows breakdown by domain
3. ✅ Asks for confirmation
4. ✅ Ingests each document with progress bar
5. ✅ Creates vector embeddings in Pinecone
6. ✅ Shows success/failure statistics

---

### Step 3: Verify Ingestion

**Check Pinecone data:**
```bash
python check_pinecone_data.py
```

**Test with queries:**
```bash
python interactive_query.py
```

**Example queries to test:**
- "What are the top attractions in Paris?"
- "What is the current mortgage rate trend?"
- "Compare home prices in New York vs Los Angeles"
- "Tell me about flight routes from Singapore"

---

## 📊 What Gets Ingested

### Travel Documents (86)

#### Destinations (83 city guides)
- **Source:** Wikivoyage
- **Content:** City descriptions, attractions, culture, transportation
- **Cities:** Paris, London, Dubai, Singapore, New York, Tokyo, Barcelona, Amsterdam, Rome, Istanbul, Seoul, Milan, Bangkok, Hong Kong, Las Vegas, Prague, Madrid, Vienna, Los Angeles, Berlin, Venice, Florence, Sydney, Lisbon, Orlando, Miami, Munich, Dublin, Copenhagen, Athens, Brussels, San Francisco, Budapest, Zurich, Hamburg, Warsaw, Krakow, Stockholm, Nice, Toronto, Edinburgh, Seville, Marrakech, Cairo, Mumbai, Delhi, Jaipur, Agra, Bangalore, Hyderabad, Chennai, Kolkata, Shanghai, Beijing, Taipei, Kuala Lumpur, Jakarta, Manila, Hanoi, Ho Chi Minh City, Phuket, Bali, Melbourne, Brisbane, Auckland, Wellington, Vancouver, Montreal, Mexico City, Cancun, Buenos Aires, Rio de Janeiro, São Paulo, Lima, Santiago, Bogota, Quito, Cusco, Havana, San Juan, Nassau, Montego Bay

#### Transportation (3 datasets)
- **openflights_airports.txt:** 7,698 airports worldwide
- **openflights_airlines.txt:** 6,162 airlines
- **openflights_routes.txt:** 67,663 flight routes

### Real Estate Documents (13)

#### Price Prediction (4 Zillow datasets)
- **zillow_home_values.txt:** Metro-level home values (ZHVI)
- **zillow_rental_index.txt:** Rental price trends (ZORI)
- **zillow_inventory.txt:** Housing inventory data
- **zillow_median_sale_price.txt:** Median sale prices

#### Economic Factors (7 FRED indicators)
- **fred_MORTGAGE30US.txt:** 30-Year Fixed Rate Mortgage Average
- **fred_CSUSHPISA.txt:** S&P/Case-Shiller U.S. National Home Price Index
- **fred_HOUST.txt:** Housing Starts
- **fred_GDP.txt:** Gross Domestic Product
- **fred_UNRATE.txt:** Unemployment Rate
- **fred_CPIAUCSL.txt:** Consumer Price Index
- **fred_FEDFUNDS.txt:** Federal Funds Effective Rate

#### Market Intelligence (2 Realtor.com datasets)
- **realtor_inventory_core.txt:** Core market metrics
- **realtor_inventory_hotness.txt:** Market hotness indicators

---

## 🔧 Advanced Usage

### Ingest Specific Domain Only

**Travel only:**
```bash
python bulk_ingest_documents.py --folder downloaded_docs/travel --domain travel
```

**Real Estate only:**
```bash
python bulk_ingest_documents.py --folder downloaded_docs/real_estate --domain real_estate
```

### Add User-Specific Documents

**Tag documents for specific user:**
```bash
python bulk_ingest_documents.py --root downloaded_docs --user-id user123
```

---

## 📈 Expected Results

### Ingestion Stats
```
Total Files Processed: 99
✅ Successful: 99
❌ Failed: 0
📦 Total Chunks Created: ~500-1000 (depends on document size)
⏱️  Duration: ~5-10 minutes
```

### Pinecone Index Stats
```
Travel namespace: ~86 documents, ~400-600 chunks
Real Estate namespace: ~13 documents, ~100-200 chunks
```

---

## 🚨 Troubleshooting

### Issue: "No documents found"
**Solution:** Run `python auto_document_downloader.py` first

### Issue: "Pinecone API key not found"
**Solution:** Check `.env` file has `PINECONE_API_KEY=your_key`

### Issue: "Import error: app2"
**Solution:** Make sure `app2.py` exists in the same directory

### Issue: "Failed to ingest document"
**Check:**
1. Document file is not corrupted
2. File encoding is UTF-8 or Latin-1
3. Pinecone index exists and is accessible

---

## 📝 Logs

**Ingestion log:** `domain_ingestion.log`
**Error log:** `domain_ingestion_errors_TIMESTAMP.txt` (if errors occur)

---

## 🎯 Next Steps After Ingestion

1. **Test the system:**
   ```bash
   python interactive_query.py
   ```

2. **Check data quality:**
   ```bash
   python check_pinecone_data.py
   ```

3. **Launch UI:**
   ```bash
   streamlit run streamlit_ui_with_upload.py
   ```

4. **Add more documents:**
   - Download more sources
   - Place in `downloaded_docs/travel/` or `downloaded_docs/real_estate/`
   - Run ingestion again

---

## 💡 Tips

1. **Start small:** Test with 10-20 documents first
2. **Monitor quality:** Check LLM responses before scaling
3. **Organize well:** Keep documents in proper domain folders
4. **Update regularly:** Re-run ingestion when adding new documents
5. **Clean up:** Remove duplicate or low-quality documents

---

## 📊 Coverage Status

**Current:** 99 documents (~5% of 2k target)

**To reach 500 docs:**
- Add 200 more travel guides
- Add 200 more real estate reports
- Focus on: hotels, visas, international markets

**To reach 2000 docs:**
- Expand to all major cities (500+)
- Add historical data (10+ years)
- Include regional reports
- Add cultural/visa guides
