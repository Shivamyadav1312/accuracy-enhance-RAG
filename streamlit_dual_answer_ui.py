"""
Enhanced Streamlit UI with Dual Answers
Shows both document-specific and generalized answers side-by-side
"""

import streamlit as st
import requests
import hashlib
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Dual Answer RAG System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        padding: 1rem 0;
    }
    .answer-box {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: #000000;
        line-height: 1.6;
        font-size: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .document-answer {
        border-left: 4px solid #4CAF50;
    }
    .general-answer {
        border-left: 4px solid #2196F3;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin: 1rem 0;
    }
    .doc-header {
        color: #4CAF50;
    }
    .gen-header {
        color: #2196F3;
    }
</style>
""", unsafe_allow_html=True)

def generate_user_id():
    """Generate unique user ID"""
    if 'user_id' not in st.session_state:
        try:
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            ctx = get_script_run_ctx()
            session_id = ctx.session_id if ctx else f"user_{hash(datetime.now())}"
        except:
            import random
            session_id = f"user_{random.randint(100000, 999999)}"
        st.session_state.user_id = hashlib.md5(str(session_id).encode()).hexdigest()[:12]
    return st.session_state.user_id

def upload_document(file, user_id, domain="travel"):
    """Upload document to server"""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        data = {"domain": domain, "user_id": user_id}
        
        response = requests.post(
            f"{API_BASE_URL}/upload",
            files=files,
            data=data,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Upload failed: {response.text}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def query_dual_answers(query, user_id, domain=None, top_k=5, include_web=False, llm_provider="together"):
    """Query with dual answers"""
    payload = {
        "query": query,
        "domain": domain,
        "detect_intent": True,
        "detect_domain": True,
        "include_web": include_web,
        "top_k": top_k,
        "user_id": user_id,
        "llm_provider": llm_provider,
        "include_reports": True
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
    except Exception as e:
        return None, str(e)

def main():
    user_id = generate_user_id()
    
    # Header
    st.markdown('<div class="main-header">🎯 Dual Answer RAG System</div>', unsafe_allow_html=True)
    st.markdown("**Get answers from both your documents AND general knowledge**")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # User ID
        st.subheader("👤 User Identity")
        user_id_option = st.radio(
            "Select User ID:",
            ["Auto (Session)", "Custom ID"]
        )
        
        if user_id_option == "Custom ID":
            custom_user_id = st.text_input("Enter User ID:", value="analyst_001")
            if custom_user_id:
                user_id = custom_user_id
        
        st.info(f"🆔 Current ID: `{user_id[:16]}...`")
        st.markdown("---")
        
        # Upload Section
        st.subheader("📤 Upload Documents")
        uploaded_file = st.file_uploader(
            "Choose file",
            type=['pdf', 'docx', 'txt', 'png', 'jpg'],
            help="Upload your documents for analysis"
        )
        
        if uploaded_file:
            domain_choice = st.selectbox("Domain:", ["travel", "real_estate"])
            if st.button("⬆️ Upload", type="primary"):
                with st.spinner("Uploading..."):
                    result, error = upload_document(uploaded_file, user_id, domain_choice)
                    if error:
                        st.error(f"❌ {error}")
                    else:
                        st.success(f"✅ Uploaded: {uploaded_file.name}")
                        st.json(result)
        
        st.markdown("---")
        
        # Query Settings
        st.subheader("🔍 Query Options")
        
        top_k = st.slider("Sources to retrieve:", 1, 10, 5)
        include_web = st.checkbox("🌐 Include Web Search", value=False)
        
        llm_provider = st.radio(
            "AI Model:",
            ["Together AI (Detailed)", "Groq (Fast)"],
            index=0
        )
        selected_provider = "together" if "Together" in llm_provider else "groq"
        
        st.markdown("---")
        
        # Example Queries
        st.subheader("💡 Example Queries")
        examples = [
            "What are the key insights in my documents?",
            "Compare Paris and London for tourism",
            "What is mentioned about hotels?",
            "Summarize the main themes",
            "What are current travel trends?"
        ]
        selected_example = st.selectbox("Choose example:", [""] + examples)
    
    # Main Content
    st.subheader("🔍 Ask Your Question")
    
    query_input = st.text_area(
        "Enter your question:",
        value=selected_example if selected_example else "",
        height=100,
        placeholder="e.g., What are the similarities between my uploaded reports?"
    )
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        submit_button = st.button("🚀 Get Dual Answers", type="primary", use_container_width=True)
    with col2:
        if st.button("🔄 Clear", use_container_width=True):
            st.rerun()
    
    # Process Query
    if submit_button and query_input.strip():
        with st.spinner("🔄 Generating dual answers..."):
            result, error = query_dual_answers(
                query_input, user_id, None, top_k, include_web, selected_provider
            )
            
            if error:
                st.error(f"❌ {error}")
            elif result:
                # Display Results
                st.markdown("---")
                
                # Stats Row
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Domain", result.get('domain', 'N/A').replace('_', ' ').title())
                with col2:
                    st.metric("Intent", result.get('intent', 'N/A').replace('_', ' ').title())
                with col3:
                    st.metric("User Docs", result.get('user_documents_found', 0))
                with col4:
                    st.metric("Time", f"{result.get('processing_time', 0):.2f}s")
                
                st.markdown("---")
                
                # Dual Answers Side by Side
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.markdown('<div class="section-header doc-header">📄 From Your Documents</div>', unsafe_allow_html=True)
                    
                    if result.get('has_user_documents'):
                        doc_answer = result.get('document_answer', 'No answer generated')
                        st.markdown(f'<div class="answer-box document-answer">{doc_answer.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
                        
                        # Show sources
                        with st.expander("📚 Your Document Sources", expanded=False):
                            user_sources = result.get('user_sources', [])
                            if user_sources:
                                for i, source in enumerate(user_sources, 1):
                                    st.markdown(f"**Source {i}:** {source.get('source', 'Unknown')}")
                                    st.caption(source.get('text', '')[:200] + "...")
                                    st.markdown(f"*Score: {source.get('score', 0):.3f}*")
                                    st.markdown("---")
                            else:
                                st.info("No sources found")
                    else:
                        st.info("📭 No documents uploaded yet. Upload documents to get personalized answers!")
                
                with col_right:
                    st.markdown('<div class="section-header gen-header">🌍 General Knowledge</div>', unsafe_allow_html=True)
                    
                    general_answer = result.get('general_answer', 'No answer generated')
                    st.markdown(f'<div class="answer-box general-answer">{general_answer.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
                    
                    # Show sources
                    with st.expander("📚 General Knowledge Sources", expanded=False):
                        general_sources = result.get('general_sources', [])
                        if general_sources:
                            for i, source in enumerate(general_sources, 1):
                                st.markdown(f"**Source {i}:** {source.get('source', 'Unknown')}")
                                st.caption(source.get('text', '')[:200] + "...")
                                st.markdown(f"*Score: {source.get('score', 0):.3f}*")
                                st.markdown("---")
                        else:
                            st.info("No sources found")
                
                # Web Results (if any)
                if result.get('web_results'):
                    st.markdown("---")
                    st.markdown("### 🌐 Web Search Results")
                    for i, web in enumerate(result['web_results'], 1):
                        st.markdown(f"**{i}. {web.get('title', 'N/A')}**")
                        st.markdown(web.get('snippet', ''))
                        st.markdown(f"🔗 [{web.get('url', 'N/A')}]({web.get('url', '#')})")
                        st.markdown("---")
                
                # Comparison Section
                st.markdown("---")
                st.markdown("### 🔍 Quick Comparison")
                
                comp_col1, comp_col2 = st.columns(2)
                with comp_col1:
                    st.markdown("**📄 Your Documents:**")
                    if result.get('has_user_documents'):
                        st.success(f"✅ Found {result.get('user_documents_found', 0)} relevant chunks")
                        st.caption("Personalized to your uploaded content")
                    else:
                        st.warning("⚠️ No documents uploaded")
                        st.caption("Upload documents for personalized answers")
                
                with comp_col2:
                    st.markdown("**🌍 General Knowledge:**")
                    st.success(f"✅ Found {result.get('general_sources_found', 0)} relevant chunks")
                    st.caption("From comprehensive knowledge base + web")
    
    elif submit_button:
        st.warning("⚠️ Please enter a question")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p><strong>Dual Answer RAG System</strong> | Get insights from both your documents and general knowledge</p>
        <p>📄 Your Documents + 🌍 General Knowledge + 🌐 Web Search</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
