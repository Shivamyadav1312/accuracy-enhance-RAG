"""
Quick script to check what data is in Pinecone
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("documents-index")

# Get index stats
stats = index.describe_index_stats()

print("=" * 60)
print("PINECONE INDEX STATISTICS")
print("=" * 60)
print(f"Total vectors: {stats.get('total_vector_count', 0)}")
print(f"Dimension: {stats.get('dimension', 0)}")
print(f"Index fullness: {stats.get('index_fullness', 0)}")
print()

# Try to query for travel queries
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer('all-MiniLM-L6-v2')

test_query = "best hotels in Paris"
query_embedding = embedder.encode(test_query).tolist()

print("=" * 60)
print("TEST QUERY: 'best hotels in Paris'")
print("=" * 60)

# Query with type filter
print("\n1. Querying with type='query' filter...")
results = index.query(
    vector=query_embedding,
    top_k=5,
    include_metadata=True,
    filter={"type": "query"}
)

print(f"   Results found: {len(results.get('matches', []))}")
if results.get('matches'):
    for i, match in enumerate(results['matches'][:3], 1):
        print(f"   {i}. {match['metadata'].get('query', 'N/A')}")
        print(f"      Intent: {match['metadata'].get('intent', 'N/A')}")
        print(f"      Score: {match['score']:.3f}")

# Query with domain filter
print("\n2. Querying with domain='travel' filter...")
results = index.query(
    vector=query_embedding,
    top_k=5,
    include_metadata=True,
    filter={"domain": "travel"}
)

print(f"   Results found: {len(results.get('matches', []))}")
if results.get('matches'):
    for i, match in enumerate(results['matches'][:3], 1):
        metadata = match['metadata']
        print(f"   {i}. Type: {metadata.get('type', 'N/A')}")
        print(f"      Query: {metadata.get('query', metadata.get('text', 'N/A')[:50])}")
        print(f"      Intent: {metadata.get('intent', 'N/A')}")
        print(f"      Score: {match['score']:.3f}")

# Query without filter
print("\n3. Querying without any filter...")
results = index.query(
    vector=query_embedding,
    top_k=5,
    include_metadata=True
)

print(f"   Results found: {len(results.get('matches', []))}")
if results.get('matches'):
    for i, match in enumerate(results['matches'][:3], 1):
        metadata = match['metadata']
        print(f"   {i}. Type: {metadata.get('type', 'N/A')}")
        print(f"      Has 'query' field: {'query' in metadata}")
        print(f"      Has 'intent' field: {'intent' in metadata}")
        print(f"      Score: {match['score']:.3f}")

print("\n" + "=" * 60)
print("DIAGNOSIS")
print("=" * 60)

if stats.get('total_vector_count', 0) == 0:
    print("❌ No vectors in index! Run: python ingest_travel_queries_csv.py")
elif len(results.get('matches', [])) == 0:
    print("❌ No travel queries found! Run: python ingest_travel_queries_csv.py")
else:
    print("✅ Travel queries are present in the index")
    
    # Check if they have the right metadata
    has_type = any(m['metadata'].get('type') == 'query' for m in results['matches'])
    has_intent = any('intent' in m['metadata'] for m in results['matches'])
    
    if not has_type:
        print("⚠️  Queries don't have 'type' metadata field")
    if not has_intent:
        print("⚠️  Queries don't have 'intent' metadata field")
    
    if has_type and has_intent:
        print("✅ Metadata structure looks correct")

print("=" * 60)
