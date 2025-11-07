"""
Bulk Document Ingestion Script
Ingests all documents from organized folders into Pinecone
Supports: PDF, DOCX, TXT, CSV, XLSX, Images
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Dict
import pandas as pd
from dotenv import load_dotenv

# Import from existing app2.py
from app2 import ingest_document, extract_text_from_file

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bulk_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
DATA_ROOT = "data"  # Root folder for all documents
SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.csv', '.xlsx', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']

# Domain mapping based on folder structure
DOMAIN_MAPPING = {
    'real_estate': 'real_estate',
    'travel': 'travel'
}

class BulkIngestionStats:
    """Track ingestion statistics"""
    def __init__(self):
        self.total_files = 0
        self.successful = 0
        self.failed = 0
        self.total_chunks = 0
        self.start_time = datetime.now()
        self.errors = []
    
    def add_success(self, filename: str, chunks: int):
        self.successful += 1
        self.total_chunks += chunks
        logger.info(f"✅ SUCCESS: {filename} ({chunks} chunks)")
    
    def add_failure(self, filename: str, error: str):
        self.failed += 1
        self.errors.append({'file': filename, 'error': error})
        logger.error(f"❌ FAILED: {filename} - {error}")
    
    def print_summary(self):
        duration = (datetime.now() - self.start_time).total_seconds()
        logger.info("\n" + "="*80)
        logger.info("BULK INGESTION SUMMARY")
        logger.info("="*80)
        logger.info(f"Total Files Processed: {self.total_files}")
        logger.info(f"Successful: {self.successful}")
        logger.info(f"Failed: {self.failed}")
        logger.info(f"Total Chunks Created: {self.total_chunks}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Average: {duration/max(self.total_files, 1):.2f} sec/file")
        
        if self.errors:
            logger.info(f"\n❌ {len(self.errors)} ERRORS:")
            for err in self.errors[:10]:  # Show first 10 errors
                logger.info(f"  - {err['file']}: {err['error']}")
            if len(self.errors) > 10:
                logger.info(f"  ... and {len(self.errors) - 10} more errors")

def detect_domain_from_path(file_path: Path) -> str:
    """Detect domain based on folder structure"""
    parts = file_path.parts
    
    # Check if 'real_estate' or 'travel' in path
    for part in parts:
        if 'real_estate' in part.lower():
            return 'real_estate'
        elif 'travel' in part.lower():
            return 'travel'
    
    # Default to travel
    return 'travel'

def process_csv_file(file_path: Path) -> str:
    """Convert CSV to text format for ingestion"""
    try:
        df = pd.read_csv(file_path)
        
        # Create a text representation
        text_parts = [f"Data from: {file_path.name}\n"]
        text_parts.append(f"Columns: {', '.join(df.columns)}\n\n")
        
        # Add summary statistics
        text_parts.append("Summary Statistics:\n")
        text_parts.append(df.describe().to_string())
        text_parts.append("\n\n")
        
        # Add first 100 rows as text
        text_parts.append("Data Sample:\n")
        for idx, row in df.head(100).iterrows():
            row_text = " | ".join([f"{col}: {val}" for col, val in row.items()])
            text_parts.append(f"Row {idx}: {row_text}\n")
        
        return "".join(text_parts)
    
    except Exception as e:
        logger.error(f"Failed to process CSV {file_path}: {str(e)}")
        return None

def process_excel_file(file_path: Path) -> str:
    """Convert Excel to text format for ingestion"""
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        text_parts = [f"Data from: {file_path.name}\n"]
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            text_parts.append(f"\n{'='*80}\n")
            text_parts.append(f"Sheet: {sheet_name}\n")
            text_parts.append(f"{'='*80}\n")
            text_parts.append(f"Columns: {', '.join(df.columns)}\n\n")
            
            # Add summary
            text_parts.append("Summary:\n")
            text_parts.append(df.describe().to_string())
            text_parts.append("\n\n")
            
            # Add sample data
            text_parts.append("Data Sample:\n")
            for idx, row in df.head(50).iterrows():
                row_text = " | ".join([f"{col}: {val}" for col, val in row.items()])
                text_parts.append(f"Row {idx}: {row_text}\n")
        
        return "".join(text_parts)
    
    except Exception as e:
        logger.error(f"Failed to process Excel {file_path}: {str(e)}")
        return None

def ingest_single_file(file_path: Path, domain: str, stats: BulkIngestionStats, user_id: str = None):
    """Ingest a single file"""
    try:
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Special handling for CSV and Excel
        if file_path.suffix.lower() == '.csv':
            text_content = process_csv_file(file_path)
            if text_content:
                file_content = text_content.encode('utf-8')
            else:
                stats.add_failure(file_path.name, "CSV processing failed")
                return
        
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            text_content = process_excel_file(file_path)
            if text_content:
                file_content = text_content.encode('utf-8')
            else:
                stats.add_failure(file_path.name, "Excel processing failed")
                return
        
        # Ingest document
        result = ingest_document(file_content, file_path.name, domain, user_id)
        
        if result.get('status') == 'success':
            stats.add_success(file_path.name, result.get('chunks_created', 0))
        else:
            stats.add_failure(file_path.name, "Ingestion returned non-success status")
    
    except Exception as e:
        stats.add_failure(file_path.name, str(e))

def find_all_documents(root_path: str) -> List[tuple]:
    """Find all documents in folder structure"""
    documents = []
    root = Path(root_path)
    
    if not root.exists():
        logger.error(f"Root path does not exist: {root_path}")
        return documents
    
    for file_path in root.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            domain = detect_domain_from_path(file_path)
            documents.append((file_path, domain))
    
    return documents

def ingest_by_category(root_path: str, user_id: str = None, batch_size: int = 10):
    """Ingest documents with progress tracking"""
    
    logger.info("="*80)
    logger.info("BULK DOCUMENT INGESTION")
    logger.info("="*80)
    logger.info(f"Root Path: {root_path}")
    logger.info(f"User ID: {user_id or 'None (general)'}")
    logger.info(f"Supported Extensions: {', '.join(SUPPORTED_EXTENSIONS)}")
    logger.info("="*80)
    
    # Find all documents
    logger.info("\n🔍 Scanning for documents...")
    documents = find_all_documents(root_path)
    
    if not documents:
        logger.warning("⚠️ No documents found!")
        return
    
    logger.info(f"📁 Found {len(documents)} documents to ingest")
    
    # Group by domain
    by_domain = {}
    for file_path, domain in documents:
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(file_path)
    
    logger.info("\nDocuments by domain:")
    for domain, files in by_domain.items():
        logger.info(f"  - {domain}: {len(files)} files")
    
    # Confirm before proceeding
    logger.info("\n" + "="*80)
    response = input(f"Proceed with ingestion of {len(documents)} documents? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        logger.info("❌ Ingestion cancelled by user")
        return
    
    # Initialize stats
    stats = BulkIngestionStats()
    stats.total_files = len(documents)
    
    # Ingest documents
    logger.info("\n🚀 Starting ingestion...\n")
    
    for idx, (file_path, domain) in enumerate(documents, 1):
        logger.info(f"\n[{idx}/{len(documents)}] Processing: {file_path.name}")
        logger.info(f"  Domain: {domain}")
        logger.info(f"  Size: {file_path.stat().st_size / 1024:.2f} KB")
        
        ingest_single_file(file_path, domain, stats, user_id)
        
        # Progress update every batch_size files
        if idx % batch_size == 0:
            logger.info(f"\n📊 Progress: {idx}/{len(documents)} files processed")
            logger.info(f"   Success: {stats.successful}, Failed: {stats.failed}")
    
    # Print final summary
    stats.print_summary()
    
    # Save error log
    if stats.errors:
        error_log_path = f"ingestion_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(error_log_path, 'w') as f:
            f.write("INGESTION ERRORS\n")
            f.write("="*80 + "\n\n")
            for err in stats.errors:
                f.write(f"File: {err['file']}\n")
                f.write(f"Error: {err['error']}\n")
                f.write("-"*80 + "\n")
        logger.info(f"\n📝 Error log saved to: {error_log_path}")

def ingest_specific_folder(folder_path: str, domain: str, user_id: str = None):
    """Ingest all documents from a specific folder"""
    logger.info(f"Ingesting from folder: {folder_path}")
    logger.info(f"Domain: {domain}")
    
    folder = Path(folder_path)
    if not folder.exists():
        logger.error(f"Folder does not exist: {folder_path}")
        return
    
    stats = BulkIngestionStats()
    
    for file_path in folder.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            stats.total_files += 1
            logger.info(f"\nProcessing: {file_path.name}")
            ingest_single_file(file_path, domain, stats, user_id)
    
    stats.print_summary()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Bulk ingest documents into Pinecone')
    parser.add_argument('--root', type=str, default='data', help='Root folder containing documents')
    parser.add_argument('--folder', type=str, help='Specific folder to ingest')
    parser.add_argument('--domain', type=str, choices=['travel', 'real_estate'], help='Domain (required if using --folder)')
    parser.add_argument('--user-id', type=str, help='User ID for document tagging')
    parser.add_argument('--batch-size', type=int, default=10, help='Progress update frequency')
    
    args = parser.parse_args()
    
    if args.folder:
        if not args.domain:
            logger.error("--domain is required when using --folder")
            sys.exit(1)
        ingest_specific_folder(args.folder, args.domain, args.user_id)
    else:
        ingest_by_category(args.root, args.user_id, args.batch_size)
