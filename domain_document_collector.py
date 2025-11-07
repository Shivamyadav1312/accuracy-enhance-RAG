"""
Domain Document Collector - Ingest Downloaded Documents into Pinecone
Processes the 99 documents downloaded by auto_document_downloader.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Dict
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

# Import from existing app2.py
from app2 import ingest_document

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('domain_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
DOWNLOADED_DOCS_ROOT = "./downloaded_docs"
SUPPORTED_EXTENSIONS = ['.txt', '.csv', '.pdf', '.docx', '.xlsx']

class IngestionStats:
    """Track ingestion statistics"""
    def __init__(self):
        self.total_files = 0
        self.successful = 0
        self.failed = 0
        self.total_chunks = 0
        self.start_time = datetime.now()
        self.errors = []
        self.by_domain = {'travel': 0, 'real_estate': 0}
    
    def add_success(self, filename: str, chunks: int, domain: str):
        self.successful += 1
        self.total_chunks += chunks
        self.by_domain[domain] += 1
        logger.info(f"✅ [{domain.upper()}] {filename} ({chunks} chunks)")
    
    def add_failure(self, filename: str, error: str, domain: str):
        self.failed += 1
        self.errors.append({'file': filename, 'error': error, 'domain': domain})
        logger.error(f"❌ [{domain.upper()}] {filename} - {error}")
    
    def print_summary(self):
        duration = (datetime.now() - self.start_time).total_seconds()
        print("\n" + "="*80)
        print("📊 DOMAIN DOCUMENT INGESTION SUMMARY")
        print("="*80)
        print(f"Total Files Processed: {self.total_files}")
        print(f"✅ Successful: {self.successful}")
        print(f"❌ Failed: {self.failed}")
        print(f"📦 Total Chunks Created: {self.total_chunks}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"⚡ Average: {duration/max(self.total_files, 1):.2f} sec/file")
        print()
        print("By Domain:")
        print(f"  🏠 Real Estate: {self.by_domain['real_estate']} documents")
        print(f"  ✈️  Travel: {self.by_domain['travel']} documents")
        print("="*80)
        
        if self.errors:
            print(f"\n❌ {len(self.errors)} ERRORS:")
            for err in self.errors[:10]:
                print(f"  - [{err['domain']}] {err['file']}: {err['error']}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")

def process_text_file(file_path: Path) -> str:
    """Read text file content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encoding
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()

def ingest_single_file(file_path: Path, domain: str, stats: IngestionStats):
    """Ingest a single file into Pinecone"""
    try:
        # Read file content
        if file_path.suffix.lower() == '.txt':
            text_content = process_text_file(file_path)
            file_content = text_content.encode('utf-8')
        else:
            with open(file_path, 'rb') as f:
                file_content = f.read()
        
        # Ingest document using app2.py function
        result = ingest_document(file_content, file_path.name, domain, user_id=None)
        
        if result.get('status') == 'success':
            stats.add_success(file_path.name, result.get('chunks_created', 0), domain)
        else:
            error_msg = result.get('message', 'Unknown error')
            stats.add_failure(file_path.name, error_msg, domain)
    
    except Exception as e:
        stats.add_failure(file_path.name, str(e), domain)

def find_all_downloaded_documents() -> List[tuple]:
    """Find all downloaded documents"""
    documents = []
    root = Path(DOWNLOADED_DOCS_ROOT)
    
    if not root.exists():
        logger.error(f"Downloaded docs folder does not exist: {DOWNLOADED_DOCS_ROOT}")
        return documents
    
    # Travel documents
    travel_path = root / "travel"
    if travel_path.exists():
        for file_path in travel_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                documents.append((file_path, 'travel'))
    
    # Real estate documents
    real_estate_path = root / "real_estate"
    if real_estate_path.exists():
        for file_path in real_estate_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                documents.append((file_path, 'real_estate'))
    
    return documents

def ingest_downloaded_documents():
    """Main ingestion function"""
    
    print("="*80)
    print("🚀 DOMAIN DOCUMENT COLLECTOR")
    print("="*80)
    print("Ingesting documents downloaded by auto_document_downloader.py")
    print(f"Source: {DOWNLOADED_DOCS_ROOT}")
    print("="*80)
    
    # Find all documents
    print("\n🔍 Scanning for documents...")
    documents = find_all_downloaded_documents()
    
    if not documents:
        print("⚠️ No documents found!")
        print(f"Make sure you've run: python auto_document_downloader.py")
        return
    
    print(f"📁 Found {len(documents)} documents")
    
    # Group by domain
    by_domain = {'travel': [], 'real_estate': []}
    for file_path, domain in documents:
        by_domain[domain].append(file_path)
    
    print("\nDocuments by domain:")
    print(f"  ✈️  Travel: {len(by_domain['travel'])} files")
    print(f"  🏠 Real Estate: {len(by_domain['real_estate'])} files")
    
    # Show breakdown
    print("\n📂 Travel Documents:")
    travel_categories = {}
    for file_path in by_domain['travel']:
        category = file_path.parent.name
        travel_categories[category] = travel_categories.get(category, 0) + 1
    for cat, count in travel_categories.items():
        print(f"  - {cat}: {count} files")
    
    print("\n📂 Real Estate Documents:")
    re_categories = {}
    for file_path in by_domain['real_estate']:
        category = file_path.parent.name
        re_categories[category] = re_categories.get(category, 0) + 1
    for cat, count in re_categories.items():
        print(f"  - {cat}: {count} files")
    
    # Confirm before proceeding
    print("\n" + "="*80)
    response = input(f"Proceed with ingestion of {len(documents)} documents into Pinecone? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Ingestion cancelled by user")
        return
    
    # Initialize stats
    stats = IngestionStats()
    stats.total_files = len(documents)
    
    # Ingest documents with progress bar
    print("\n🚀 Starting ingestion...\n")
    
    for file_path, domain in tqdm(documents, desc="Ingesting", unit="doc"):
        ingest_single_file(file_path, domain, stats)
    
    # Print final summary
    stats.print_summary()
    
    # Save error log if needed
    if stats.errors:
        error_log_path = f"domain_ingestion_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(error_log_path, 'w', encoding='utf-8') as f:
            f.write("DOMAIN DOCUMENT INGESTION ERRORS\n")
            f.write("="*80 + "\n\n")
            for err in stats.errors:
                f.write(f"Domain: {err['domain']}\n")
                f.write(f"File: {err['file']}\n")
                f.write(f"Error: {err['error']}\n")
                f.write("-"*80 + "\n")
        print(f"\n📝 Error log saved to: {error_log_path}")
    
    # Next steps
    print("\n" + "="*80)
    print("✅ INGESTION COMPLETE!")
    print("="*80)
    print("\n📊 Your Pinecone vector database now contains:")
    print(f"  - {stats.by_domain['travel']} Travel documents")
    print(f"  - {stats.by_domain['real_estate']} Real Estate documents")
    print(f"  - Total: {stats.successful} documents with {stats.total_chunks} chunks")
    print("\n🎯 Next Steps:")
    print("  1. Test queries: python interactive_query.py")
    print("  2. Check Pinecone data: python check_pinecone_data.py")
    print("  3. Start UI: streamlit run streamlit_ui_with_upload.py")
    print("="*80)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest downloaded domain documents into Pinecone')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be ingested without actually ingesting')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - Scanning only, no ingestion")
        documents = find_all_downloaded_documents()
        print(f"\nFound {len(documents)} documents:")
        for file_path, domain in documents:
            print(f"  [{domain}] {file_path}")
    else:
        ingest_downloaded_documents()
