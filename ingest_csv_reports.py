"""
CSV Reports Ingestion Script
Ingests travel and real estate reports from CSV into Pinecone with namespace
"""

import pandas as pd
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import hashlib
import os
from datetime import datetime
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
INDEX_NAME = "documents-index"
NAMESPACE = "reports"  # Separate namespace for CSV reports

# Initialize
logger.info("Initializing models and connections...")
embedder = SentenceTransformer(EMBEDDING_MODEL)
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

def create_embedding_for_report(title: str, url: str, domain: str) -> list:
    """Create embedding from report metadata"""
    # Combine title, domain, and URL for richer embedding
    text = f"{domain.upper()} Report: {title}\nSource: {url}"
    embedding = embedder.encode(text).tolist()
    return embedding, text

def ingest_csv_reports(csv_path: str):
    """Ingest reports from CSV into Pinecone with namespace"""
    
    logger.info(f"Reading CSV file: {csv_path}")
    df = pd.read_csv(csv_path)
    
    logger.info(f"Found {len(df)} reports to ingest")
    logger.info(f"Domains: {df['domain'].unique().tolist()}")
    
    vectors = []
    
    for idx, row in df.iterrows():
        domain = row['domain']
        title = row['title']
        url = row['url']
        
        # Skip empty rows
        if pd.isna(title) or pd.isna(url):
            continue
        
        # Create embedding
        embedding, text = create_embedding_for_report(title, url, domain)
        
        # Create unique ID
        doc_id = hashlib.md5(f"{domain}_{title}_{url}".encode()).hexdigest()
        
        # Prepare metadata
        metadata = {
            "text": text,
            "title": title,
            "url": url,
            "source": f"{title} (CSV Report)",
            "domain": domain,
            "type": "report",  # Mark as report (vs document)
            "timestamp": datetime.now().isoformat(),
            "source_type": "csv_report"
        }
        
        vectors.append({
            "id": doc_id,
            "values": embedding,
            "metadata": metadata
        })
        
        logger.info(f"Prepared: [{domain}] {title}")
    
    # Upsert to Pinecone with namespace
    logger.info(f"\nUpserting {len(vectors)} vectors to Pinecone...")
    logger.info(f"Index: {INDEX_NAME}")
    logger.info(f"Namespace: {NAMESPACE}")
    
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch, namespace=NAMESPACE)
        logger.info(f"Upserted batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1}")
    
    logger.info(f"\n✅ Successfully ingested {len(vectors)} reports!")
    
    # Get index stats
    stats = index.describe_index_stats()
    logger.info(f"\nIndex Statistics:")
    logger.info(f"Total vectors: {stats.get('total_vector_count', 0)}")
    logger.info(f"Namespaces: {stats.get('namespaces', {})}")
    
    return len(vectors)

def verify_ingestion(sample_query: str = "luxury real estate market trends"):
    """Verify ingestion by running a test query"""
    logger.info(f"\n🔍 Testing retrieval with query: '{sample_query}'")
    
    # Create query embedding
    query_embedding = embedder.encode(sample_query).tolist()
    
    # Query the namespace
    results = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True,
        namespace=NAMESPACE
    )
    
    logger.info(f"\nFound {len(results.get('matches', []))} matches:")
    for i, match in enumerate(results.get('matches', []), 1):
        title = match['metadata'].get('title', 'Unknown')
        domain = match['metadata'].get('domain', 'Unknown')
        score = match['score']
        logger.info(f"{i}. [{domain}] {title} (score: {score:.4f})")
    
    return results

if __name__ == "__main__":
    csv_file = "travel_real_estate_reports_sources.csv"
    
    logger.info("="*80)
    logger.info("CSV REPORTS INGESTION TO PINECONE")
    logger.info("="*80)
    
    try:
        # Ingest CSV
        count = ingest_csv_reports(csv_file)
        
        # Verify with test queries
        logger.info("\n" + "="*80)
        logger.info("VERIFICATION TESTS")
        logger.info("="*80)
        
        verify_ingestion("luxury real estate market trends")
        verify_ingestion("tourism statistics and travel trends")
        
        logger.info("\n" + "="*80)
        logger.info("✅ INGESTION COMPLETE!")
        logger.info("="*80)
        logger.info(f"Total reports ingested: {count}")
        logger.info(f"Namespace: '{NAMESPACE}'")
        logger.info(f"Index: '{INDEX_NAME}'")
        
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {str(e)}")
        raise
