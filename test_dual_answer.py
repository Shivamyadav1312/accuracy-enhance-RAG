"""
Quick test script for dual answer functionality
"""
import requests
import json

API_BASE_URL = "http://localhost:8000"

def test_dual_answer():
    """Test the dual answer endpoint"""
    
    print("\n" + "="*70)
    print("TESTING DUAL ANSWER SYSTEM")
    print("="*70)
    
    # Test query
    query = "What are the future traveller tribes for 2030?"
    user_id = "test_user_123"
    
    print(f"\n📝 Query: {query}")
    print(f"👤 User ID: {user_id}")
    
    # Make request
    payload = {
        "query": query,
        "user_id": user_id,
        "domain": None,
        "detect_intent": True,
        "detect_domain": True,
        "include_web": False,
        "top_k": 5,
        "llm_provider": "together",
        "include_reports": True
    }
    
    print("\n🔄 Sending request to /query-dual...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/query-dual",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n✅ SUCCESS!")
            print("="*70)
            
            # Display results
            print(f"\n🎯 Domain: {result.get('domain', 'N/A')}")
            print(f"🎯 Intent: {result.get('intent', 'N/A')}")
            print(f"⏱️  Processing Time: {result.get('processing_time', 0):.2f}s")
            
            print(f"\n📊 Statistics:")
            print(f"   User Documents Found: {result.get('user_documents_found', 0)}")
            print(f"   General Sources Found: {result.get('general_sources_found', 0)}")
            print(f"   Has User Documents: {result.get('has_user_documents', False)}")
            
            print("\n" + "="*70)
            print("📄 DOCUMENT-SPECIFIC ANSWER")
            print("="*70)
            print(result.get('document_answer', 'No answer'))
            
            print("\n" + "="*70)
            print("🌍 GENERALIZED ANSWER")
            print("="*70)
            print(result.get('general_answer', 'No answer'))
            
            # Show sources
            print("\n" + "="*70)
            print("📚 SOURCES")
            print("="*70)
            
            user_sources = result.get('user_sources', [])
            if user_sources:
                print(f"\n📄 User Document Sources ({len(user_sources)}):")
                for i, src in enumerate(user_sources, 1):
                    print(f"   {i}. {src.get('source', 'Unknown')} (score: {src.get('score', 0):.3f})")
            else:
                print("\n📄 No user document sources")
            
            general_sources = result.get('general_sources', [])
            if general_sources:
                print(f"\n🌍 General Knowledge Sources ({len(general_sources)}):")
                for i, src in enumerate(general_sources, 1):
                    print(f"   {i}. {src.get('source', 'Unknown')} (score: {src.get('score', 0):.3f})")
            else:
                print("\n🌍 No general knowledge sources")
            
            print("\n" + "="*70)
            print("✅ TEST COMPLETED SUCCESSFULLY")
            print("="*70)
            
            return True
            
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server")
        print("Make sure the server is running: python app2.py")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

def test_health():
    """Test if server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print("⚠️  Server responded but not healthy")
            return False
    except:
        print("❌ Server is not running")
        print("Start it with: python app2.py")
        return False

if __name__ == "__main__":
    print("\n🔍 Checking server health...")
    if test_health():
        print("\n🚀 Running dual answer test...")
        test_dual_answer()
    else:
        print("\n⚠️  Please start the server first:")
        print("   python app2.py")
