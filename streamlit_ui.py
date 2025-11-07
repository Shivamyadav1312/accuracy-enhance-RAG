"""
Streamlit Web UI for Enhanced RAG System
Simple, beautiful interface to interact with the travel RAG API
"""

import streamlit as st
import requests
import json
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Enhanced Travel RAG",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
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
    
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1E88E5;
        margin: 0.5rem 0;
    }
    .source-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .web-result-card {
        background-color: #f1f8ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #0366d6;
        margin: 0.5rem 0;
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
</style>
""", unsafe_allow_html=True)

def get_intent_badge(intent):
    """Generate HTML badge for intent"""
    intent_class = intent.replace('_', '-') if intent else 'general'
    return f'<span class="intent-badge {intent_class}">{intent.replace("_", " ").title()}</span>'

def check_server_health():
    """Check if API server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def query_api(query, include_web, top_k):
    """Send query to API"""
    payload = {
        "query": query,
        "domain": "travel",
        "detect_intent": True,
        "include_web": include_web,
        "top_k": top_k
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

def main():
    # Header
    st.markdown('<div class="main-header">✈️ Enhanced Travel RAG System</div>', unsafe_allow_html=True)
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
            st.info("Start server: `python enhanced_rag_with_queries.py`")
        
        st.markdown("---")
        
        # Query settings
        st.subheader("Query Options")
        include_web = st.checkbox("🌐 Enable Web Search", value=True, 
                                  help="Search the web for current information")
        top_k = st.slider("📊 Number of Sources", min_value=1, max_value=10, value=5,
                         help="Number of relevant sources to retrieve")
        
        st.markdown("---")
        
        # Example queries
        st.subheader("💡 Example Queries")
        example_queries = [
            "What's the weather like in Bangkok in July?",
            "How do I apply for a visa to Dubai?",
            "Best family hotels in Paris near Eiffel Tower",
            "Cheap flights from London to New York",
            "What are the top attractions in Tokyo?",
            "Travel tips for visiting Thailand",
            "Create a 3-day itinerary for Rome"
        ]
        
        selected_example = st.selectbox("Choose an example:", [""] + example_queries)
        
        st.markdown("---")
        
        # About
        with st.expander("ℹ️ About"):
            st.write("""
            **Enhanced Travel RAG System**
            
            Features:
            - 🎯 Intent Detection
            - 🔗 Similar Query Matching
            - 📚 Knowledge Base Search
            - 🌐 Web Search Integration
            - 🤖 AI-Powered Answers
            
            Dataset: 5,000 travel queries
            Intents: 7 categories
            """)
    
    # Handle follow-up query
    if 'followup_query' in st.session_state and st.session_state.followup_query:
        query_to_use = st.session_state.followup_query
        st.session_state.followup_query = None  # Clear after use
    elif selected_example:
        query_to_use = selected_example
    else:
        query_to_use = ""
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔍 Ask Your Travel Question")
        
        # Show conversation history if exists
        if 'query_history' in st.session_state and st.session_state.query_history:
            with st.expander("📜 Conversation History", expanded=False):
                for i, hist in enumerate(st.session_state.query_history[-3:], 1):  # Show last 3
                    st.markdown(f"**Q{i}:** {hist['query']}")
                    st.caption(f"Intent: {hist.get('intent', 'N/A')} | Time: {hist.get('time', 'N/A')}")
                    st.markdown("---")
        
        # Query input
        query_input = st.text_area(
            "Enter your question:",
            value=query_to_use,
            height=100,
            placeholder="e.g., What are the best hotels in Paris for families?"
        )
        
        # Submit button
        submit_button = st.button("🚀 Get Answer", type="primary", use_container_width=True)
    
    with col2:
        st.subheader("📊 Quick Stats")
        # Placeholder for stats - will be updated after query
        stats_placeholder = st.empty()
        
        # Show previous stats if available (before new query)
        if 'last_result' in st.session_state and not submit_button:
            with stats_placeholder.container():
                prev_result = st.session_state.last_result
                st.metric("Intent", prev_result.get('intent', 'N/A').replace('_', ' ').title())
                st.metric("Processing Time", f"{prev_result.get('processing_time', 0):.2f}s")
                st.metric("Sources Found", len(prev_result.get('sources', [])))
                if prev_result.get('web_results'):
                    st.metric("Web Results", len(prev_result.get('web_results', [])))
    
    # Process query
    if submit_button and query_input.strip():
        with st.spinner("🔄 Processing your query..."):
            result, error = query_api(query_input, include_web, top_k)
            
            if error:
                st.error(f"❌ {error}")
            elif result:
                st.session_state.last_result = result
                
                # Update stats in the placeholder immediately
                with stats_placeholder.container():
                    st.metric("Intent", result.get('intent', 'N/A').replace('_', ' ').title())
                    st.metric("Processing Time", f"{result.get('processing_time', 0):.2f}s")
                    st.metric("Sources Found", len(result.get('sources', [])))
                    if result.get('web_results'):
                        st.metric("Web Results", len(result.get('web_results', [])))
                
                # Save to query history
                if 'query_history' not in st.session_state:
                    st.session_state.query_history = []
                
                st.session_state.query_history.append({
                    'query': query_input,
                    'intent': result.get('intent', 'N/A'),
                    'time': datetime.now().strftime("%H:%M:%S")
                })
                
                # Display results in tabs
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "💬 Answer", 
                    "🎯 Intent & Similar", 
                    "📚 Sources", 
                    "🌐 Web Results",
                    "📋 Raw JSON"
                ])
                
                # Tab 1: Answer
                with tab1:
                    st.markdown("### 💬 AI Generated Answer")
                    
                    # Intent badge
                    intent = result.get('intent', 'general')
                    st.markdown(get_intent_badge(intent), unsafe_allow_html=True)
                    
                    # Answer
                    answer = result.get('answer', 'No answer generated')
                    # Replace newlines with HTML breaks for proper display
                    answer_html = answer.replace('\n', '<br>')
                    st.markdown(f'<div class="answer-box">{answer_html}</div>', unsafe_allow_html=True)
                    
                    # Also show as regular markdown for better formatting
                    with st.expander("📝 View as formatted text", expanded=False):
                        st.markdown(answer)
                    
                    # Processing info
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.info(f"⏱️ Time: {result.get('processing_time', 0):.2f}s")
                    with col2:
                        st.info(f"📚 Sources: {len(result.get('sources', []))}")
                    with col3:
                        web_count = len(result.get('web_results', [])) if result.get('web_results') else 0
                        st.info(f"🌐 Web: {web_count}")
                    
                    st.markdown("---")
                    
                    # Follow-up questions section
                    st.markdown("### 💭 Ask a Follow-up Question")
                    
                    # Generate suggested follow-ups based on intent
                    intent = result.get('intent', 'general')
                    suggested_followups = {
                        "hotel_search": [
                            "What are the best neighborhoods to stay in?",
                            "Are there any budget-friendly options?",
                            "What amenities should I look for?",
                            "How far in advance should I book?"
                        ],
                        "visa_info": [
                            "How long does the visa process take?",
                            "What documents do I need to prepare?",
                            "Can I apply online?",
                            "What are the visa fees?"
                        ],
                        "weather": [
                            "What should I pack for this weather?",
                            "Is this a good time to visit?",
                            "Are there any weather-related travel warnings?",
                            "What's the best season to visit?"
                        ],
                        "flight_search": [
                            "What's the best time to book flights?",
                            "Which airlines fly this route?",
                            "Are there any direct flights?",
                            "What's the average flight duration?"
                        ],
                        "destination_info": [
                            "What are the must-see attractions?",
                            "How many days should I spend here?",
                            "What's the best way to get around?",
                            "Are there any hidden gems?"
                        ],
                        "travel_tips": [
                            "What are the local customs I should know?",
                            "Is it safe for solo travelers?",
                            "What's the local currency?",
                            "Do I need travel insurance?"
                        ],
                        "itinerary": [
                            "Can you add more activities?",
                            "What about food recommendations?",
                            "How much will this itinerary cost?",
                            "Are there any day trips nearby?"
                        ]
                    }
                    
                    followups = suggested_followups.get(intent, [
                        "Can you provide more details?",
                        "What else should I know?",
                        "Are there any alternatives?",
                        "What are the costs involved?"
                    ])
                    
                    # Display suggested follow-ups as buttons
                    st.markdown("**💡 Suggested follow-ups:**")
                    cols = st.columns(2)
                    for i, followup in enumerate(followups[:4]):
                        with cols[i % 2]:
                            if st.button(followup, key=f"followup_{i}", use_container_width=True):
                                st.session_state.followup_query = followup
                                st.rerun()
                    
                    # Custom follow-up input
                    st.markdown("**✍️ Or ask your own:**")
                    followup_input = st.text_input(
                        "Follow-up question:",
                        placeholder="e.g., What about family-friendly options?",
                        key="custom_followup",
                        label_visibility="collapsed"
                    )
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button("🔄 Ask Follow-up", type="secondary", use_container_width=True):
                            if followup_input.strip():
                                st.session_state.followup_query = followup_input
                                st.rerun()
                    with col2:
                        if st.button("🗑️ Clear", use_container_width=True):
                            st.session_state.clear()
                            st.rerun()
                
                # Tab 2: Intent & Similar Queries
                with tab2:
                    st.markdown("### 🎯 Detected Intent")
                    intent = result.get('intent', 'general')
                    st.markdown(get_intent_badge(intent), unsafe_allow_html=True)
                    
                    # Intent descriptions
                    intent_descriptions = {
                        "visa_info": "Queries about visa requirements, applications, and travel documentation",
                        "travel_tips": "Queries about travel advice, safety, packing, and local transport",
                        "destination_info": "Queries about destinations, attractions, and best times to visit",
                        "weather": "Queries about weather conditions and seasons",
                        "hotel_search": "Queries about accommodation options",
                        "flight_search": "Queries about flights, airlines, and travel routes",
                        "itinerary": "Queries about trip planning and itineraries"
                    }
                    
                    if intent in intent_descriptions:
                        st.info(intent_descriptions[intent])
                    
                    st.markdown("---")
                    
                    # Similar queries
                    similar_queries = result.get('similar_queries', [])
                    if similar_queries:
                        st.markdown("### 🔗 Similar Queries from Dataset")
                        for i, sq in enumerate(similar_queries, 1):
                            with st.container():
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.markdown(f"**{i}. {sq['query']}**")
                                    st.caption(f"Intent: {sq['intent']}")
                                with col2:
                                    similarity_pct = sq['similarity'] * 100
                                    st.metric("Match", f"{similarity_pct:.1f}%")
                                st.markdown("---")
                    else:
                        st.warning("No similar queries found")
                
                # Tab 3: Sources
                with tab3:
                    sources = result.get('sources', [])
                    if sources:
                        st.markdown(f"### 📚 Knowledge Base Sources ({len(sources)} found)")
                        
                        for i, source in enumerate(sources, 1):
                            with st.container():
                                st.markdown(f'<div class="source-card">', unsafe_allow_html=True)
                                
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    st.markdown(f"**Source {i}**")
                                with col2:
                                    score = source.get('score', 0)
                                    st.metric("Score", f"{score:.3f}")
                                
                                text = source.get('text', '')
                                st.markdown(text)
                                
                                # Metadata
                                if source.get('source'):
                                    st.caption(f"📄 Source: {source.get('source')}")
                                if source.get('intent'):
                                    st.caption(f"🎯 Intent: {source.get('intent')}")
                                
                                st.markdown('</div>', unsafe_allow_html=True)
                                st.markdown("")
                    else:
                        st.warning("No sources found in knowledge base")
                
                # Tab 4: Web Results
                with tab4:
                    web_results = result.get('web_results', [])
                    if web_results:
                        st.markdown(f"### 🌐 Web Search Results ({len(web_results)} found)")
                        
                        for i, web_result in enumerate(web_results, 1):
                            st.markdown(f'<div class="web-result-card">', unsafe_allow_html=True)
                            
                            st.markdown(f"**{i}. {web_result.get('title', 'N/A')}**")
                            st.markdown(web_result.get('snippet', 'No description available'))
                            st.markdown(f"🔗 [{web_result.get('url', 'N/A')}]({web_result.get('url', '#')})")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.markdown("")
                    elif include_web:
                        st.info("🌐 Web search was enabled but no results were found. This might be because:")
                        st.write("- Serper API key is not configured")
                        st.write("- The query didn't trigger web search")
                        st.write("- No relevant web results available")
                    else:
                        st.info("🌐 Web search was disabled for this query")
                
                # Tab 5: Raw JSON
                with tab5:
                    st.markdown("### 📋 Raw API Response")
                    st.json(result)
    
    elif submit_button:
        st.warning("⚠️ Please enter a question")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>Enhanced Travel RAG System | Powered by Pinecone, Groq, and Serper</p>
        <p>📚 5,000 travel queries | 🎯 7 intent categories | 🤖 AI-powered answers</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
