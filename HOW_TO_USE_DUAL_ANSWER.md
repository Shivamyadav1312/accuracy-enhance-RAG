# 🎯 How to Use Dual Answer Mode

## ✅ Feature Added to Existing UI

The dual answer feature has been integrated into your existing `streamlit_ui_with_upload.py` - no need for a separate UI!

## 🚀 Quick Start

### 1. Start the Backend

```bash
python app2.py
```

### 2. Launch the UI

```bash
python -m streamlit run streamlit_ui_with_upload.py
```

Or if streamlit is in your PATH:
```bash
streamlit run streamlit_ui_with_upload.py
```

### 3. Enable Dual Answer Mode

In the sidebar under **"🔍 Query Options"**, check the box:

```
☑️ 🎯 Dual Answer Mode
```

When enabled, you'll see:
> ✅ Dual Answer Mode: You'll get both document-specific AND generalized answers!

## 📊 How It Works

### Normal Mode (Dual Answer OFF)
- Single answer based on your search scope selection
- Traditional RAG behavior

### Dual Answer Mode (Dual Answer ON)
- **Left Panel (Green):** Answer from YOUR uploaded documents
- **Right Panel (Blue):** Answer from general knowledge base
- Both answers shown side-by-side for easy comparison

## 🎨 Visual Layout

When you enable Dual Answer Mode and query:

```
┌─────────────────────────────────────────────────────────┐
│  Domain: Travel | Intent: Destination Info              │
├──────────────────────┬──────────────────────────────────┤
│  📄 From Your Docs   │  🌍 General Knowledge            │
│  (Green background)  │  (Blue background)               │
│                      │                                  │
│  "According to your  │  "Paris is the capital of        │
│  uploaded Paris      │  France with 2.2M population.    │
│  guide..."           │  Top attractions include..."     │
│                      │                                  │
│  [📚 Your Sources]   │  [📚 General Sources]            │
└──────────────────────┴──────────────────────────────────┘
```

## 📝 Example Usage

### Step 1: Upload Documents
1. Go to sidebar → **"📤 Upload Documents"**
2. Choose your PDF/DOCX/TXT files
3. Click **"⬆️ Upload"**
4. Documents are automatically ingested!

### Step 2: Enable Dual Answer
1. In sidebar → **"🔍 Query Options"**
2. Check **"🎯 Dual Answer Mode"**

### Step 3: Ask Questions
Enter your query and click **"🚀 Get Answer"**

**Example Query:**
```
What are the key themes in my documents?
```

**You'll get TWO answers:**

**📄 From Your Documents:**
> "Your uploaded documents focus on three main themes: sustainable tourism practices, digital transformation in travel, and post-pandemic recovery strategies. The Amadeus report specifically mentions..."

**🌍 General Knowledge:**
> "Current travel industry research identifies several key themes including sustainability and eco-tourism, technology integration with AI and contactless services, health and safety protocols, personalized experiences through data analytics..."

## 🎯 Use Cases

### 1. Validate Your Research
**Query:** "Are my findings consistent with industry standards?"
- Left: What YOUR research says
- Right: What industry standards say
- Compare to validate!

### 2. Find Gaps
**Query:** "What information is missing from my report?"
- Left: What's in your report
- Right: What general knowledge adds
- Identify gaps!

### 3. Get Complete Picture
**Query:** "Explain this concept"
- Left: Your specific notes/documents
- Right: Comprehensive expert explanation
- Best of both worlds!

## ⚙️ Settings

### Search Scope (Still Works!)
Even with Dual Answer Mode ON, you can control general knowledge scope:
- **My Documents Only:** Left panel only (right shows general)
- **My Documents + General Knowledge:** Both panels active
- **General Knowledge Only:** Right panel emphasized

### Other Options
- **Web Search:** Adds current info to general answer
- **Top K Sources:** Controls how many chunks to retrieve
- **AI Model:** Choose Together AI or Groq

## 💡 Pro Tips

1. **Upload First:** Add your documents before enabling dual mode
2. **Compare Answers:** Look for differences and similarities
3. **Use for Validation:** Check if your docs align with general knowledge
4. **Find Unique Insights:** See what's unique in your documents
5. **Toggle On/Off:** Switch between modes based on your needs

## 🔧 Troubleshooting

### "No documents uploaded yet" in left panel
**Solution:** Upload documents using the sidebar upload feature

### Both answers look the same
**Solution:** Your documents might be very similar to general knowledge, or try more specific queries

### Slow response
**Solution:** 
- Reduce top_k sources
- Disable web search
- Use Groq instead of Together AI

### Left panel is empty
**Solution:** Make sure you have documents uploaded and dual mode is enabled

## 📊 Technical Details

### What Happens Behind the Scenes

**When Dual Answer Mode is ON:**
1. Query is sent to `/query-dual` endpoint
2. System retrieves from YOUR documents (filtered by user_id)
3. System retrieves from general knowledge base
4. Two separate LLM calls generate two answers
5. Both displayed side-by-side

**When Dual Answer Mode is OFF:**
- Uses traditional `/query` endpoint
- Single answer based on search scope

## 🎉 Summary

✅ **Integrated** into existing UI - no separate app needed  
✅ **Toggle on/off** - use when you need it  
✅ **Side-by-side** comparison for easy analysis  
✅ **Automatic ingestion** - upload and query immediately  
✅ **Source citations** - see where each answer comes from  

## 🚀 Start Using It Now!

```bash
# Terminal 1: Backend
python app2.py

# Terminal 2: UI
python -m streamlit run streamlit_ui_with_upload.py

# In browser:
# 1. Upload documents
# 2. Enable "🎯 Dual Answer Mode"
# 3. Ask questions
# 4. Compare answers!
```

Happy querying! 🎯
