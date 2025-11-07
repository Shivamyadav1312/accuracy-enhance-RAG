"""
Retry Failed Document Ingestion
Re-ingests only the documents that failed in the previous run
"""

import os
from pathlib import Path
from app2 import ingest_document
import time

# Failed documents from error log
failed_docs = [
    "downloaded_docs/real_estate/price_prediction/zillow_home_values.txt",
    "downloaded_docs/real_estate/price_prediction/zillow_inventory.txt",
    "downloaded_docs/real_estate/price_prediction/zillow_median_sale_price.txt"
]

print("="*80)
print("🔄 RETRY FAILED DOCUMENT INGESTION")
print("="*80)
print(f"Retrying {len(failed_docs)} failed documents\n")

success = 0
failed = 0

for doc_path in failed_docs:
    file_path = Path(doc_path)
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        failed += 1
        continue
    
    print(f"\n📄 Processing: {file_path.name}")
    print(f"   Size: {file_path.stat().st_size / 1024:.2f} KB")
    
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_content = content.encode('utf-8')
        
        # Ingest with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"   Attempt {attempt + 1}/{max_retries}...")
                result = ingest_document(file_content, file_path.name, 'real_estate', user_id=None)
                
                if result.get('status') == 'success':
                    chunks = result.get('chunks_created', 0)
                    print(f"   ✅ SUCCESS: {chunks} chunks created")
                    success += 1
                    break
                else:
                    print(f"   ⚠️ Non-success status: {result.get('message', 'Unknown')}")
                    if attempt < max_retries - 1:
                        time.sleep(5)  # Wait before retry
            
            except Exception as e:
                print(f"   ❌ Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"   Waiting 10 seconds before retry...")
                    time.sleep(10)
                else:
                    print(f"   ❌ All retries exhausted")
                    failed += 1
    
    except Exception as e:
        print(f"   ❌ Error reading file: {str(e)}")
        failed += 1

# Summary
print("\n" + "="*80)
print("📊 RETRY SUMMARY")
print("="*80)
print(f"Total Attempted: {len(failed_docs)}")
print(f"✅ Successful: {success}")
print(f"❌ Failed: {failed}")
print("="*80)

if success == len(failed_docs):
    print("\n🎉 All failed documents successfully ingested!")
    print(f"📊 Your database now has: 95 + {success} = {95 + success} documents")
elif success > 0:
    print(f"\n⚠️ Partial success: {success}/{len(failed_docs)} documents ingested")
    print(f"📊 Your database now has: 95 + {success} = {95 + success} documents")
else:
    print("\n❌ No documents were successfully ingested")
    print("Check your internet connection and Pinecone API key")
