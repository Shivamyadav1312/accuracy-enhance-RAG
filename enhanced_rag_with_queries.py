# enhanced_rag_with_queries.py
"""
Enhanced RAG backend that uses the travel queries dataset
to improve responses with intent detection and query matching
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import httpx
import os
from typing import Optional, List, Dict
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Enhanced Travel RAG API")

# Initialize
embedder = SentenceTransformer('all-MiniLM-L6-v2')
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("documents-index")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# ==================== MODELS ====================

class EnhancedQueryRequest(BaseModel):
    query: str
    domain: str = "travel"
    include_web: bool = True
    top_k: int = 5
    detect_intent: bool = True  # New: Auto-detect query intent

class EnhancedQueryResponse(BaseModel):
    answer: str
    intent: Optional[str] = None
    similar_queries: List[Dict] = []
    sources: List[Dict] = []
    web_results: Optional[List[Dict]] = None
    processing_time: float

# ==================== INTENT DETECTION ====================

def detect_query_intent(query: str) -> Dict:
    """
    Detect the intent of user query by matching with known travel queries
    """
    # Generate query embedding
    query_embedding = embedder.encode(query).tolist()
    
    # Try with type filter first
    results = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True,
        filter={
            "domain": "travel",
            "type": "query"  # Only match with query examples
        }
    )
    
    # If no results with filter, try without type filter (fallback)
    if not results.get('matches') or len(results['matches']) == 0:
        results = index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True,
            filter={"domain": "travel"}
        )
    
    if not results.get('matches') or len(results['matches']) == 0:
        return {"intent": "general", "confidence": 0.0, "similar_queries": []}
    
    # Get the most common intent from top matches
    intents = {}
    similar_queries = []
    
    for match in results['matches']:
        intent = match['metadata'].get('intent', 'unknown')
        intents[intent] = intents.get(intent, 0) + match['score']
        
        similar_queries.append({
            "query": match['metadata']['text'],
            "intent": intent,
            "similarity": float(match['score'])
        })
    
    # Find dominant intent
    dominant_intent = max(intents.items(), key=lambda x: x[1])
    
    return {
        "intent": dominant_intent[0],
        "confidence": float(dominant_intent[1] / len(results['matches'])),
        "similar_queries": similar_queries
    }

# ==================== ENHANCED RETRIEVAL ====================

def retrieve_with_intent(
    query: str,
    intent: Optional[str] = None,
    domain: str = "travel",
    top_k: int = 5
) -> List[Dict]:
    """
    Retrieve documents with intent-aware filtering
    """
    query_embedding = embedder.encode(query).tolist()
    
    # Build filter based on intent
    filter_dict = {"domain": domain}
    
    # If we know the intent, we can add more specific filtering
    if intent:
        # You can add intent-specific metadata here if your documents have it
        pass
    
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter=filter_dict
    )
    
    return [
        {
            "text": match["metadata"].get("text", ""),
            "source": match["metadata"].get("source", ""),
            "intent": match["metadata"].get("intent"),
            "score": float(match.get("score", 0))
        }
        for match in results.get("matches", [])
    ]

def needs_web_search(query: str, intent: str) -> bool:
    """Enhanced web search detection based on intent"""
    fresh_keywords = ['latest', 'current', 'recent', 'today', 'now', 'new', '2025', '2024']
    
    # Intents that typically need fresh data
    fresh_intents = ['flight_search', 'hotel_search', 'weather', 'visa_info']
    
    return (
        any(kw in query.lower() for kw in fresh_keywords) or
        intent in fresh_intents
    )

def create_enhanced_search_query(original_query: str, doc_context: List[Dict]) -> str:
    """Create enhanced search query using document context"""
    if not doc_context:
        return original_query
    
    # Extract key information from top documents
    context_snippets = []
    for doc in doc_context[:2]:  # Use top 2 documents
        text = doc.get('text', '')[:200]  # First 200 chars
        if text:
            context_snippets.append(text)
    
    # Combine query with context
    if context_snippets:
        context_text = " ".join(context_snippets)
        enhanced_query = f"{original_query} {context_text[:150]}"
        print(f"Enhanced web search query with document context")
        return enhanced_query
    
    return original_query

async def search_web(query: str, doc_context: List[Dict] = None) -> List[Dict]:
    """Search web for fresh information with optional document context"""
    if not SERPER_API_KEY:
        return []
    
    try:
        # Enhance query with document context
        search_query = query
        if doc_context:
            search_query = create_enhanced_search_query(query, doc_context)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": SERPER_API_KEY},
                json={"q": search_query, "num": 5}
            )
            
            if response.status_code != 200:
                return []
            
            results = response.json()
            return [
                {
                    "title": r.get("title", ""),
                    "snippet": r.get("snippet", ""),
                    "url": r.get("link", "")
                }
                for r in results.get("organic", [])[:3]
            ]
    except Exception as e:
        print(f"Web search failed: {str(e)}")
        return []

# ==================== LLM GENERATION ====================

async def generate_intent_aware_answer(
    query: str,
    intent: str,
    doc_results: List[Dict],
    similar_queries: List[Dict],
    web_results: Optional[List[Dict]] = None
) -> str:
    """Generate answer with intent-aware context"""
    
    # Build context based on intent
    context_parts = [
        f"You are a travel expert assistant specializing in {intent.replace('_', ' ')} queries.",
        "\n## SIMILAR USER QUERIES:\n"
    ]
    
    # Add similar queries for context
    if similar_queries:
        for i, sq in enumerate(similar_queries[:3], 1):
            context_parts.append(f"{i}. {sq['query']} (intent: {sq['intent']})\n")
    
    # Add document context
    if doc_results:
        context_parts.append("\n## RELEVANT INFORMATION:\n")
        for i, doc in enumerate(doc_results, 1):
            context_parts.append(f"[{i}] {doc['text']}\n\n")
    
    # Add web results
    if web_results:
        context_parts.append("\n## CURRENT WEB INFORMATION:\n")
        for i, result in enumerate(web_results, 1):
            context_parts.append(f"[W{i}] {result['title']}: {result['snippet']}\n\n")
    
    # Intent-specific instructions
    intent_instructions = {
        "visa_info": "Provide specific visa requirements, application processes, and important warnings.",
        "travel_tips": "Give practical, actionable travel advice with safety considerations.",
        "destination_info": "Describe attractions, best times to visit, and local highlights.",
        "weather": "Provide seasonal weather patterns and clothing recommendations.",
        "hotel_search": "Suggest accommodation types with price ranges and booking tips.",
        "flight_search": "Mention airlines, typical routes, and booking strategies.",
        "itinerary": "Create a structured day-by-day plan with timing and logistics."
    }
    
    instruction = intent_instructions.get(intent, "Provide comprehensive travel information.")
    
    context_parts.append(f"\n## INSTRUCTIONS:\n{instruction}\n")
    context_parts.append(f"\n## USER QUESTION:\n{query}\n\n## YOUR ANSWER:\n")
    
    prompt = "".join(context_parts)
    
    # Call Groq API
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1024
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="LLM generation failed")
            
            return response.json()["choices"][0]["message"]["content"]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")

# ==================== API ENDPOINTS ====================

@app.post("/query", response_model=EnhancedQueryResponse)
async def enhanced_query(request: EnhancedQueryRequest):
    """
    Enhanced query endpoint with intent detection and query matching
    """
    start_time = datetime.now()
    
    try:
        # 1. Detect intent from similar queries
        intent_info = None
        detected_intent = None
        similar_queries = []
        
        if request.detect_intent:
            try:
                intent_info = detect_query_intent(request.query)
                detected_intent = intent_info.get('intent', 'general')
                similar_queries = intent_info.get('similar_queries', [])
                print(f"DEBUG: Detected intent: {detected_intent}, Similar queries: {len(similar_queries)}")
            except Exception as e:
                print(f"DEBUG: Intent detection failed: {str(e)}")
                detected_intent = "general"
                similar_queries = []
        
        # 2. Retrieve relevant documents
        doc_results = retrieve_with_intent(
            request.query,
            detected_intent,
            request.domain,
            request.top_k
        )
        
        # 3. Decide if web search is needed (enhanced with document context)
        web_results = None
        if request.include_web or (detected_intent and needs_web_search(request.query, detected_intent)):
            web_results = await search_web(request.query, doc_results)
        
        # 4. Generate intent-aware answer
        answer = await generate_intent_aware_answer(
            request.query,
            detected_intent or "general",
            doc_results,
            similar_queries,
            web_results
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return EnhancedQueryResponse(
            answer=answer,
            intent=detected_intent,
            similar_queries=similar_queries[:3],
            sources=doc_results,
            web_results=web_results,
            processing_time=processing_time
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/intents")
async def get_available_intents():
    """Get list of available query intents"""
    return {
        "intents": [
            "visa_info",
            "travel_tips",
            "destination_info",
            "weather",
            "hotel_search",
            "flight_search",
            "itinerary"
        ]
    }

@app.get("/similar-queries/{query}")
async def find_similar_queries(query: str, top_k: int = 5):
    """Find similar queries from the dataset"""
    intent_info = detect_query_intent(query)
    return {
        "query": query,
        "detected_intent": intent_info['intent'],
        "confidence": intent_info['confidence'],
        "similar_queries": intent_info['similar_queries'][:top_k]
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "intent_detection": True,
            "query_matching": True,
            "web_search": bool(SERPER_API_KEY),
            "llm_generation": bool(GROQ_API_KEY)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)