# 🧪 Test Queries for Your RAG System

## Quick Test

Run this to test your ingested data:
```bash
python interactive_query.py
```

---

## 📋 Recommended Test Queries

### Travel Domain Queries (85 documents ingested)

#### City Information
```
What are the top attractions in Paris?
Tell me about things to do in Tokyo
What should I see in Dubai?
Compare London and Paris for tourism
Best places to visit in New York City
```

#### Transportation
```
What airlines fly from Singapore to Tokyo?
Tell me about airports in Europe
How many flight routes are there from London?
What are the major airports in Asia?
Compare air travel options between major cities
```

#### Travel Planning
```
Plan a 3-day itinerary for Barcelona
What's the best way to get around Rome?
Compare Bangkok and Singapore for a vacation
Tell me about cultural attractions in Istanbul
What are budget-friendly destinations in Europe?
```

---

### Real Estate Domain Queries (10 documents ingested)

#### Market Trends
```
What is the current mortgage rate trend?
Show me rental price trends in major metros
How have home prices changed over time?
What's happening in the housing market right now?
Compare rental prices across different cities
```

#### Economic Indicators
```
What economic factors affect housing prices?
How does GDP impact the real estate market?
What is the relationship between unemployment and housing?
Tell me about the Case-Shiller Home Price Index
How do interest rates affect home prices?
```

#### Market Intelligence
```
Which markets are hot right now?
What does inventory data tell us about the market?
Is the housing market cooling down or heating up?
Compare housing inventory across metros
What are the market hotness indicators showing?
```

---

### Cross-Domain Queries

```
Best cities for real estate investment with good tourism
Compare cost of living in major tourist destinations
Which cities have both strong real estate and tourism?
Economic conditions in popular travel destinations
```

---

## 🎯 Expected Results

### What Should Work Well ✅
- **City guides**: Detailed info on 83 major cities
- **Flight data**: Airport and route information
- **Economic data**: 7 FRED indicators with historical trends
- **Rental trends**: Zillow rental index data (2015-2025)
- **Market intelligence**: Realtor.com hotness metrics

### What Might Be Limited ⚠️
- **Hotel information**: Not in current dataset
- **Visa requirements**: Not in current dataset
- **International real estate**: Mostly US-focused data
- **Specific property prices**: Aggregated metro-level only

---

## 📊 Data Coverage Summary

### Travel (85 docs, ~18,000 chunks)
- ✅ 83 city guides (comprehensive)
- ✅ Airport data (7,698 airports)
- ✅ Airline data (6,162 airlines)
- ✅ Route data (67,663 routes)

### Real Estate (10 docs, ~3,300 chunks)
- ✅ Rental trends (695 metros, 2015-2025)
- ✅ Economic indicators (7 metrics, historical)
- ✅ Market intelligence (2 datasets)
- ❌ Home values (pending retry)
- ❌ Inventory (pending retry)
- ❌ Median prices (pending retry)

---

## 🔍 Testing Tips

1. **Start Simple**: Test basic queries first
2. **Check Sources**: Verify LLM cites specific documents
3. **Test Limits**: Ask about data you know isn't there
4. **Compare Responses**: Try similar queries with different wording
5. **Note Gaps**: Document what queries don't work well

---

## 📝 Sample Test Session

```bash
python interactive_query.py
```

**Query 1:** "What are the top attractions in Paris?"
- **Expected:** Eiffel Tower, Louvre, Notre-Dame, etc.
- **Source:** Paris.txt from Wikivoyage

**Query 2:** "What is the current mortgage rate?"
- **Expected:** Historical trend from FRED data
- **Source:** fred_MORTGAGE30US.txt

**Query 3:** "Compare rental prices in New York vs Los Angeles"
- **Expected:** Data from Zillow rental index
- **Source:** zillow_rental_index.txt

**Query 4:** "Which airlines fly from Singapore?"
- **Expected:** List of airlines and routes
- **Source:** openflights_routes.txt

---

## 🚨 If Queries Don't Work

### Check Pinecone Connection
```bash
python check_pinecone_data.py
```

### Verify Document Count
Should show:
- Travel namespace: ~85 documents
- Real Estate namespace: ~10 documents (13 after retry)

### Check Logs
- `domain_ingestion.log` - Ingestion details
- `domain_ingestion_errors_*.txt` - Error details

---

## 🎯 Success Criteria

✅ **Good Response:**
- Cites specific documents
- Provides accurate information
- Matches source data
- Acknowledges limitations

❌ **Poor Response:**
- Generic/hallucinated info
- No source citations
- Contradicts source data
- Claims to have data it doesn't

---

## 📈 Next Steps After Testing

1. **Document gaps** - What queries failed?
2. **Retry failed docs** - Run `retry_failed_ingestion.py`
3. **Add more data** - Focus on identified gaps
4. **Refine queries** - Improve prompt engineering
5. **Scale up** - Add 100-200 more documents
