"""
Interactive query tool for Enhanced RAG API
Ask questions and see full responses with formatting
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def print_separator(char="=", length=80):
    print(char * length)

def print_section(title: str):
    print(f"\n{title}")
    print_separator("-")

def format_answer(data: Dict[Any, Any]):
    """Format and display the query response"""
    
    print_separator()
    print("📊 QUERY RESULTS")
    print_separator()
    
    # Basic Info
    print(f"\n✨ Intent: {data.get('intent', 'N/A')}")
    print(f"⏱️  Processing Time: {data.get('processing_time', 0):.2f}s")
    
    # Similar Queries
    similar = data.get('similar_queries', [])
    if similar:
        print_section("🔗 SIMILAR QUERIES")
        for i, sq in enumerate(similar, 1):
            print(f"\n{i}. {sq['query']}")
            print(f"   📌 Intent: {sq['intent']}")
            print(f"   📊 Similarity: {sq['similarity']:.1%}")
    
    # Sources
    sources = data.get('sources', [])
    if sources:
        print_section(f"📚 KNOWLEDGE BASE SOURCES ({len(sources)} found)")
        for i, source in enumerate(sources, 1):
            print(f"\n[{i}] Relevance Score: {source.get('score', 0):.3f}")
            text = source.get('text', '')
            # Show first 200 chars
            if len(text) > 200:
                print(f"    {text[:200]}...")
            else:
                print(f"    {text}")
    
    # Web Results
    web_results = data.get('web_results', [])
    if web_results:
        print_section(f"🌐 WEB SEARCH RESULTS ({len(web_results)} found)")
        for i, result in enumerate(web_results, 1):
            print(f"\n[{i}] {result.get('title', 'N/A')}")
            print(f"    {result.get('snippet', 'N/A')}")
            print(f"    🔗 {result.get('url', 'N/A')}")
    
    # Answer
    answer = data.get('answer', '')
    print_section("💬 AI GENERATED ANSWER")
    print(f"\n{answer}\n")
    
    print_separator()

def query_api(query: str, include_web: bool = True, top_k: int = 5):
    """Send query to API and display results"""
    
    print_separator()
    print(f"🔍 YOUR QUERY: {query}")
    print_separator()
    print(f"\n⏳ Processing (web search: {'ON' if include_web else 'OFF'})...\n")
    
    payload = {
        "query": query,
        "domain": "travel",
        "detect_intent": True,
        "include_web": include_web,
        "top_k": top_k
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/query",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            format_answer(data)
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server!")
        print("   Make sure the server is running:")
        print("   python enhanced_rag_with_queries.py")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def interactive_mode():
    """Interactive query mode"""
    
    print("\n" + "="*80)
    print("🚀 ENHANCED RAG - INTERACTIVE QUERY MODE")
    print("="*80)
    print("\nCommands:")
    print("  - Type your query and press Enter")
    print("  - Type 'web on' or 'web off' to toggle web search")
    print("  - Type 'examples' to see example queries")
    print("  - Type 'quit' or 'exit' to quit")
    print("="*80 + "\n")
    
    web_search = True
    
    while True:
        try:
            user_input = input("\n💭 Your query: ").strip()
            
            if not user_input:
                continue
            
            # Commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            elif user_input.lower() == 'web on':
                web_search = True
                print("✅ Web search enabled")
                continue
            
            elif user_input.lower() == 'web off':
                web_search = False
                print("✅ Web search disabled")
                continue
            
            elif user_input.lower() == 'examples':
                print("\n📝 Example Queries:")
                print("  1. What's the weather like in Bangkok in July?")
                print("  2. How do I apply for a visa to Dubai?")
                print("  3. Best family hotels in Paris near Eiffel Tower")
                print("  4. Cheap flights from London to New York")
                print("  5. What are the top attractions in Tokyo?")
                continue
            
            # Process query
            query_api(user_input, include_web=web_search)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

def quick_test():
    """Run a few quick test queries"""
    
    print("\n" + "="*80)
    print("🧪 RUNNING QUICK TESTS")
    print("="*80)
    
    test_queries = [
        ("What's the weather like in Bangkok in July?", True),
        ("Best budget hotels in Tokyo", True),
        ("What are the top attractions in Paris?", False),
    ]
    
    for i, (query, web) in enumerate(test_queries, 1):
        print(f"\n\n{'='*80}")
        print(f"TEST {i}/{len(test_queries)}")
        print('='*80)
        query_api(query, include_web=web)
        
        if i < len(test_queries):
            input("\nPress Enter to continue to next test...")
    
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETED")
    print("="*80)

if __name__ == "__main__":
    import sys
    
    # Check if query provided as command line argument
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        query_api(query, include_web=True)
    else:
        # Show menu
        print("\n" + "="*80)
        print("🚀 ENHANCED RAG - QUERY TOOL")
        print("="*80)
        print("\nWhat would you like to do?")
        print("  1. Interactive mode (ask multiple questions)")
        print("  2. Quick test (run 3 example queries)")
        print("  3. Single query (provide query as argument)")
        print("="*80)
        
        choice = input("\nYour choice (1-3): ").strip()
        
        if choice == "1":
            interactive_mode()
        elif choice == "2":
            quick_test()
        elif choice == "3":
            query = input("\nEnter your query: ").strip()
            if query:
                query_api(query, include_web=True)
        else:
            print("Invalid choice. Starting interactive mode...")
            interactive_mode()
