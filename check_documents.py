"""
Check what documents are uploaded and test retrieval diversity
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

def check_user_documents(user_id="travel_analyst_001"):
    """Check what documents are uploaded for a user"""
    print("=" * 80)
    print(f"CHECKING DOCUMENTS FOR USER: {user_id}")
    print("=" * 80)
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/user-documents/{user_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            docs = result.get('documents', [])
            
            print(f"\n📚 Total documents: {len(docs)}")
            
            if docs:
                print("\nDocuments found:")
                for i, doc in enumerate(docs, 1):
                    print(f"\n{i}. {doc.get('filename', 'Unknown')}")
                    print(f"   Chunks: {doc.get('chunks', 0)}")
                    print(f"   Uploaded: {doc.get('timestamp', 'N/A')[:19]}")
                
                # Check for the 3 expected documents
                filenames = [doc.get('filename', '') for doc in docs]
                expected = [
                    'amadeus-future-traveller-tribes-2030-report.pdf',
                    'The-Travel-Industrys-New-Trip-Final.pdf',
                    'WEF_Travel_and_Tourism_at_a_Turning_Point_2025.pdf'
                ]
                
                print("\n" + "=" * 80)
                print("VERIFICATION:")
                for exp in expected:
                    if exp in filenames:
                        print(f"✅ {exp}")
                    else:
                        print(f"❌ {exp} - NOT FOUND")
                
                if len(docs) >= 3:
                    print("\n✅ All 3 documents are uploaded!")
                    return True
                else:
                    print(f"\n⚠️ Only {len(docs)} documents found. Need 3.")
                    return False
            else:
                print("\n❌ No documents found!")
                print("\n💡 Upload documents with:")
                print("   python upload_travel_reports.py")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_retrieval_diversity(user_id="travel_analyst_001"):
    """Test if retrieval gets chunks from all documents"""
    print("\n" + "=" * 80)
    print("TESTING RETRIEVAL DIVERSITY")
    print("=" * 80)
    
    query = "What is the similarity between them?"
    
    payload = {
        "query": query,
        "domain": "travel",
        "include_web": False,
        "top_k": 15,
        "detect_intent": True,
        "user_id": user_id
    }
    
    print(f"\nQuery: {query}")
    print(f"Top K: {payload['top_k']}")
    print(f"User ID: {user_id}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            sources = result.get('sources', [])
            
            print(f"\n📊 Retrieved {len(sources)} chunks")
            
            # Group by source
            by_source = {}
            for source in sources:
                src = source.get('source', 'Unknown')
                if src not in by_source:
                    by_source[src] = []
                by_source[src].append(source)
            
            print(f"\n📁 From {len(by_source)} different documents:")
            
            for src, chunks in by_source.items():
                print(f"\n  📄 {src}")
                print(f"     Chunks: {len(chunks)}")
                avg_score = sum(c.get('score', 0) for c in chunks) / len(chunks)
                print(f"     Avg Score: {avg_score:.3f}")
            
            # Check diversity
            print("\n" + "=" * 80)
            print("DIVERSITY CHECK:")
            
            if len(by_source) >= 3:
                print("✅ GOOD: Chunks retrieved from 3+ documents")
                print("   System will analyze multiple sources")
            elif len(by_source) == 2:
                print("⚠️ MODERATE: Only 2 documents retrieved")
                print("   Try increasing top_k to 20")
            else:
                print("❌ POOR: Only 1 document retrieved")
                print("   All chunks from same source!")
                print("\n💡 Solutions:")
                print("   1. Increase top_k to 20-25")
                print("   2. Check if all documents are uploaded")
                print("   3. Verify user_id matches")
            
            return len(by_source) >= 3
            
        else:
            print(f"❌ Query failed: {response.status_code}")
            print(response.text[:500])
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def check_backend():
    """Check if backend is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print("✅ Backend is running")
            print(f"   Model: {health.get('model', 'N/A')}")
            return True
        return False
    except:
        print("❌ Backend is not running")
        print("   Start it with: python app2.py")
        return False

if __name__ == "__main__":
    print("\n🔍 DOCUMENT & RETRIEVAL DIAGNOSTIC\n")
    
    # Check backend
    if not check_backend():
        exit(1)
    
    print()
    
    # Check documents
    docs_ok = check_user_documents()
    
    if not docs_ok:
        print("\n⚠️ Documents not properly uploaded!")
        print("\n💡 Run this first:")
        print("   python upload_travel_reports.py")
        exit(1)
    
    # Test retrieval
    retrieval_ok = test_retrieval_diversity()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if docs_ok and retrieval_ok:
        print("\n✅ Everything looks good!")
        print("   - All 3 documents uploaded")
        print("   - Retrieval is diverse (3+ sources)")
        print("\n🎉 Ready for analytical queries!")
    elif docs_ok and not retrieval_ok:
        print("\n⚠️ Documents uploaded but retrieval needs improvement")
        print("\n💡 Try:")
        print("   1. Increase top_k to 20-25")
        print("   2. Restart backend: python app2.py")
    else:
        print("\n❌ Issues detected")
        print("   Check the output above for details")
    
    print()
