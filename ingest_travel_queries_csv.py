# ingest_travel_queries_csv.py
"""
Script to ingest travel queries from CSV into Pinecone vector database
For use with RAG system for travel domain
"""

import pandas as pd
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
from tqdm import tqdm
import time

# Load environment variables
load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Get or create index
index_name = "documents-index"

# Check if index exists, if not create it
existing_indexes = [index_info['name'] for index_info in pc.list_indexes()]
print(f"Existing indexes: {existing_indexes}")

if index_name not in existing_indexes:
    print(f"Creating index '{index_name}'...")
    from pinecone import ServerlessSpec
    
    pc.create_index(
        name=index_name,
        dimension=384,  # all-MiniLM-L6-v2 produces 384-dimensional embeddings
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )
    print(f"Index '{index_name}' created successfully!")
    # Wait for index to be ready
    import time
    time.sleep(5)
else:
    print(f"Using existing index '{index_name}'")

index = pc.Index(index_name)

# Initialize embedding model
print("Loading embedding model...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def process_travel_queries_csv(csv_file_path, batch_size=100):
    """
    Process travel queries CSV and upload to Pinecone
    
    Args:
        csv_file_path: Path to the CSV file
        batch_size: Number of records to process at once
    """
    
    print(f"Reading CSV file: {csv_file_path}")
    
    # Read CSV
    df = pd.read_csv(csv_file_path)
    
    print(f"Total queries found: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nFirst few rows:")
    print(df.head())
    
    # Prepare vectors for upload
    vectors = []
    
    print("\nGenerating embeddings and preparing vectors...")
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing queries"):
        query_id = row['id']
        intent = row['intent']
        query_text = row['query']
        
        # Generate embedding for the query
        embedding = embedder.encode(query_text).tolist()
        
        # Create vector with metadata
        vector = {
            "id": f"travel_query_{query_id}",
            "values": embedding,
            "metadata": {
                "text": query_text,
                "intent": intent,
                "query_id": int(query_id),
                "domain": "travel",
                "source": "travel_queries_dataset",
                "type": "query"
            }
        }
        
        vectors.append(vector)
        
        # Upload in batches
        if len(vectors) >= batch_size:
            print(f"\nUploading batch of {len(vectors)} vectors...")
            index.upsert(vectors=vectors)
            vectors = []
            time.sleep(0.5)  # Small delay to avoid rate limits
    
    # Upload remaining vectors
    if vectors:
        print(f"\nUploading final batch of {len(vectors)} vectors...")
        index.upsert(vectors=vectors)
    
    print("\n✅ All queries uploaded successfully!")
    
    # Get index statistics
    stats = index.describe_index_stats()
    print(f"\nPinecone Index Statistics:")
    print(f"Total vectors: {stats['total_vector_count']}")
    print(f"Dimension: {stats['dimension']}")
    
    return df

def verify_upload(sample_queries=5):
    """Verify that queries were uploaded correctly"""
    
    print(f"\n🔍 Verifying upload with {sample_queries} sample queries...")
    
    # Test queries
    test_queries = [
        "best hotels in Paris",
        "visa requirements for Tokyo",
        "flight deals to Dubai",
        "weather in Bangkok",
        "things to do in Sydney"
    ]
    
    for test_query in test_queries[:sample_queries]:
        print(f"\nQuery: {test_query}")
        
        # Generate embedding
        query_embedding = embedder.encode(test_query).tolist()
        
        # Search
        results = index.query(
            vector=query_embedding,
            top_k=3,
            include_metadata=True,
            filter={"domain": "travel"}
        )
        
        print("Top matches:")
        for match in results['matches']:
            print(f"  - {match['metadata']['text']} (intent: {match['metadata']['intent']}, score: {match['score']:.3f})")

def analyze_query_intents(df):
    """Analyze the distribution of query intents"""
    
    print("\n📊 Query Intent Analysis:")
    print("="*50)
    
    intent_counts = df['intent'].value_counts()
    
    print(f"\nTotal unique intents: {len(intent_counts)}")
    print(f"\nTop 10 intents:")
    print(intent_counts.head(10))
    
    print(f"\nIntent distribution:")
    for intent, count in intent_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  {intent}: {count} queries ({percentage:.1f}%)")

def create_intent_summary():
    """Create a summary document for each intent type"""
    
    intents_info = {
        "visa_info": "Queries about visa requirements, applications, and travel documentation",
        "travel_tips": "Queries about travel advice, safety, packing, and local transport",
        "destination_info": "Queries about destinations, attractions, and best times to visit",
        "weather": "Queries about weather conditions and seasons",
        "hotel_search": "Queries about accommodation options",
        "flight_search": "Queries about flights, airlines, and travel routes",
        "itinerary": "Queries about trip planning and itineraries"
    }
    
    print("\n📝 Creating intent summary documents...")
    
    vectors = []
    for intent, description in intents_info.items():
        # Create a comprehensive text for embedding
        text = f"{intent}: {description}"
        embedding = embedder.encode(text).tolist()
        
        vector = {
            "id": f"intent_summary_{intent}",
            "values": embedding,
            "metadata": {
                "text": description,
                "intent": intent,
                "domain": "travel",
                "source": "intent_summary",
                "type": "intent_metadata"
            }
        }
        vectors.append(vector)
    
    # Upload intent summaries
    index.upsert(vectors=vectors)
    print(f"✅ Uploaded {len(vectors)} intent summary documents")

# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    print("="*60)
    print("Travel Queries CSV to Pinecone Ingestion")
    print("="*60)
    
    # Path to your CSV file
    csv_file = "travel_queries_global_5000.csv"
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"❌ Error: CSV file not found at {csv_file}")
        print("Please make sure the file is in the same directory as this script")
        exit(1)
    
    try:
        # Process and upload queries
        df = process_travel_queries_csv(csv_file, batch_size=100)
        
        # Analyze intents
        analyze_query_intents(df)
        
        # Create intent summaries
        create_intent_summary()
        
        # Verify upload
        verify_upload(sample_queries=5)
        
        print("\n" + "="*60)
        print("✅ INGESTION COMPLETE!")
        print("="*60)
        print("\nYou can now use these queries with your RAG system!")
        print("Example API call:")
        print("""
curl -X POST "http://localhost:8000/query" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "best hotels in Paris",
    "domain": "travel",
    "include_web": true,
    "top_k": 5
  }'
        """)
        
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()