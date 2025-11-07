"""
Check what query parameters the UI is sending
"""

import requests

API_BASE_URL = "http://localhost:8000"

# Test with the exact same settings as UI should use
payload = {
    "query": "What is the similarity between them?",
    "domain": "travel",
    "detect_intent": True,
    "include_web": False,  # Make sure this is False
    "top_k": 15,
    "user_id": "travel_analyst_001"
}

print("=" * 80)
print("TESTING QUERY WITH UI SETTINGS")
print("=" * 80)
print("\nPayload being sent:")
print(f"  Query: {payload['query']}")
print(f"  User ID: {payload['user_id']}")
print(f"  Top K: {payload['top_k']}")
print(f"  Include Web: {payload['include_web']}")
print(f"  Domain: {payload['domain']}")
print()

try:
    response = requests.post(
        f"{API_BASE_URL}/query",
        json=payload,
        timeout=90
    )
    
    if response.status_code == 200:
        result = response.json()
        answer = result['answer']
        sources = result.get('sources', [])
        
        # Check sources
        unique_sources = list(set(s.get('source', 'Unknown') for s in sources))
        
        print("✅ SUCCESS!")
        print("=" * 80)
        print(f"\n📊 Retrieved {len(sources)} chunks from {len(unique_sources)} sources:")
        for src in unique_sources:
            count = sum(1 for s in sources if s.get('source') == src)
            print(f"  - {src}: {count} chunks")
        
        print("\n" + "=" * 80)
        print("FIRST 1000 CHARACTERS OF RESPONSE:")
        print("=" * 80)
        print(answer[:1000])
        print("\n... (truncated)")
        
        # Check mentions
        print("\n" + "=" * 80)
        print("SOURCE MENTIONS:")
        print("=" * 80)
        
        answer_lower = answer.lower()
        amadeus = 'amadeus' in answer_lower
        accenture = 'accenture' in answer_lower or 'travel-industrys' in answer_lower
        wef = 'wef' in answer_lower or 'world economic' in answer_lower
        
        print(f"  {'✅' if amadeus else '❌'} Amadeus")
        print(f"  {'✅' if accenture else '❌'} Accenture/Travel Industry")
        print(f"  {'✅' if wef else '❌'} WEF")
        
        if amadeus and accenture and wef:
            print("\n🎉 PERFECT! All 3 sources mentioned")
        elif amadeus and wef:
            print("\n✅ GOOD! Amadeus and WEF mentioned")
            print("   (Accenture file is 'Travel-Industrys-New-Trip-Final.pdf')")
        else:
            print("\n⚠️ Check if all sources are being analyzed")
        
    else:
        print(f"❌ ERROR: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

print("\n" + "=" * 80)
