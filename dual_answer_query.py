"""
Enhanced Query System with Dual Answers
- Answer 1: Based on uploaded documents
- Answer 2: Generalized knowledge
"""

from typing import List, Dict, Optional
from app2 import (
    retrieve_documents, 
    generate_answer, 
    detect_domain, 
    detect_intent,
    search_web,
    needs_web_search
)
import httpx
from config import config
import logging

logger = logging.getLogger(__name__)

async def generate_dual_answer(
    query: str, 
    user_doc_results: List[Dict],
    general_doc_results: List[Dict],
    web_results: Optional[List[Dict]] = None,
    llm_provider: str = "together"
) -> Dict[str, str]:
    """
    Generate TWO separate answers:
    1. Document-specific answer (from user uploads)
    2. Generalized answer (from general knowledge + database)
    """
    
    # Answer 1: Document-Specific
    doc_answer = await generate_document_specific_answer(
        query, user_doc_results, llm_provider
    )
    
    # Answer 2: Generalized
    general_answer = await generate_generalized_answer(
        query, general_doc_results, web_results, llm_provider
    )
    
    return {
        "document_answer": doc_answer,
        "general_answer": general_answer,
        "has_user_documents": len(user_doc_results) > 0,
        "has_general_knowledge": len(general_doc_results) > 0
    }


async def generate_document_specific_answer(
    query: str,
    doc_results: List[Dict],
    llm_provider: str = "together"
) -> str:
    """Generate answer ONLY from user's uploaded documents"""
    
    if not doc_results or len(doc_results) == 0:
        return "No relevant information found in your uploaded documents."
    
    # Build context from user documents only
    context_parts = [
        "You are analyzing the user's PERSONAL UPLOADED DOCUMENTS.\n\n"
        "INSTRUCTIONS:\n"
        "- Answer ONLY based on what is explicitly stated in these documents\n"
        "- If information is not in the documents, say 'Not mentioned in your documents'\n"
        "- Quote specific parts when relevant\n"
        "- Be precise and document-focused\n"
        "- Use phrases like 'According to your documents...', 'Your files mention...'\n\n"
        "USER'S UPLOADED DOCUMENTS:\n\n"
    ]
    
    # Group by source
    by_source = {}
    for doc in doc_results:
        source = doc.get('source', 'Unknown')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(doc['text'])
    
    # Add each document
    for idx, (source, chunks) in enumerate(by_source.items(), 1):
        context_parts.append(f"\n{'='*60}\n")
        context_parts.append(f"Document {idx}: {source}\n")
        context_parts.append(f"{'='*60}\n\n")
        for chunk in chunks:
            context_parts.append(f"{chunk}\n\n")
    
    context_parts.append(
        f"\nQUESTION: {query}\n\n"
        "ANSWER (based ONLY on the uploaded documents above):"
    )
    
    prompt = "".join(context_parts)
    
    # Call LLM
    return await call_llm(prompt, llm_provider)


async def generate_generalized_answer(
    query: str,
    doc_results: List[Dict],
    web_results: Optional[List[Dict]] = None,
    llm_provider: str = "together"
) -> str:
    """Generate comprehensive answer using general knowledge + database + web"""
    
    context_parts = [
        "You are an EXPERT CONSULTANT providing comprehensive, detailed answers.\n\n"
        "INSTRUCTIONS:\n"
        "- Use your FULL KNOWLEDGE BASE to answer comprehensively\n"
        "- Provide context, background, and expert insights\n"
        "- Include industry trends, best practices, and recommendations\n"
        "- Structure your answer with clear sections and headings\n"
        "- Be detailed and thorough - aim for 300-500 words\n"
        "- Add examples, statistics, and actionable insights\n"
        "- Make it valuable and informative\n\n"
    ]
    
    # Add reference documents if available
    if doc_results and len(doc_results) > 0:
        context_parts.append("REFERENCE INFORMATION (use as foundation, but enhance with your expertise):\n\n")
        for i, doc in enumerate(doc_results[:5], 1):
            context_parts.append(f"Reference {i}:\n{doc['text']}\n\n")
    
    # Add web results
    if web_results:
        context_parts.append("\nCURRENT WEB INFORMATION:\n")
        for i, result in enumerate(web_results, 1):
            context_parts.append(f"[{i}] {result['title']}: {result['snippet']}\n\n")
    
    context_parts.append(
        f"\nQUESTION: {query}\n\n"
        "COMPREHENSIVE EXPERT ANSWER (use all your knowledge + references above):"
    )
    
    prompt = "".join(context_parts)
    
    # Call LLM
    return await call_llm(prompt, llm_provider)


async def call_llm(prompt: str, llm_provider: str = "together") -> str:
    """Call the selected LLM provider"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if llm_provider == "together" and config.TOGETHER_API_KEY:
                response = await client.post(
                    "https://api.together.xyz/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {config.TOGETHER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": config.LLM_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 2000,
                        "top_p": 0.9
                    }
                )
                
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                else:
                    return f"Error from Together AI: {response.text}"
            
            elif llm_provider == "groq" and config.GROQ_API_KEY:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {config.GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 2000
                    }
                )
                
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                else:
                    return f"Error from Groq: {response.text}"
            
            else:
                return "No LLM API key configured"
    
    except Exception as e:
        logger.error(f"LLM call failed: {str(e)}")
        return f"Error generating answer: {str(e)}"


async def query_with_dual_answers(
    query: str,
    domain: Optional[str] = None,
    user_id: Optional[str] = None,
    top_k: int = 5,
    include_web: bool = False,
    llm_provider: str = "together"
) -> Dict:
    """
    Main query function that returns dual answers
    """
    
    # Detect domain if needed
    if not domain:
        domain = detect_domain(query)
    
    # Detect intent
    intent = detect_intent(query)
    
    # Retrieve user documents (if user_id provided)
    user_doc_results = []
    if user_id:
        user_doc_results = retrieve_documents(
            query, domain, top_k, user_id=user_id, include_reports=False
        )
    
    # Retrieve general knowledge (no user_id filter)
    general_doc_results = retrieve_documents(
        query, domain, top_k, user_id=None, include_reports=True
    )
    
    # Web search if needed
    web_results = None
    if include_web or needs_web_search(query):
        web_results = await search_web(query, general_doc_results)
    
    # Generate dual answers
    answers = await generate_dual_answer(
        query, user_doc_results, general_doc_results, web_results, llm_provider
    )
    
    return {
        "query": query,
        "domain": domain,
        "intent": intent,
        "document_answer": answers["document_answer"],
        "general_answer": answers["general_answer"],
        "user_documents_found": len(user_doc_results),
        "general_sources_found": len(general_doc_results),
        "user_sources": user_doc_results,
        "general_sources": general_doc_results,
        "web_results": web_results,
        "has_user_documents": answers["has_user_documents"]
    }
