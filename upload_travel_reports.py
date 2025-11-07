"""
Upload the three travel industry reports for analytical comparison
"""

import requests
import os
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def upload_document(file_path, user_id="travel_analyst_001", domain="travel"):
    """Upload a single document"""
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    filename = Path(file_path).name
    print(f"\n📤 Uploading: {filename}")
    print(f"   Size: {os.path.getsize(file_path) / 1024:.1f} KB")
    
    try:
        with open(file_path, 'rb') as f:
            files = {
                'file': (filename, f, 'application/pdf')
            }
            data = {
                'domain': domain,
                'user_id': user_id
            }
            
            response = requests.post(
                f"{API_BASE_URL}/upload",
                files=files,
                data=data,
                timeout=120  # PDFs can take time to process
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success!")
                print(f"   Chunks created: {result['chunks_created']}")
                print(f"   Processing time: {result['processing_time']:.2f}s")
                return True
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def upload_all_reports():
    """Upload all three travel industry reports"""
    
    print("=" * 80)
    print("UPLOADING TRAVEL INDUSTRY REPORTS FOR ANALYSIS")
    print("=" * 80)
    
    # Define the three reports
    reports = [
        "amadeus-future-traveller-tribes-2030-report.pdf",
        "The-Travel-Industrys-New-Trip-Final.pdf",
        "WEF_Travel_and_Tourism_at_a_Turning_Point_2025.pdf"
    ]
    
    user_id = "travel_analyst_001"
    print(f"\n👤 User ID: {user_id}")
    print(f"📁 Domain: travel")
    print(f"\n📚 Documents to upload: {len(reports)}")
    
    results = []
    for report in reports:
        file_path = os.path.join(os.path.dirname(__file__), report)
        success = upload_document(file_path, user_id)
        results.append((report, success))
    
    # Summary
    print("\n" + "=" * 80)
    print("UPLOAD SUMMARY")
    print("=" * 80)
    
    successful = sum(1 for _, success in results if success)
    print(f"\n✅ Successful: {successful}/{len(reports)}")
    
    if successful < len(reports):
        print(f"❌ Failed: {len(reports) - successful}")
        print("\nFailed uploads:")
        for report, success in results:
            if not success:
                print(f"  - {report}")
    
    if successful == len(reports):
        print("\n🎉 All documents uploaded successfully!")
        print("\n💡 Now you can ask analytical questions like:")
        print('   "What is the similarity between them?"')
        print('   "Compare the main themes across these documents"')
        print('   "What patterns emerge from these reports?"')
    
    return successful == len(reports)

def check_backend():
    """Check if backend is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print("✅ Backend is running")
            print(f"   Model: {health.get('model', 'N/A')}")
            print(f"   LLM Provider: {health['services'].get('llm_provider', 'N/A')}")
            return True
        return False
    except:
        print("❌ Backend is not running")
        print("   Start it with: python app2.py")
        return False

def verify_uploads(user_id="travel_analyst_001"):
    """Verify documents were uploaded"""
    print("\n" + "=" * 80)
    print("VERIFYING UPLOADED DOCUMENTS")
    print("=" * 80)
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/user-documents/{user_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            docs = result.get('documents', [])
            
            print(f"\n📚 Found {len(docs)} documents for user: {user_id}")
            
            if docs:
                print("\nDocuments:")
                for i, doc in enumerate(docs, 1):
                    print(f"\n{i}. {doc.get('filename', 'Unknown')}")
                    print(f"   Chunks: {doc.get('chunks', 0)}")
                    print(f"   Uploaded: {doc.get('timestamp', 'N/A')[:19]}")
                
                return True
            else:
                print("\n⚠️ No documents found. Upload may have failed.")
                return False
        else:
            print(f"❌ Failed to verify: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n🚀 TRAVEL REPORTS UPLOAD SCRIPT")
    print()
    
    # Check backend
    if not check_backend():
        print("\n⚠️ Please start the backend first:")
        print("   python app2.py")
        exit(1)
    
    print()
    input("Press Enter to start uploading documents...")
    print()
    
    # Upload all reports
    success = upload_all_reports()
    
    if success:
        # Verify uploads
        verify_uploads()
        
        print("\n" + "=" * 80)
        print("✅ READY FOR ANALYTICAL QUERIES!")
        print("=" * 80)
        print("\n🔍 Next steps:")
        print("   1. Run: python test_analytical_query.py")
        print("   2. Or use the Streamlit UI")
        print('   3. Ask: "What is the similarity between them?"')
        print()
        print("💡 Make sure to use the same user_id: travel_analyst_001")
        print()
    else:
        print("\n⚠️ Some uploads failed. Please check the errors above.")
