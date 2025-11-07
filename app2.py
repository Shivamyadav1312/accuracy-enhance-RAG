# complete_rag_backend.py - Unified RAG Backend with Document Ingestion
"""
Complete RAG System for Domain-Specific AI Insights
- Document ingestion (PDF, DOCX, TXT)
- Vector storage with Pinecone
- Semantic search with domain filtering
- Web search integration for fresh data
- LLM generation with Groq/Llama
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
import PyPDF2
import docx
import httpx
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
from pinecone import Pinecone
import os
import logging
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path
import hashlib
import io
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================

class Config:
    """Application configuration"""
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENV = os.getenv("PINECONE_ENV", "us-west1-gcp")
    SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
    
    # Model settings
    EMBEDDING_MODEL = "paraphrase-MiniLM-L3-v2"  # Smaller, faster model
    LLM_MODEL = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"  # Together AI model
    LLM_PROVIDER = "together"  # Options: "groq" or "together"
    
    # Document processing
    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 100
    
    # Query settings
    DEFAULT_TOP_K = 5
    MAX_TOKENS = 3072  # Increased for comprehensive analytical responses

config = Config()

# ==================== INITIALIZATION ====================

# Global variables for lazy loading
embedder = None
text_splitter = None
pc = None
index = None

def get_embedder():
    """Lazy load embedder on first use"""
    global embedder
    if embedder is None:
        logger.info("🔄 Loading sentence transformer model (lazy load)...")
        embedder = SentenceTransformer(config.EMBEDDING_MODEL)
        logger.info("✅ Sentence transformer loaded")
    return embedder

def get_text_splitter():
    """Lazy load text splitter on first use"""
    global text_splitter
    if text_splitter is None:
        logger.info("🔄 Initializing text splitter...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        logger.info("✅ Text splitter initialized")
    return text_splitter

def get_pinecone_index():
    """Lazy load Pinecone on first use"""
    global pc, index
    if index is None and config.PINECONE_API_KEY:
        logger.info("🔄 Connecting to Pinecone...")
        try:
            pc = Pinecone(api_key=config.PINECONE_API_KEY)
            index = pc.Index("documents-index")
            logger.info("✅ Pinecone connected")
        except Exception as e:
            logger.error(f"⚠️ Pinecone connection failed: {str(e)}")
            raise HTTPException(status_code=503, detail="Vector database unavailable")
    return index

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager - server starts immediately"""
    logger.info("✅ Backend fully started and ready to serve requests.")
    yield
    logger.info("Shutting down...")

app = FastAPI(title="RAG Backend API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== DATA MODELS ====================

class QueryRequest(BaseModel):
    query: str
    domain: Optional[str] = None  # If None, will auto-detect
    include_web: bool = False
    top_k: int = 5
    user_id: Optional[str] = None  # Filter by user's documents
    detect_intent: bool = True  # Enable intent detection
    detect_domain: bool = True  # Auto-detect domain (travel/real_estate)
    llm_provider: str = "together"  # Options: "groq" or "together"
    include_reports: bool = True  # Include CSV reports from 'reports' namespace

class QueryResponse(BaseModel):
    answer: str
    intent: Optional[str] = None
    domain: Optional[str] = None  # Detected or specified domain
    sources: List[Dict]
    web_results: Optional[List[Dict]] = None
    processing_time: float
    reasoning: Optional[str] = None  # Step-by-step reasoning

class DocumentUploadRequest(BaseModel):
    domain: str
    file_name: str

class IngestionResponse(BaseModel):
    status: str
    chunks_created: int
    processing_time: float
    file_name: str

# ==================== DOCUMENT PROCESSING ====================

def extract_text_with_ocr(image) -> str:
    """Extract text from image using OCR"""
    try:
        text = pytesseract.image_to_string(image, lang='eng')
        return text.strip()
    except Exception as e:
        logger.warning(f"OCR failed: {str(e)}")
        return ""

def extract_text_from_file(file_content: bytes, filename: str, use_ocr: bool = True) -> str:
    """Extract text from PDF, DOCX, or TXT files with OCR support"""
    ext = Path(filename).suffix.lower()
    
    try:
        if ext == '.pdf':
            # Try standard text extraction first
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text_parts = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                
                # If page has little or no text, try OCR
                if use_ocr and (not page_text or len(page_text.strip()) < 50):
                    logger.info(f"Page {page_num + 1} has minimal text, attempting OCR...")
                    try:
                        # Convert PDF page to image
                        images = convert_from_bytes(
                            file_content,
                            first_page=page_num + 1,
                            last_page=page_num + 1,
                            dpi=300
                        )
                        if images:
                            ocr_text = extract_text_with_ocr(images[0])
                            if ocr_text:
                                page_text = ocr_text
                                logger.info(f"OCR extracted {len(ocr_text)} characters from page {page_num + 1}")
                    except Exception as e:
                        logger.warning(f"OCR failed for page {page_num + 1}: {str(e)}")
                
                if page_text:
                    text_parts.append(page_text)
            
            full_text = "\n\n".join(text_parts)
            
            # If still no text, try OCR on entire PDF
            if use_ocr and len(full_text.strip()) < 100:
                logger.info("Minimal text extracted, attempting full PDF OCR...")
                try:
                    images = convert_from_bytes(file_content, dpi=300)
                    ocr_parts = []
                    for i, image in enumerate(images):
                        ocr_text = extract_text_with_ocr(image)
                        if ocr_text:
                            ocr_parts.append(ocr_text)
                            logger.info(f"OCR page {i + 1}: {len(ocr_text)} characters")
                    if ocr_parts:
                        full_text = "\n\n".join(ocr_parts)
                except Exception as e:
                    logger.warning(f"Full PDF OCR failed: {str(e)}")
            
            return full_text
        
        elif ext in ['.docx', '.doc']:
            doc = docx.Document(io.BytesIO(file_content))
            return "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())
        
        elif ext == '.txt':
            return file_content.decode('utf-8')
        
        elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            # Direct image file - use OCR
            if use_ocr:
                image = Image.open(io.BytesIO(file_content))
                return extract_text_with_ocr(image)
            else:
                raise ValueError("OCR is required for image files but is disabled")
        
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    except Exception as e:
        logger.error(f"Text extraction failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to extract text: {str(e)}")

def chunk_and_embed(text: str, filename: str, domain: str, user_id: Optional[str] = None) -> List[Dict]:
    """Split text into chunks and create embeddings"""
    splitter = get_text_splitter()
    chunks = splitter.split_text(text)
    logger.info(f"Created {len(chunks)} chunks from {filename}")
    
    vectors = []
    model = get_embedder()
    for i, chunk in enumerate(chunks):
        embedding = model.encode(chunk).tolist()
        doc_id = hashlib.md5(f"{user_id}_{filename}_{i}".encode()).hexdigest() if user_id else hashlib.md5(f"{filename}_{i}".encode()).hexdigest()
        
        metadata = {
            "text": chunk,
            "source": filename,
            "domain": domain,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "timestamp": datetime.now().isoformat(),
            "type": "document"  # Mark as user document vs query
        }
        
        # Add user_id if provided
        if user_id:
            metadata["user_id"] = user_id
        
        vectors.append({
            "id": doc_id,
            "values": embedding,
            "metadata": metadata
        })
    
    return vectors

def ingest_document(file_content: bytes, filename: str, domain: str, user_id: Optional[str] = None) -> Dict:
    """Complete document ingestion pipeline"""
    start_time = datetime.now()
    
    # Extract text
    text = extract_text_from_file(file_content, filename)
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text content found in document")
    
    # Create chunks and embeddings with user_id
    vectors = chunk_and_embed(text, filename, domain, user_id)
    
    # Get Pinecone index
    idx = get_pinecone_index()
    
    # Upload to Pinecone in batches
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        idx.upsert(vectors=batch)
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    return {
        "status": "success",
        "chunks_created": len(vectors),
        "processing_time": processing_time,
        "file_name": filename,
        "user_id": user_id
    }

# ==================== DOMAIN & INTENT DETECTION ====================

def detect_domain(query: str) -> str:
    """Automatically detect if query is about travel or real estate"""
    query_lower = query.lower()
    
    # Real estate keywords
    real_estate_keywords = [
        'property', 'real estate', 'housing', 'rental', 'rent', 'apartment', 'condo',
        'mortgage', 'home price', 'house price', 'property market', 'residential',
        'commercial property', 'investment property', 'real estate market',
        'housing demand', 'housing supply', 'property value', 'property investment',
        'real estate trend', 'property price', 'housing market', 'realty',
        'land', 'plot', 'villa', 'penthouse', 'square feet', 'sqft',
        'builder', 'developer', 'construction', 'emi', 'down payment'
    ]
    
    # Travel keywords
    travel_keywords = [
        'travel', 'trip', 'vacation', 'holiday', 'tour', 'flight', 'hotel',
        'visa', 'passport', 'destination', 'tourism', 'tourist', 'itinerary',
        'booking', 'airline', 'airport', 'train', 'rail', 'bus', 'road trip',
        'backpack', 'cruise', 'resort', 'accommodation', 'sightseeing',
        'adventure', 'explore', 'visit', 'journey', 'cultural', 'festival',
        'weather', 'season', 'budget travel', 'luxury travel', 'solo travel',
        'family vacation', 'honeymoon', 'weekend getaway', 'pilgrimage'
    ]
    
    # Count matches
    real_estate_score = sum(1 for keyword in real_estate_keywords if keyword in query_lower)
    travel_score = sum(1 for keyword in travel_keywords if keyword in query_lower)
    
    # Determine domain
    if real_estate_score > travel_score:
        return "real_estate"
    elif travel_score > real_estate_score:
        return "travel"
    else:
        # Default to travel if ambiguous
        return "travel"

def detect_intent(query: str) -> str:
    """Simple intent detection based on keywords"""
    query_lower = query.lower()
    
    # Intent keywords
    if any(word in query_lower for word in ['visa', 'passport', 'document', 'requirement', 'application']):
        return 'visa_info'
    elif any(word in query_lower for word in ['hotel', 'accommodation', 'stay', 'lodge', 'resort']):
        return 'hotel_search'
    elif any(word in query_lower for word in ['flight', 'airline', 'fly', 'ticket', 'booking']):
        return 'flight_search'
    elif any(word in query_lower for word in ['weather', 'temperature', 'climate', 'season', 'rain']):
        return 'weather'
    elif any(word in query_lower for word in ['itinerary', 'plan', 'schedule', 'trip plan', 'day by day']):
        return 'itinerary'
    elif any(word in query_lower for word in ['tip', 'advice', 'guide', 'safety', 'custom', 'culture']):
        return 'travel_tips'
    elif any(word in query_lower for word in ['attraction', 'place', 'visit', 'destination', 'city', 'country']):
        return 'destination_info'
    else:
        return 'general'

def needs_web_search(query: str) -> bool:
    """Detect if query needs fresh information"""
    fresh_keywords = ['latest', 'current', 'recent', 'today', 'now', 'new', '2025', '2024']
    return any(kw in query.lower() for kw in fresh_keywords)

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
        # Extract key entities/terms from context
        context_text = " ".join(context_snippets)
        
        # Create enhanced query
        enhanced_query = f"{original_query} {context_text[:150]}"
        logger.info(f"Enhanced query: {enhanced_query[:100]}...")
        return enhanced_query
    
    return original_query

async def search_web(query: str, doc_context: List[Dict] = None) -> List[Dict]:
    """Search web using Serper API with optional document context"""
    if not config.SERPER_API_KEY:
        logger.warning("Serper API key not configured")
        return []
    
    try:
        # Enhance query with document context
        search_query = query
        if doc_context:
            search_query = create_enhanced_search_query(query, doc_context)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": config.SERPER_API_KEY},
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
        logger.error(f"Web search failed: {str(e)}")
        return []

def retrieve_documents(query: str, domain: Optional[str], top_k: int = 5, user_id: Optional[str] = None, include_reports: bool = True) -> List[Dict]:
    """Retrieve relevant documents from vector DB with optional user filtering and reports namespace"""
    try:
        # Generate query embedding
        model = get_embedder()
        query_embedding = model.encode(query).tolist()
        
        # Build filter
        filter_dict = {}
        if domain:
            filter_dict["domain"] = domain
        
        # Add user_id filter if provided
        if user_id:
            filter_dict["user_id"] = user_id
        
        # For analytical queries, retrieve more documents to ensure diversity
        # This helps get chunks from all uploaded documents, not just the most similar one
        retrieval_k = top_k * 2 if top_k < 20 else top_k
        
        # Get Pinecone index
        idx = get_pinecone_index()
        
        # Query default namespace (user documents)
        results_default = idx.query(
            vector=query_embedding,
            top_k=retrieval_k,
            include_metadata=True,
            filter=filter_dict if filter_dict else None,
            namespace=""  # Default namespace
        )
        
        all_matches = results_default.get("matches", [])
        
        # Also query reports namespace if enabled
        if include_reports:
            results_reports = idx.query(
                vector=query_embedding,
                top_k=retrieval_k // 2,  # Get fewer from reports
                include_metadata=True,
                filter={"domain": domain} if domain else None,
                namespace="reports"  # Reports namespace
            )
            all_matches.extend(results_reports.get("matches", []))
            logger.info(f"Retrieved {len(results_default.get('matches', []))} from default namespace, {len(results_reports.get('matches', []))} from reports namespace")
        
        # Sort all matches by score
        all_matches.sort(key=lambda x: x["score"], reverse=True)
        results = {"matches": all_matches}
        
        # Diversify results to include chunks from different source documents
        matches = results.get("matches", [])[:retrieval_k * 2]  # Limit before diversification
        
        # Group by source document
        by_source = {}
        for match in matches:
            source = match["metadata"].get("source", "unknown")
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(match)
        
        logger.info(f"Found {len(by_source)} unique source documents")
        
        # Strategy: Ensure we get chunks from ALL different documents
        # If we have 3 documents and top_k=5, get at least 1-2 chunks from each document
        diverse_matches = []
        
        if len(by_source) > 0:
            # Calculate how many chunks to take from each source
            chunks_per_source = max(1, top_k // len(by_source))
            remaining_slots = top_k - (chunks_per_source * len(by_source))
            
            # First pass: Take equal chunks from each source
            for source, source_matches in by_source.items():
                diverse_matches.extend(source_matches[:chunks_per_source])
            
            # Second pass: Fill remaining slots with highest scoring chunks
            if remaining_slots > 0:
                all_remaining = []
                for source, source_matches in by_source.items():
                    all_remaining.extend(source_matches[chunks_per_source:])
                all_remaining.sort(key=lambda x: x["score"], reverse=True)
                diverse_matches.extend(all_remaining[:remaining_slots])
        
        # Sort by score
        diverse_matches.sort(key=lambda x: x["score"], reverse=True)
        final_matches = diverse_matches[:top_k]
        
        logger.info(f"Retrieved {len(final_matches)} chunks from {len(by_source)} different source documents")
        
        return [
            {
                "text": match["metadata"]["text"],
                "source": match["metadata"]["source"],
                "domain": match["metadata"]["domain"],
                "score": float(match["score"]),
                "user_id": match["metadata"].get("user_id"),
                "type": match["metadata"].get("type", "document")
            }
            for match in final_matches
        ]
    
    except Exception as e:
        logger.error(f"Document retrieval failed: {str(e)}")
        return []

# ==================== LLM GENERATION ====================

async def generate_answer(query: str, doc_results: List[Dict], web_results: Optional[List[Dict]] = None, llm_provider: str = "together") -> str:
    """Generate analytical, synthesized answer using Together AI or Groq"""
    
    # Detect if query is analytical (comparison, similarity, analysis)
    analytical_keywords = ['similarity', 'similar', 'compare', 'difference', 'common', 'theme', 
                          'pattern', 'trend', 'analyze', 'analysis', 'relationship', 'connection']
    is_analytical = any(keyword in query.lower() for keyword in analytical_keywords)
    
    # Check if we have documents
    has_documents = doc_results and len(doc_results) > 0
    
    # Build context based on query type
    if is_analytical and has_documents:
        # For analytical queries: emphasize synthesis and comparison
        context_parts = [
            "You are an expert analyst. Your task is to ANALYZE, SYNTHESIZE, and COMPARE the content across multiple documents. "
            "Do NOT just describe what's in each document. Instead:\n"
            "1. Identify common themes, patterns, and insights across ALL documents\n"
            "2. Compare and contrast different perspectives\n"
            "3. Synthesize information into coherent findings\n"
            "4. Provide structured, analytical responses with clear categories\n"
            "5. Use your expertise to draw meaningful conclusions\n\n"
        ]
        
                    # Add full document content for analysis with clear source labels
        # First, list all unique sources and group chunks by source
        unique_sources = list(set(doc.get('source', 'Unknown') for doc in doc_results))
        
        # Group chunks by their source document
        chunks_by_source = {}
        for doc in doc_results:
            source = doc.get('source', 'Unknown')
            if source not in chunks_by_source:
                chunks_by_source[source] = []
            chunks_by_source[source].append(doc['text'])
        
        # Create readable names for sources
        def get_readable_name(src):
            if 'amadeus' in src.lower():
                return "Amadeus Report (Future Traveller Tribes 2030)"
            elif 'accenture' in src.lower() or 'travel-industrys' in src.lower():
                return "Accenture Report (Travel Industry's New Trip)"
            elif 'wef' in src.lower():
                return "WEF Report (Travel and Tourism at a Turning Point 2025)"
            else:
                # Use filename without extension
                return src.replace('.pdf', '').replace('.docx', '').replace('.txt', '').replace('_', ' ').title()
        
        context_parts.append("=" * 80 + "\n")
        context_parts.append(f"YOU HAVE {len(unique_sources)} DIFFERENT SOURCE DOCUMENTS TO ANALYZE:\n")
        context_parts.append(f"\nIMPORTANT: These are {len(unique_sources)} SEPARATE, DISTINCT documents (not the same document repeated):\n\n")
        for idx, src in enumerate(unique_sources, 1):
            readable = get_readable_name(src)
            chunk_count = len(chunks_by_source[src])
            context_parts.append(f"{idx}. **{readable}** ({chunk_count} chunk(s) from this document)\n")
        context_parts.append("\n" + "=" * 80 + "\n\n")
        context_parts.append("CRITICAL INSTRUCTIONS:\n")
        context_parts.append("- These are DIFFERENT documents with DIFFERENT content\n")
        context_parts.append("- DO NOT say they are 'identical' or 'the same' unless the content is truly identical\n")
        context_parts.append("- Analyze what is UNIQUE to each document and what is COMMON across them\n")
        context_parts.append("- Use the actual document names listed above, NOT 'Document 1, Document 2, Document 3'\n\n")
        context_parts.append("DOCUMENT CONTENT (grouped by source):\n\n")
        
        # Present content grouped by source document
        for idx, src in enumerate(unique_sources, 1):
            readable_name = get_readable_name(src)
            context_parts.append(f"\n{'='*80}\n")
            context_parts.append(f"SOURCE DOCUMENT {idx}: {readable_name}\n")
            context_parts.append(f"{'='*80}\n\n")
            
            # Combine all chunks from this source
            for chunk_idx, chunk_text in enumerate(chunks_by_source[src], 1):
                context_parts.append(f"[Excerpt {chunk_idx} from {readable_name}]:\n")
                context_parts.append(f"{chunk_text}\n\n")
            
            context_parts.append(f"\n{'='*80}\n\n")
    else:
        # For general queries: enhanced detailed approach
        context_parts = [
            "You are an expert AI assistant with deep knowledge across multiple domains. "
            "Your goal is to provide COMPREHENSIVE, DETAILED, and INSIGHTFUL answers that go far beyond simple extraction.\n\n"
            "INSTRUCTIONS FOR ANSWERING:\n"
            "1. **Use Your Expertise**: Draw from your extensive knowledge to provide context, background, and broader understanding\n"
            "2. **Enhance Document Content**: Don't just repeat what's in the documents - explain, elaborate, and add valuable insights\n"
            "3. **Provide Context**: Explain WHY things matter, HOW they work, and WHAT the implications are\n"
            "4. **Add Examples**: Include relevant examples, use cases, or scenarios to illustrate points\n"
            "5. **Structure Clearly**: Use headings, bullet points, and organized sections for readability\n"
            "6. **Be Comprehensive**: Cover multiple angles - definitions, benefits, challenges, trends, best practices\n"
            "7. **Make it Actionable**: Include practical takeaways, recommendations, or next steps\n"
            "8. **Connect Ideas**: Show relationships between concepts and broader industry trends\n\n"
            "RESPONSE STYLE:\n"
            "- Start with a clear overview or definition\n"
            "- Provide detailed explanations with depth\n"
            "- Use professional yet accessible language\n"
            "- Include relevant statistics or data points when applicable\n"
            "- End with key takeaways or actionable insights\n\n"
        ]
        
        # Add documents as reference with full content
        if has_documents:
            context_parts.append("REFERENCE DOCUMENTS (Use these as foundation, but enhance with your knowledge):\n\n")
            for i, doc in enumerate(doc_results, 1):
                source_name = doc.get('source', 'Unknown')
                # Provide more context from documents
                context_parts.append(f"Document {i} (Source: {source_name}):\n")
                context_parts.append(f"{doc['text']}\n\n")
                context_parts.append(f"{'='*80}\n\n")
        else:
            # No documents - pure general knowledge query
            context_parts.append(
                "NOTE: No specific documents were provided. Use your comprehensive knowledge to answer this query.\n"
                "Provide the same level of detail and expertise as if you were consulting on this topic.\n\n"
            )
    
    # Add web results if available
    if web_results:
        context_parts.append("\nADDITIONAL WEB INFORMATION:\n")
        for i, result in enumerate(web_results, 1):
            context_parts.append(f"[W{i}] {result['title']}: {result['snippet']}\n\n")
    
    # Add query-specific instructions
    if is_analytical:
        # Get unique source names for explicit instruction
        unique_sources = list(set(doc.get('source', 'Unknown') for doc in doc_results))
        
        # Create a mapping of document names for clarity
        source_names = {}
        for src in unique_sources:
            if 'amadeus' in src.lower():
                source_names[src] = "Amadeus Report"
            elif 'accenture' in src.lower() or 'travel-industrys' in src.lower():
                source_names[src] = "Accenture Report"
            elif 'wef' in src.lower():
                source_names[src] = "WEF Report"
            else:
                source_names[src] = src.replace('.pdf', '').replace('.docx', '').replace('.txt', '').replace('_', ' ').title()
        
        readable_sources = ", ".join([f"'{source_names.get(s, s)}'" for s in unique_sources])
        
        context_parts.append(
            f"\nQUESTION: {query}\n\n"
            "CRITICAL INSTRUCTIONS FOR YOUR ANALYSIS:\n"
            f"- You have {len(unique_sources)} SEPARATE, DISTINCT source documents: {readable_sources}\n"
            f"- These are NOT the same document - they are {len(unique_sources)} different documents\n"
            "- DO NOT say 'the documents are identical' unless you verify the content is truly the same\n"
            "- First, identify what is UNIQUE to each specific document\n"
            "- Then, identify what is COMMON or similar across the different documents\n"
            "- Compare and contrast perspectives from EACH named source\n"
            "- Structure your response with clear themes/categories\n"
            "- IMPORTANT: Use the ACTUAL DOCUMENT NAMES listed above\n"
            "- NEVER use generic references like 'Document 1', 'Document 2', 'Document 3'\n"
            "- For each theme, explicitly state which named sources discuss it\n"
            "- If documents have different content, highlight the differences\n"
            "- If documents have similar content, explain what is similar and what differs\n"
            "- Use bullet points, tables, or structured format for clarity\n"
            "- Be analytical and insightful, not just descriptive\n\n"
            "ANSWER:"
        )
    else:
        context_parts.append(
            f"\nQUESTION: {query}\n\n"
            "CRITICAL INSTRUCTIONS FOR YOUR RESPONSE:\n"
            "- **Go Beyond the Documents**: Don't just extract or summarize - add context, explanations, and insights\n"
            "- **Provide Depth**: Explain concepts thoroughly with background information and implications\n"
            "- **Add Value**: Include industry context, trends, best practices, and real-world applications\n"
            "- **Structure Professionally**: Use clear headings (##, ###), bullet points, and logical flow\n"
            "- **Be Comprehensive**: Cover definition, importance, benefits, challenges, examples, and recommendations\n"
            "- **Make it Actionable**: Include practical takeaways and next steps\n"
            "- **Use Examples**: Illustrate points with relevant scenarios or use cases\n"
            "- **Connect to Broader Context**: Show how this relates to industry trends and future directions\n\n"
            "Remember: You're an expert consultant, not just a document reader. Provide the kind of detailed, "
            "insightful response that would come from a subject matter expert.\n\n"
            "ANSWER:"
        )
    
    prompt = "".join(context_parts)
    
    # Call Together AI or Groq API based on llm_provider parameter
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if llm_provider == "together" and config.TOGETHER_API_KEY:
                # Together AI API - Best for detailed analysis
                logger.info(f"Using Together AI ({config.LLM_MODEL}) for detailed response")
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
                        "max_tokens": config.MAX_TOKENS,
                        "top_p": 0.9,
                        "top_k": 50
                    }
                )
            elif llm_provider == "groq" and config.GROQ_API_KEY:
                # Groq API - Best for fast, current information
                logger.info("Using Groq (llama-3.3-70b-versatile) for fast response")
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
                        "max_tokens": config.MAX_TOKENS
                    }
                )
            else:
                # Fallback: Try Together AI first, then Groq
                if config.TOGETHER_API_KEY:
                    logger.warning(f"Requested provider '{llm_provider}' not available, falling back to Together AI")
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
                            "max_tokens": config.MAX_TOKENS,
                            "top_p": 0.9,
                            "top_k": 50
                        }
                    )
                elif config.GROQ_API_KEY:
                    logger.warning(f"Requested provider '{llm_provider}' not available, falling back to Groq")
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
                            "max_tokens": config.MAX_TOKENS
                        }
                    )
                else:
                    raise HTTPException(status_code=500, detail="No LLM API keys configured")
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"LLM API error: {error_detail}")
                raise HTTPException(status_code=500, detail=f"LLM generation failed: {error_detail}")
            
            return response.json()["choices"][0]["message"]["content"]
    
    except Exception as e:
        logger.error(f"LLM generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")

# ==================== API ENDPOINTS ====================

@app.post("/upload", response_model=IngestionResponse)
async def upload_document(
    file: UploadFile = File(...),
    domain: str = Form("general"),
    user_id: Optional[str] = Form(None)
):
    """
    Upload and ingest a document into the vector database
    
    Supports: PDF (with OCR), DOCX, TXT, Images (PNG, JPG, JPEG, TIFF, BMP)
    OCR automatically extracts text from scanned PDFs and images
    Optionally tag with user_id for personalized retrieval
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Validate file type
    ext = Path(file.filename).suffix.lower()
    supported_formats = ['.pdf', '.docx', '.txt', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
    if ext not in supported_formats:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Supported: PDF, DOCX, TXT, PNG, JPG, JPEG, TIFF, BMP"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Process document with user_id
        result = ingest_document(content, file.filename, domain, user_id)
        
        logger.info(f"Successfully ingested {file.filename} for user {user_id}")
        return IngestionResponse(**result)
    
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query the RAG system
    
    - Searches domain-specific documents
    - Optionally includes web search for fresh data
    - Returns AI-generated answer with sources
    """
    start_time = datetime.now()
    
    try:
        # 1. Auto-detect domain if not specified
        detected_domain = request.domain
        if request.detect_domain and not request.domain:
            detected_domain = detect_domain(request.query)
            logger.info(f"Auto-detected domain: {detected_domain}")
        
        # 2. Detect intent if requested
        detected_intent = None
        if request.detect_intent:
            detected_intent = detect_intent(request.query)
            logger.info(f"Detected intent: {detected_intent}")
        
        # 3. Retrieve relevant documents (with optional user_id filter and reports)
        logger.info(f"Processing query: {request.query[:50]}... (domain: {detected_domain}, user_id: {request.user_id}, include_reports: {request.include_reports})")
        doc_results = retrieve_documents(request.query, detected_domain, request.top_k, request.user_id, request.include_reports)
        
        # 3. Web search if needed (enhanced with document context)
        web_results = None
        if request.include_web or needs_web_search(request.query):
            logger.info("Triggering context-enhanced web search...")
            web_results = await search_web(request.query, doc_results)
        
        # 4. Generate answer with selected LLM provider
        answer = await generate_answer(request.query, doc_results, web_results, request.llm_provider)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResponse(
            answer=answer,
            intent=detected_intent,
            domain=detected_domain,
            sources=doc_results,
            web_results=web_results,
            processing_time=processing_time,
            reasoning=None  # Can be enhanced later with explicit reasoning steps
        )
    
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch-upload")
async def batch_upload(
    files: List[UploadFile] = File(...),
    domain: str = Form("general"),
    user_id: Optional[str] = Form(None)
):
    """Upload multiple documents at once with user_id support"""
    results = []
    total_chunks = 0
    
    for file in files:
        try:
            content = await file.read()
            result = ingest_document(content, file.filename, domain, user_id)
            results.append({"file": file.filename, "status": "success", **result})
            total_chunks += result.get("chunks_created", 0)
        except Exception as e:
            logger.error(f"Failed to upload {file.filename}: {str(e)}")
            results.append({"file": file.filename, "status": "failed", "error": str(e)})
    
    return {
        "total": len(files),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "total_chunks": total_chunks,
        "user_id": user_id,
        "results": results
    }

@app.get("/stats")
async def get_statistics():
    """Get vector database statistics"""
    try:
        idx = get_pinecone_index()
        stats = idx.describe_index_stats()
        return {
            "total_vectors": stats.get("total_vector_count", 0),
            "dimension": stats.get("dimension", 0),
            "index_fullness": stats.get("index_fullness", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/domains")
async def list_domains():
    """List available domains"""
    # This is simplified - in production, query unique domains from metadata
    return {
        "domains": ["travel", "real_estate", "market_research", "general"]
    }

@app.get("/user-documents/{user_id}")
async def get_user_documents(user_id: str):
    """Get list of documents uploaded by a specific user"""
    try:
        # Query Pinecone to get unique documents for this user
        # This is a simplified approach - in production, use a separate metadata store
        query_embedding = embedder.encode("document").tolist()
        
        results = index.query(
            vector=query_embedding,
            top_k=100,
            include_metadata=True,
            filter={"user_id": user_id, "type": "document"}
        )
        
        # Extract unique documents
        documents = {}
        for match in results.get("matches", []):
            metadata = match.get("metadata", {})
            source = metadata.get("source", "Unknown")
            if source not in documents:
                documents[source] = {
                    "filename": source,
                    "chunks": 0,
                    "timestamp": metadata.get("timestamp", "N/A")
                }
            documents[source]["chunks"] += 1
        
        return {
            "user_id": user_id,
            "documents": list(documents.values())
        }
    except Exception as e:
        logger.error(f"Failed to get user documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query-dual")
async def query_with_dual_answers(request: QueryRequest):
    """
    Enhanced query that returns BOTH:
    1. Answer from user's uploaded documents
    2. Generalized answer from knowledge base
    """
    start_time = datetime.now()
    
    try:
        # Detect domain
        detected_domain = request.domain
        if request.detect_domain and not request.domain:
            detected_domain = detect_domain(request.query)
        
        # Detect intent
        detected_intent = None
        if request.detect_intent:
            detected_intent = detect_intent(request.query)
        
        # Retrieve user documents (if user_id provided)
        user_doc_results = []
        if request.user_id:
            user_doc_results = retrieve_documents(
                request.query, detected_domain, request.top_k, 
                user_id=request.user_id, include_reports=False
            )
            logger.info(f"Found {len(user_doc_results)} chunks from user documents")
        
        # Retrieve general knowledge (no user filter)
        general_doc_results = retrieve_documents(
            request.query, detected_domain, request.top_k, 
            user_id=None, include_reports=request.include_reports
        )
        logger.info(f"Found {len(general_doc_results)} chunks from general knowledge")
        
        # Web search if needed
        web_results = None
        if request.include_web or needs_web_search(request.query):
            web_results = await search_web(request.query, general_doc_results)
        
        # Generate document-specific answer
        doc_answer = "No relevant information found in your uploaded documents."
        if user_doc_results:
            doc_answer = await generate_answer(
                request.query, user_doc_results, None, request.llm_provider
            )
        
        # Generate generalized answer
        general_answer = await generate_answer(
            request.query, general_doc_results, web_results, request.llm_provider
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "query": request.query,
            "domain": detected_domain,
            "intent": detected_intent,
            "document_answer": doc_answer,
            "general_answer": general_answer,
            "user_documents_found": len(user_doc_results),
            "general_sources_found": len(general_doc_results),
            "user_sources": user_doc_results[:3],  # Top 3 user sources
            "general_sources": general_doc_results[:3],  # Top 3 general sources
            "web_results": web_results,
            "has_user_documents": len(user_doc_results) > 0,
            "processing_time": processing_time
        }
    
    except Exception as e:
        logger.error(f"Dual query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    """Root endpoint for Render - responds instantly"""
    from fastapi.responses import JSONResponse
    return JSONResponse({
        "name": "RAG Backend API",
        "version": "1.0.0",
        "status": "running",
        "message": "Backend is live ✅",
        "endpoints": {
            "health": "GET /health - Health check",
            "ready": "GET /ready - Readiness check",
            "upload": "POST /upload - Upload single document",
            "batch_upload": "POST /batch-upload - Upload multiple documents",
            "query": "POST /query - Query with RAG + web search",
            "stats": "GET /stats - Database statistics",
            "domains": "GET /domains - List available domains"
        }
    })

@app.get("/health")
async def health():
    """Health check for Render"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "models_loaded": embedder is not None,
        "pinecone_connected": index is not None
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check - always returns 200 OK"""
    return {"ready": True, "timestamp": datetime.now().isoformat()}

# ==================== RUN ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)