"""
Ingest the 3 travel industry PDF reports into Pinecone
"""
import sys
from pathlib import Path
from app2 import ingest_document

def ingest_travel_pdfs():
    """Ingest the 3 travel PDF reports"""
    
    pdfs = [
        "amadeus-future-traveller-tribes-2030-report.pdf",
        "The-Travel-Industrys-New-Trip-Final.pdf",
        "WEF_Travel_and_Tourism_at_a_Turning_Point_2025.pdf"
    ]
    
    print("\n" + "="*70)
    print("INGESTING TRAVEL INDUSTRY PDF REPORTS")
    print("="*70)
    
    success_count = 0
    failed = []
    
    for pdf_file in pdfs:
        try:
            print(f"\n📄 Processing: {pdf_file}")
            
            # Read file
            file_path = Path(pdf_file)
            if not file_path.exists():
                print(f"   ❌ File not found: {pdf_file}")
                failed.append((pdf_file, "File not found"))
                continue
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Ingest into Pinecone
            result = ingest_document(
                file_content=file_content,
                filename=pdf_file,
                domain="travel",
                user_id=None
            )
            
            print(f"   ✅ SUCCESS: {result['chunks_created']} chunks created")
            print(f"   ⏱️  Processing time: {result['processing_time']:.2f}s")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ FAILED: {str(e)}")
            failed.append((pdf_file, str(e)))
    
    # Summary
    print("\n" + "="*70)
    print("📊 INGESTION SUMMARY")
    print("="*70)
    print(f"Total PDFs: {len(pdfs)}")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {len(failed)}")
    
    if failed:
        print("\n❌ FAILED FILES:")
        for filename, error in failed:
            print(f"   - {filename}: {error}")
    
    if success_count > 0:
        print("\n🎉 PDF reports successfully ingested!")
        print("\n📝 Now you can query:")
        print("   - 'What are the future traveller tribes for 2030?'")
        print("   - 'Compare the travel industry reports'")
        print("   - 'What does WEF say about travel and tourism?'")
    
    print("="*70)

if __name__ == "__main__":
    ingest_travel_pdfs()
