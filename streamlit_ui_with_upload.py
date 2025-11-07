"""
Enhanced Streamlit Web UI with Document Upload
Allows users to upload their own documents and query them
"""

import streamlit as st
import requests
import json
from datetime import datetime
import hashlib

# Page config
st.set_page_config(
    page_title="Enhanced Travel RAG with Upload",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS (same as before)
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        padding: 1rem 0;
    }
    .intent-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1rem;
        margin: 0.5rem 0;
    }
    .visa-info { background-color: #E3F2FD; color: #1565C0; }
    .hotel-search { background-color: #F3E5F5; color: #6A1B9A; }
    .flight-search { background-color: #E8F5E9; color: #2E7D32; }
    .weather { background-color: #FFF3E0; color: #E65100; }
    .destination-info { background-color: #FCE4EC; color: #C2185B; }
    .travel-tips { background-color: #E0F2F1; color: #00695C; }
    .itinerary { background-color: #FFF9C4; color: #F57F17; }
    
    .upload-section {
        background-color: #f0f8ff;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px dashed #1E88E5;
        margin: 1rem 0;
    }
    .document-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .answer-box {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #1E88E5;
        margin: 1rem 0;
        color: #000000;
        line-height: 1.6;
        font-size: 1rem;
    }
    .document-answer {
        border-left: 4px solid #4CAF50;
        background-color: #f1f8f4;
    }
    .general-answer {
        border-left: 4px solid #2196F3;
        background-color: #f0f7ff;
    }
    .answer-header {
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .doc-header {
        color: #4CAF50;
    }
    .gen-header {
        color: #2196F3;
    }
</style>
""", unsafe_allow_html=True)

def get_intent_badge(intent):
    """Generate HTML badge for intent"""
    intent_class = intent.replace('_', '-') if intent else 'general'
    return f'<span class="intent-badge {intent_class}">{intent.replace("_", " ").title()}</span>'

def generate_user_id():
    """Generate a unique user ID for session"""
    if 'user_id' not in st.session_state:
        # Create a unique ID based on session
        try:
            # Try new Streamlit API
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            ctx = get_script_run_ctx()
            if ctx:
                session_id = ctx.session_id
            else:
                # Fallback to random ID
                import random
                session_id = f"user_{random.randint(100000, 999999)}"
        except:
            # Fallback to random ID
            import random
            session_id = f"user_{random.randint(100000, 999999)}"
        
        st.session_state.user_id = hashlib.md5(str(session_id).encode()).hexdigest()[:12]
    return st.session_state.user_id

def check_server_health():
    """Check if API server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def upload_document(file, user_id, domain="travel"):
    """Upload single document to the server"""
    try:
        # Prepare the file
        files = {
            "file": (file.name, file.getvalue(), file.type)
        }
        
        # Prepare form data (domain and user_id as form fields)
        data = {
            "domain": domain,
            "user_id": user_id
        }
        
        response = requests.post(
            f"{API_BASE_URL}/upload",
            files=files,
            data=data,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json(), None
        else:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get('detail', response.text)
            except:
                pass
            return None, f"Upload failed: {error_detail}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def upload_multiple_documents(files, user_id, domain="travel"):
    """Upload multiple documents to the server using batch upload"""
    try:
        # Prepare multiple files
        files_data = []
        for file in files:
            files_data.append(
                ("files", (file.name, file.getvalue(), file.type))
            )
        
        # Prepare form data
        data = {
            "domain": domain,
            "user_id": user_id
        }
        
        response = requests.post(
            f"{API_BASE_URL}/batch-upload",
            files=files_data,
            data=data,
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json(), None
        else:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get('detail', response.text)
            except:
                pass
            return None, f"Batch upload failed: {error_detail}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def query_api(query, include_web, top_k, user_id=None, llm_provider="together", include_reports=True, domain=None, detect_domain=True):
    """Send query to API with optional user_id filter and LLM provider selection"""
    payload = {
        "query": query,
        "domain": domain,  # None for auto-detect
        "detect_intent": True,
        "detect_domain": detect_domain,  # Auto-detect domain
        "include_web": include_web,
        "top_k": top_k,
        "user_id": user_id,  # Filter by user's documents
        "llm_provider": llm_provider,  # Choose between 'groq' and 'together'
        "include_reports": include_reports  # Include CSV reports from namespace
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Error {response.status_code}: {response.text}"
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to API server. Make sure it's running on port 8000."
    except Exception as e:
        return None, str(e)

def query_dual_api(query, include_web, top_k, user_id=None, llm_provider="together", include_reports=True, domain=None, detect_domain=True):
    """Query with dual answers - document-specific + generalized"""
    payload = {
        "query": query,
        "domain": domain,
        "detect_intent": True,
        "detect_domain": detect_domain,
        "include_web": include_web,
        "top_k": top_k,
        "user_id": user_id,
        "llm_provider": llm_provider,
        "include_reports": include_reports
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/query-dual",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Error {response.status_code}: {response.text}"
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to API server. Make sure it's running on port 8000."
    except Exception as e:
        return None, str(e)

def get_user_documents(user_id):
    """Get list of documents uploaded by user"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/user-documents/{user_id}",
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get('documents', [])
        return []
    except:
        return []

def main():
    # Generate user ID
    user_id = generate_user_id()
    
    # Header
    st.markdown('<div class="main-header">✈️ Enhanced Travel RAG with Personal Documents</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Server status
        server_status = check_server_health()
        if server_status:
            st.success("🟢 API Server: Online")
        else:
            st.error("🔴 API Server: Offline")
            st.info("Start server: `python app2.py`")
        
        st.markdown("---")
        
        # User ID options - Simplified and more flexible
        st.subheader("👤 User Identity")
        user_id_option = st.radio(
            "Select User ID:",
            ["Auto (Session)", "Custom ID"],
            help="Choose how to identify your documents"
        )
        
        if user_id_option == "Custom ID":
            custom_user_id = st.text_input(
                "Enter User ID:", 
                value="travel_analyst_001",
                help="Use this to access previously uploaded documents"
            )
            if custom_user_id:
                user_id = custom_user_id
        
        st.info(f"🆔 Current ID: `{user_id[:16]}...`")
        st.markdown("---")
        
        # Document Upload Section
        st.subheader("📤 Upload Your Documents")
        st.markdown("Upload travel documents (PDF, DOCX, TXT, Images)")
        st.caption("✨ OCR enabled - extracts text from scanned PDFs and images!")
        
        # Multiple file upload
        uploaded_files = st.file_uploader(
            "Choose file(s)",
            type=['pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'],
            help="Upload documents or images - OCR will extract text automatically",
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.info(f"📁 {len(uploaded_files)} file(s) selected")
            
            # Show selected files
            with st.expander("View selected files", expanded=False):
                for file in uploaded_files:
                    st.text(f"• {file.name} ({file.size / 1024:.1f} KB)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if len(uploaded_files) == 1:
                    if st.button("⬆️ Upload Document", type="primary", use_container_width=True):
                        with st.spinner("Uploading and processing..."):
                            result, error = upload_document(uploaded_files[0], user_id)
                            if error:
                                st.error(f"❌ {error}")
                            else:
                                st.success(f"✅ Uploaded: {uploaded_files[0].name}")
                                st.json(result)
                                st.rerun()
            
            with col2:
                if len(uploaded_files) > 1:
                    if st.button(f"⬆️ Upload All ({len(uploaded_files)})", type="primary", use_container_width=True):
                        with st.spinner(f"Uploading {len(uploaded_files)} documents..."):
                            result, error = upload_multiple_documents(uploaded_files, user_id)
                            if error:
                                st.error(f"❌ {error}")
                            else:
                                st.success(f"✅ Uploaded {result.get('successful', 0)} of {result.get('total', 0)} files")
                                st.info(f"Total chunks created: {result.get('total_chunks', 0)}")
                                
                                # Show detailed results
                                with st.expander("Upload details", expanded=True):
                                    for res in result.get('results', []):
                                        if res['status'] == 'success':
                                            st.success(f"✓ {res['file_name']} - {res['chunks_created']} chunks")
                                        else:
                                            st.error(f"✗ {res['file']} - {res.get('error', 'Unknown error')}")
                                
                                st.rerun()
        
        st.markdown("---")
        
        # Show user's documents
        st.subheader("📚 Your Documents")
        user_docs = get_user_documents(user_id)
        
        if user_docs:
            for doc in user_docs:
                st.markdown(f'<div class="document-card">', unsafe_allow_html=True)
                st.markdown(f"**{doc.get('filename', 'Unknown')}**")
                st.caption(f"Chunks: {doc.get('chunks', 0)} | Uploaded: {doc.get('timestamp', 'N/A')}")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No documents uploaded yet")
        
        st.markdown("---")
        
        # Query settings - More flexible
        st.subheader("🔍 Query Options")
        
        # Dual Answer Mode Toggle
        dual_answer_mode = st.checkbox(
            "🎯 Dual Answer Mode",
            value=False,
            help="Get TWO answers: one from your documents + one from general knowledge"
        )
        
        if dual_answer_mode:
            st.success("✅ Dual Answer Mode: You'll get both document-specific AND generalized answers!")
        
        # Search scope - flexible selection
        search_scope = st.radio(
            "Search Scope:",
            ["My Documents Only", "My Documents + General Knowledge", "General Knowledge Only"],
            index=1,
            help="Choose where to search - you can change this anytime!"
        )
        
        # Web search - optional, can be toggled anytime
        include_web = st.checkbox(
            "🌐 Enable Web Search", 
            value=False,
            help="Toggle web search on/off based on your needs"
        )
        
        # Number of sources - this controls the actual number returned
        top_k = st.slider(
            "📊 Number of Sources to Retrieve", 
            min_value=1, 
            max_value=10, 
            value=3,
            help="Exact number of document sources to retrieve and display"
        )
        
        st.markdown("---")
        
        # LLM Provider Selection
        st.subheader("🤖 AI Model Selection")
        llm_provider = st.radio(
            "Choose AI Model:",
            ["Together AI (Detailed)", "Groq (Fast & Current)"],
            index=0,
            help="Together AI: Best for detailed analysis\nGroq: Best for current/real-time information"
        )
        
        # Map selection to provider name
        selected_provider = "together" if "Together" in llm_provider else "groq"
        
        if selected_provider == "groq":
            st.info("⚡ Groq: Fast responses with current information")
        else:
            st.info("🎯 Together AI: Detailed, comprehensive analysis")
        
        st.markdown("---")
        
        # Domain Selection
        st.subheader("🎯 Domain Selection")
        domain_option = st.radio(
            "Select Domain:",
            ["Auto-Detect", "Travel", "Real Estate"],
            index=0,
            help="Auto-detect will automatically determine if your query is about travel or real estate"
        )
        
        # Map selection to domain value
        if domain_option == "Auto-Detect":
            selected_domain = None
            detect_domain = True
            st.info("🤖 AI will automatically detect domain from your query")
        elif domain_option == "Travel":
            selected_domain = "travel"
            detect_domain = False
            st.success("✈️ Travel domain selected")
        else:  # Real Estate
            selected_domain = "real_estate"
            detect_domain = False
            st.success("🏠 Real Estate domain selected")
        
        st.markdown("---")
        
        # Reports Database Toggle
        st.subheader("📊 Knowledge Base")
        include_reports = st.checkbox(
            "📚 Include Industry Reports Database",
            value=True,
            help="Access 30+ travel & real estate industry reports from UNWTO, CBRE, JLL, Knight Frank, etc."
        )
        
        if include_reports:
            st.success("✅ Reports database enabled (30+ industry reports)")
        else:
            st.info("ℹ️ Using only uploaded documents")
        
        st.markdown("---")
        
        # Example queries
        st.subheader("💡 Example Queries")
        example_queries = [
            "What hotels are mentioned in my documents?",
            "What are the prices in my uploaded file?",
            "Summarize my travel documents",
            "What's the weather like in Bangkok?",
            "What is the price of Paris restaurant in 2025?",
            "Compare my documents with general recommendations",
            "Current travel restrictions for Japan"
        ]
        
        selected_example = st.selectbox("Choose an example:", [""] + example_queries)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔍 Ask Your Travel Question")
        
        # Show conversation history
        if 'query_history' in st.session_state and st.session_state.query_history:
            with st.expander("📜 Conversation History", expanded=False):
                for i, hist in enumerate(st.session_state.query_history[-3:], 1):
                    st.markdown(f"**Q{i}:** {hist['query']}")
                    st.caption(f"Intent: {hist.get('intent', 'N/A')} | Scope: {hist.get('scope', 'N/A')}")
                    st.markdown("---")
        
        # Query input
        query_input = st.text_area(
            "Enter your question:",
            value=selected_example if selected_example else "",
            height=100,
            placeholder="e.g., What hotels are near Eiffel Tower in my documents?"
        )
        
        # Submit button
        submit_button = st.button("🚀 Get Answer", type="primary", use_container_width=True)
    
    with col2:
        st.subheader("📊 Quick Stats")
        st.metric("Your Documents", len(user_docs))
        
        # Placeholder for query stats
        stats_placeholder = st.empty()
        
        # Show previous stats if available (before new query)
        if 'last_result' in st.session_state and not submit_button:
            with stats_placeholder.container():
                prev_result = st.session_state.last_result
                st.metric("Intent", prev_result.get('intent', 'N/A').replace('_', ' ').title())
                st.metric("Processing Time", f"{prev_result.get('processing_time', 0):.2f}s")
                st.metric("Sources Found", len(prev_result.get('sources', [])))
    
    # Process query
    if submit_button and query_input.strip():
        # Determine user_id filter based on search scope
        if search_scope == "My Documents Only":
            query_user_id = user_id
            scope_label = "Your Documents"
        elif search_scope == "My Documents + General Knowledge":
            query_user_id = None  # Search all
            scope_label = "All Sources"
        else:  # General Knowledge Only
            query_user_id = "general"  # Special flag for general only
            scope_label = "General Knowledge"
        
        # Show search configuration
        reports_status = "Reports: ON" if include_reports else "Reports: OFF"
        search_config = f"{scope_label} | {top_k} sources | {'Web: ON' if include_web else 'Web: OFF'} | {reports_status} | {llm_provider.split()[0]}"
        
        with st.spinner(f"🔄 Searching: {search_config}..."):
            # Use dual answer API if mode is enabled
            if dual_answer_mode:
                result, error = query_dual_api(query_input, include_web, top_k, user_id, selected_provider, include_reports, selected_domain, detect_domain)
            else:
                result, error = query_api(query_input, include_web, top_k, query_user_id, selected_provider, include_reports, selected_domain, detect_domain)
            
            if error:
                st.error(f"❌ {error}")
            elif result:
                st.session_state.last_result = result
                
                # Update stats in the placeholder immediately
                with stats_placeholder.container():
                    detected_domain_display = result.get('domain', 'N/A').replace('_', ' ').title()
                    st.metric("Domain", detected_domain_display)
                    st.metric("Intent", result.get('intent', 'N/A').replace('_', ' ').title())
                    st.metric("Processing Time", f"{result.get('processing_time', 0):.2f}s")
                    actual_sources = len(result.get('sources', []))
                    st.metric("Sources Retrieved", f"{actual_sources}/{top_k}")
                    if selected_provider == "groq":
                        st.caption("⚡ Groq (Fast)")
                    else:
                        st.caption("🎯 Together AI")
                
                # Save to history
                if 'query_history' not in st.session_state:
                    st.session_state.query_history = []
                
                st.session_state.query_history.append({
                    'query': query_input,
                    'intent': result.get('intent', 'N/A'),
                    'scope': scope_label,
                    'time': datetime.now().strftime("%H:%M:%S")
                })
                
                # Display results in tabs
                tab1, tab2, tab3, tab4 = st.tabs([
                    "💬 Answer", 
                    "🎯 Intent & Sources", 
                    "🌐 Web Results",
                    "📋 Raw JSON"
                ])
                
                # Tab 1: Answer
                with tab1:
                    # Domain and Intent badges
                    detected_domain_display = result.get('domain', 'general').replace('_', ' ').title()
                    domain_emoji = "✈️" if result.get('domain') == 'travel' else "🏠" if result.get('domain') == 'real_estate' else "🎯"
                    st.markdown(f"**{domain_emoji} Domain:** {detected_domain_display}")
                    
                    intent = result.get('intent', 'general')
                    st.markdown(get_intent_badge(intent), unsafe_allow_html=True)
                    
                    # Check if dual answer mode
                    if dual_answer_mode and 'document_answer' in result:
                        # Dual Answer Display
                        st.markdown("### 🎯 Dual Answers")
                        st.caption(f"📊 User Docs: {result.get('user_documents_found', 0)} | General Sources: {result.get('general_sources_found', 0)}")
                        
                        col_left, col_right = st.columns(2)
                        
                        with col_left:
                            st.markdown('<div class="answer-header doc-header">📄 From Your Documents</div>', unsafe_allow_html=True)
                            doc_answer = result.get('document_answer', 'No answer')
                            doc_answer_html = doc_answer.replace('\n', '<br>')
                            st.markdown(f'<div class="answer-box document-answer">{doc_answer_html}</div>', unsafe_allow_html=True)
                            
                            if result.get('has_user_documents'):
                                with st.expander("📚 Your Sources", expanded=False):
                                    user_sources = result.get('user_sources', [])
                                    for i, src in enumerate(user_sources, 1):
                                        st.markdown(f"**{i}. {src.get('source', 'Unknown')}** (score: {src.get('score', 0):.3f})")
                                        st.caption(src.get('text', '')[:150] + "...")
                            else:
                                st.info("📭 No documents uploaded yet")
                        
                        with col_right:
                            st.markdown('<div class="answer-header gen-header">🌍 General Knowledge</div>', unsafe_allow_html=True)
                            gen_answer = result.get('general_answer', 'No answer')
                            gen_answer_html = gen_answer.replace('\n', '<br>')
                            st.markdown(f'<div class="answer-box general-answer">{gen_answer_html}</div>', unsafe_allow_html=True)
                            
                            with st.expander("📚 General Sources", expanded=False):
                                gen_sources = result.get('general_sources', [])
                                for i, src in enumerate(gen_sources, 1):
                                    st.markdown(f"**{i}. {src.get('source', 'Unknown')}** (score: {src.get('score', 0):.3f})")
                                    st.caption(src.get('text', '')[:150] + "...")
                    else:
                        # Single Answer Display
                        st.markdown("### 💬 AI Generated Answer")
                        st.caption(f"🔍 Searched in: {scope_label}")
                        
                        # Answer
                        answer = result.get('answer', 'No answer generated')
                        answer_html = answer.replace('\n', '<br>')
                        st.markdown(f'<div class="answer-box">{answer_html}</div>', unsafe_allow_html=True)
                    
                    # Processing info
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.info(f"⏱️ Time: {result.get('processing_time', 0):.2f}s")
                    with col2:
                        actual_sources = len(result.get('sources', []))
                        st.info(f"📚 Sources: {actual_sources}/{top_k}")
                    with col3:
                        web_count = len(result.get('web_results', [])) if result.get('web_results') else 0
                        st.info(f"🌐 Web: {web_count}")
                    with col4:
                        model_name = "Groq" if selected_provider == "groq" else "Together AI"
                        st.info(f"🤖 {model_name}")
                    
                    st.markdown("---")
                    
                    # Follow-up questions
                    st.markdown("### 💭 Suggested Follow-ups")
                    
                    followup_suggestions = {
                        "hotel_search": [
                            "What are the price ranges mentioned?",
                            "Which hotels have the best reviews?",
                            "Are there family-friendly options?",
                            "What amenities are available?"
                        ],
                        "visa_info": [
                            "What documents are required?",
                            "How long does processing take?",
                            "What are the fees?",
                            "Can I apply online?"
                        ],
                        "destination_info": [
                            "What are the top attractions?",
                            "How many days should I spend?",
                            "What's the best time to visit?",
                            "Are there any hidden gems?"
                        ]
                    }
                    
                    suggestions = followup_suggestions.get(intent, [
                        "Can you provide more details?",
                        "What else is mentioned in my documents?",
                        "Compare with general recommendations",
                        "What are the key highlights?"
                    ])
                    
                    cols = st.columns(2)
                    for i, suggestion in enumerate(suggestions[:4]):
                        with cols[i % 2]:
                            if st.button(suggestion, key=f"followup_{i}"):
                                st.session_state.next_query = suggestion
                                st.rerun()
                
                # Tab 2: Intent & Sources
                with tab2:
                    st.markdown("### 🎯 Detected Intent")
                    st.markdown(get_intent_badge(intent), unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # Sources
                    sources = result.get('sources', [])
                    if sources:
                        st.markdown(f"### 📚 Sources ({len(sources)} found)")
                        
                        # Separate user docs from general
                        user_sources = [s for s in sources if s.get('user_id') == user_id]
                        general_sources = [s for s in sources if s.get('user_id') != user_id]
                        
                        if user_sources:
                            st.markdown("#### 📄 From Your Documents")
                            for i, source in enumerate(user_sources, 1):
                                with st.container():
                                    col1, col2 = st.columns([4, 1])
                                    with col1:
                                        st.markdown(f"**Source {i}**")
                                        st.markdown(source.get('text', '')[:200] + "...")
                                        st.caption(f"📄 {source.get('source', 'Unknown')}")
                                    with col2:
                                        st.metric("Score", f"{source.get('score', 0):.3f}")
                                    st.markdown("---")
                        
                        if general_sources:
                            st.markdown("#### 🌍 From General Knowledge")
                            for i, source in enumerate(general_sources, 1):
                                with st.container():
                                    col1, col2 = st.columns([4, 1])
                                    with col1:
                                        st.markdown(f"**Source {i}**")
                                        st.markdown(source.get('text', '')[:200] + "...")
                                    with col2:
                                        st.metric("Score", f"{source.get('score', 0):.3f}")
                                    st.markdown("---")
                    else:
                        st.warning("No sources found")
                
                # Tab 3: Web Results
                with tab3:
                    web_results = result.get('web_results', [])
                    if web_results:
                        st.markdown(f"### 🌐 Web Search Results ({len(web_results)} found)")
                        for i, web_result in enumerate(web_results, 1):
                            st.markdown(f"**{i}. {web_result.get('title', 'N/A')}**")
                            st.markdown(web_result.get('snippet', ''))
                            st.markdown(f"🔗 [{web_result.get('url', 'N/A')}]({web_result.get('url', '#')})")
                            st.markdown("---")
                    else:
                        st.info("No web results")
                
                # Tab 4: Raw JSON
                with tab4:
                    st.json(result)
    
    elif submit_button:
        st.warning("⚠️ Please enter a question")
    
    # Handle follow-up
    if 'next_query' in st.session_state and st.session_state.next_query:
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>Enhanced Travel RAG with Personal Documents | Flexible Search & Dual AI Models</p>
        <p>📚 Your documents + 5,000 travel queries + 🌐 Live web search</p>
        <p>🤖 Together AI (Detailed Analysis) | ⚡ Groq (Fast & Current Info)</p>
        <p>🎯 <strong>NEW:</strong> Dual Answer Mode - Get answers from YOUR docs + General knowledge!</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
