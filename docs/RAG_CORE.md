# RAG Core Components Documentation

## Overview

The RAG (Retrieval-Augmented Generation) core provides the foundation for document-based question answering. It consists of three main components:

1. **Embeddings**: Convert text to vector representations
2. **Vector Store**: Store and search embeddings efficiently
3. **RAG Chain**: Orchestrate retrieval and generation

## Architecture

```
Document Upload
     ↓
DocumentLoader (Extract text)
     ↓
EmbeddingManager (Chunk + Embed)
     ↓
VectorStoreManager (Index)
     ↓
[FAISS/Pinecone Storage]

Query Processing
     ↓
EmbeddingManager (Embed query)
     ↓
VectorStoreManager (Similarity search)
     ↓
RAGChain (Retrieve + Format + Generate)
     ↓
Answer
```

## Embeddings

**File**: [src/embeddings.py](../src/embeddings.py)

Handles text chunking and conversion to vector embeddings.

### EmbeddingManager

```python
class EmbeddingManager:
    text_splitter: RecursiveCharacterTextSplitter
    embedding_model: Embeddings  # HuggingFace or Google
```

### Supported Providers

#### 1. HuggingFace (Default - Free)

```python
# In .env
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Model details:
# - Size: ~80MB download
# - Dimension: 384
# - Speed: ~50 texts/second on CPU
# - Cost: FREE
# - Quality: Good for general purpose
```

**Popular Models**:
- `all-MiniLM-L6-v2`: Fast, small, good quality (default)
- `all-mpnet-base-v2`: Slower, larger, better quality
- `multi-qa-mpnet-base-dot-v1`: Optimized for Q&A

#### 2. Google Embeddings (Paid)

```python
# In .env
EMBEDDING_PROVIDER=google
EMBEDDING_MODEL=models/embedding-001
GOOGLE_API_KEY=your_key_here

# Model details:
# - Dimension: 768
# - Speed: Fast (API)
# - Cost: Pay per 1k tokens
# - Quality: Excellent
```

### Text Chunking

Documents are split into smaller chunks for better retrieval granularity.

```python
# Configuration
CHUNK_SIZE=800          # Characters per chunk
CHUNK_OVERLAP=100       # Overlap between chunks

# Chunking strategy
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", " ", ""]  # Try paragraph, line, word, char
)
```

**Why Chunking?**
- LLMs have token limits (~4k-8k for most models)
- Smaller chunks = more precise retrieval
- Overlap preserves context across boundaries

**Example**:
```
Document: 2000 characters

Without chunking:
└─ [Full document] → 1 embedding → coarse-grained search

With chunking (800 chars, 100 overlap):
├─ [Chunk 1: 0-800]
├─ [Chunk 2: 700-1500]   ← 100 char overlap
└─ [Chunk 3: 1400-2000]  ← 100 char overlap
→ 3 embeddings → fine-grained search
```

### Usage

```python
from src.embeddings import EmbeddingManager

# Initialize
embedding_mgr = EmbeddingManager()

# Chunk documents
documents = [
    {
        'content': "Machine learning is...",
        'metadata': {'source': 'ml_basics.pdf', 'topic': 'ML'}
    }
]

chunks = embedding_mgr.chunk_documents(documents)
# Output: List[Document] with metadata['chunk_id']

# Generate embeddings for documents
texts = [chunk.page_content for chunk in chunks]
embeddings = embedding_mgr.generate_embeddings(texts)
# Returns: List[List[float]] - 384-dim vectors

# Generate embedding for query
query_embedding = embedding_mgr.generate_query_embedding("What is ML?")
# Returns: List[float] - 384-dim vector
```

### Metadata Tracking

Each chunk includes metadata for provenance:

```python
chunk.metadata = {
    'source': 'ml_basics.pdf',      # Original file
    'topic': 'Machine Learning',     # Category
    'chunk_id': 0,                   # Position in document
    'upload_date': '2026-02-04',     # When indexed
    # ... custom fields
}
```

## Vector Store

**File**: [src/vector_store.py](../src/vector_store.py)

Manages vector storage and similarity search.

### VectorStoreManager

```python
class VectorStoreManager:
    embedding_manager: EmbeddingManager
    vector_store: FAISS  # or Pinecone
    store_path: Path     # data/vector_store/
```

### Supported Backends

#### 1. FAISS (Default - Local)

**Facebook AI Similarity Search** - Fast local vector database

```python
# Automatic in-memory index
# Saved to: data/vector_store/

# Pros:
# - FREE
# - Fast (millisecond search)
# - No API required
# - Works offline

# Cons:
# - Limited to single machine
# - Must fit in memory (~1GB per 100k docs)
# - No cloud sync
```

#### 2. Pinecone (Optional - Cloud)

```python
# In .env
USE_PINECONE=true
PINECONE_API_KEY=your_key_here
PINECONE_INDEX_NAME=rag-agent
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1

# Pros:
# - Scalable to billions of vectors
# - Serverless (no infrastructure)
# - Real-time updates
# - Multi-region

# Cons:
# - Costs money
# - Requires internet
# - API latency
```

**See**: [src/vector_store_pinecone.py](../src/vector_store_pinecone.py) for Pinecone implementation.

### Creating Vector Store

```python
from src.vector_store import VectorStoreManager
from src.embeddings import EmbeddingManager

# Initialize
embedding_mgr = EmbeddingManager()
vector_store_mgr = VectorStoreManager(embedding_mgr)

# Create from chunks
chunks = embedding_mgr.chunk_documents(documents)

vector_store = vector_store_mgr.create_vector_store(
    chunks,
    batch_size=3,   # Process 3 at a time
    delay=2.0       # 2s delay between batches (rate limiting)
)

# Save to disk
vector_store_mgr.save_vector_store()
# → Saved to data/vector_store/
```

**Rate Limiting**: Prevents overwhelming embedding API with batching and delays.

### Searching Vector Store

```python
# Basic search (returns documents)
results = vector_store_mgr.similarity_search(
    query="What is machine learning?",
    k=3  # Top 3 results
)

for doc in results:
    print(doc.page_content)
    print(doc.metadata)

# Search with scores
results_with_scores = vector_store_mgr.similarity_search_with_score(
    query="What is machine learning?",
    k=3
)

for doc, score in results_with_scores:
    print(f"Score: {score:.4f}")
    print(f"Content: {doc.page_content[:100]}...")
    print(f"Source: {doc.metadata['source']}")
```

**Similarity Scores**:
- FAISS: Lower is better (L2 distance)
- Typical range: 0.3 (very similar) to 2.0 (dissimilar)
- Threshold: < 1.0 for relevant results

### Loading Existing Store

```python
# Automatically loads on init if exists
vector_store_mgr = VectorStoreManager(embedding_mgr)

# Or explicitly load
vector_store_mgr.load_vector_store()
```

### Adding New Documents

```python
# Chunk new documents
new_chunks = embedding_mgr.chunk_documents(new_documents)

# Add to existing store
vector_store_mgr.vector_store.add_documents(new_chunks)

# Save updated store
vector_store_mgr.save_vector_store()
```

## RAG Chain

**File**: [src/rag_chain.py](../src/rag_chain.py)

Orchestrates the complete RAG pipeline: retrieve → format → generate.

### RAGChain

```python
class RAGChain:
    vector_store_manager: VectorStoreManager
    llm: ChatLLM                        # Groq or Google
    prompt_template: ChatPromptTemplate
    observability: ObservabilityManager
```

### RAG Pipeline Steps

#### 1. Retrieve Context

```python
def retrieve_context(self, query: str, k: int = 3) -> List[Document]:
    """
    Retrieve relevant documents for the query.

    Steps:
    1. Generate query embedding
    2. Search vector store
    3. Return top-k similar documents
    """
    results = self.vector_store_manager.similarity_search_with_score(query, k=k)
    documents = [doc for doc, score in results]
    return documents
```

#### 2. Format Context

```python
def format_context(self, documents: List[Document]) -> str:
    """
    Format documents into LLM-readable context.

    Output format:
    [Source 1: filename.pdf (Topic: ML)]
    Chunk content here...

    ---

    [Source 2: article.txt (Topic: AI)]
    Another chunk here...
    """
    context_parts = []
    for i, doc in enumerate(documents, 1):
        source = doc.metadata.get("source", "unknown")
        topic = doc.metadata.get("topic", "unknown")
        content = doc.page_content.strip()

        context_parts.append(
            f"[Source {i}: {source} (Topic: {topic})]\n{content}"
        )

    return "\n\n---\n\n".join(context_parts)
```

#### 3. Generate Answer

```python
def generate_answer(self, query: str, context: str) -> str:
    """
    Generate answer using LLM with retrieved context.

    Prompt structure:
    [System]: You are a helpful AI assistant...
              Use ONLY the provided context.
              Context: [retrieved documents]
    [Human]: [user query]
    """
    messages = self.prompt_template.format_messages(
        context=context,
        question=query
    )

    response = self.llm.invoke(messages)
    return response.content
```

### Complete RAG Query

```python
# Initialize RAG chain
rag_chain = RAGChain(vector_store_manager)

# Ask question
result = rag_chain.ask(
    question="What is a transformer architecture?",
    top_k=3  # Retrieve top 3 documents
)

# Result structure:
{
    'question': 'What is a transformer architecture?',
    'answer': 'A transformer architecture is...',
    'context': [Document(...), Document(...), Document(...)],
    'sources': [
        {
            'source': 'transformers.pdf',
            'topic': 'Deep Learning',
            'content': 'Preview of content...'
        },
        # ... more sources
    ]
}

# Display formatted result
rag_chain.display_result(result)
```

### Prompt Template

```python
prompt_template = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful AI assistant that answers questions based on the provided context.

Instructions:
- Use ONLY the information from the context below to answer the question
- If the context doesn't contain relevant information, say "I don't have enough information to answer this question based on the provided context."
- Be concise and clear in your answers
- If you use information from the context, mention which source it came from
- Do not make up information or use external knowledge

Context:
{context}"""),
    ("human", "{question}")
])
```

**Why this prompt?**
- **Grounding**: Forces LLM to use only provided context
- **Transparency**: Cites sources
- **Honesty**: Admits when information is missing
- **Prevents hallucination**: Explicit "don't make up" instruction

## Document Management

**File**: [src/document_manager.py](../src/document_manager.py)

Higher-level interface for document lifecycle management.

### DocumentManager

Wraps VectorStoreManager with additional features:
- Document metadata tracking
- Batch indexing
- Document updates/deletes
- Statistics

```python
from src.document_manager import DocumentManager

# Initialize
doc_manager = DocumentManager(
    embedding_manager=embedding_mgr,
    data_dir="data/documents"
)

# Index documents
doc_manager.index_documents([
    {
        'content': "...",
        'metadata': {'source': 'file.pdf', 'topic': 'ML'}
    }
])

# Search
results = doc_manager.search("machine learning", top_k=5)

# Get statistics
stats = doc_manager.get_stats()
# Returns: {'total_documents': 42, 'total_chunks': 156, ...}
```

## Document Loaders

**File**: [src/document_loader.py](../src/document_loader.py)

Extract text from various file formats.

### Supported Formats

```python
from src.document_loader import DocumentLoader

loader = DocumentLoader()

# PDF files
docs = loader.load_pdf("path/to/document.pdf")

# Web URLs
docs = loader.load_url("https://example.com/article")

# Plain text
docs = loader.load_text("path/to/notes.txt")

# Markdown
docs = loader.load_markdown("path/to/README.md")
```

### Document Structure

```python
{
    'content': "Full text content...",
    'metadata': {
        'source': 'document.pdf',
        'source_type': 'pdf',
        'page_count': 10,
        'upload_date': '2026-02-04',
        'file_size': 1024000,
        # ... format-specific metadata
    }
}
```

## Configuration

**RAG Settings** (from `.env`):

```bash
# Embeddings
EMBEDDING_PROVIDER=huggingface           # or google
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Chunking
CHUNK_SIZE=800                           # Characters per chunk
CHUNK_OVERLAP=100                        # Overlap between chunks

# Retrieval
TOP_K_RESULTS=3                          # Documents to retrieve

# Vector Store
USE_PINECONE=false                       # Use Pinecone (cloud)
# PINECONE_API_KEY=your_key_here
# PINECONE_INDEX_NAME=rag-agent

# LLM for generation
LLM_PROVIDER=groq                        # or google
GROQ_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1024
```

## Indexing Documents

### Command-Line Indexing

```bash
# Re-index all documents
python reindex_documents.py

# Index specific directory
python reindex_documents.py --path data/my_docs/

# With custom batch size
python reindex_documents.py --batch-size 5 --delay 1.0
```

### Programmatic Indexing

```python
from src.embeddings import EmbeddingManager
from src.vector_store import VectorStoreManager
from src.document_loader import DocumentLoader

# 1. Load documents
loader = DocumentLoader()
documents = loader.load_directory("data/documents/")

# 2. Chunk and embed
embedding_mgr = EmbeddingManager()
chunks = embedding_mgr.chunk_documents(documents)

# 3. Create vector store
vector_store_mgr = VectorStoreManager(embedding_mgr)
vector_store = vector_store_mgr.create_vector_store(
    chunks,
    batch_size=3,
    delay=2.0
)

# 4. Save to disk
vector_store_mgr.save_vector_store()

print(f"✅ Indexed {len(documents)} documents → {len(chunks)} chunks")
```

## Performance Optimization

### Embedding Generation

```python
# Batch processing (faster than one-by-one)
texts = [chunk.page_content for chunk in chunks]
embeddings = embedding_mgr.generate_embeddings(texts)  # Batch

# vs. (slow)
embeddings = [embedding_mgr.generate_query_embedding(t) for t in texts]
```

### Vector Store Search

```python
# Use appropriate k value
results = vector_store_mgr.similarity_search(query, k=3)  # Fast
results = vector_store_mgr.similarity_search(query, k=50) # Slower

# Cache frequent queries
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query: str):
    return vector_store_mgr.similarity_search(query, k=3)
```

### Chunking Strategy

```python
# Smaller chunks = more precise but more embeddings
CHUNK_SIZE=500, CHUNK_OVERLAP=50  # Fine-grained

# Larger chunks = less precise but fewer embeddings
CHUNK_SIZE=1500, CHUNK_OVERLAP=200  # Coarse-grained

# Balanced (default)
CHUNK_SIZE=800, CHUNK_OVERLAP=100
```

## Best Practices

### 1. Document Metadata

Always include rich metadata:

```python
{
    'content': "...",
    'metadata': {
        'source': 'ml_paper.pdf',
        'topic': 'Machine Learning',
        'author': 'John Doe',
        'date': '2025-01-15',
        'page': 3,
        'section': 'Results',
        # Custom fields as needed
    }
}
```

### 2. Chunking for Long Documents

```python
# For long documents (>10 pages), use:
CHUNK_SIZE=1000
CHUNK_OVERLAP=200  # Larger overlap preserves context
```

### 3. Query Optimization

```python
# Expand queries for better retrieval
query = "ML algorithms"

# Better: Add context
expanded_query = "machine learning algorithms classification regression"

results = rag_chain.ask(expanded_query)
```

### 4. Source Citation

Always cite sources in answers:

```python
# The prompt template already does this, but verify:
answer = rag_chain.ask(query)
print(answer['sources'])  # Check sources are included
```

### 5. Periodic Re-indexing

```bash
# Re-index when:
# - Embedding model changes
# - Chunk settings change
# - New documents added

python reindex_documents.py
```

## Troubleshooting

### No relevant results found

**Symptom**: `similarity_search` returns empty or irrelevant results

**Solutions**:
1. Check if vector store is loaded: `vector_store_mgr.vector_store is not None`
2. Verify documents are indexed: `python reindex_documents.py`
3. Try different query phrasing
4. Increase `k` parameter: `k=10` instead of `k=3`
5. Check embedding model is working: Test with `generate_query_embedding()`

### Slow indexing

**Symptom**: Creating vector store takes very long

**Solutions**:
1. Reduce batch size: `batch_size=1` for free APIs
2. Increase delay: `delay=3.0` or more
3. Use local embeddings: `EMBEDDING_PROVIDER=huggingface`
4. Check network connectivity for cloud embeddings

### Out of memory

**Symptom**: FAISS indexing fails with memory error

**Solutions**:
1. Reduce number of documents
2. Use Pinecone (cloud) instead of FAISS
3. Increase system RAM
4. Process in smaller batches and merge indices

### Poor answer quality

**Symptom**: LLM gives wrong or incomplete answers

**Solutions**:
1. Increase `TOP_K_RESULTS`: Retrieve more context
2. Check retrieved documents: Print `context` to verify relevance
3. Improve document metadata for better filtering
4. Adjust chunk size for better granularity
5. Use better embedding model: `all-mpnet-base-v2`
6. Lower LLM temperature: `LLM_TEMPERATURE=0.3` for more deterministic

## Monitoring & Observability

The RAG system includes built-in observability:

```python
from src.observability import get_observability

obs = get_observability()

# Metrics are automatically tracked:
# - retrieval_duration_ms: Time to search vector store
# - generation_duration_ms: Time for LLM to generate
# - query_duration_ms: Total RAG pipeline time
# - documents_retrieved: Number of chunks retrieved
# - avg_similarity_score: Average relevance score

# View metrics (if observability enabled)
# See docs/OBSERVABILITY.md
```

## Advanced Topics

### Hybrid Search

Combine vector search with keyword search:

```python
# Vector search
vector_results = vector_store.similarity_search(query, k=5)

# Keyword search (using metadata)
keyword_results = [
    doc for doc in all_docs
    if query.lower() in doc.metadata.get('topic', '').lower()
]

# Merge and re-rank
combined_results = merge_results(vector_results, keyword_results)
```

### Re-ranking

Improve retrieval with re-ranking:

```python
from sentence_transformers import CrossEncoder

# After retrieval
initial_results = vector_store.similarity_search(query, k=20)

# Re-rank with cross-encoder (more accurate but slower)
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
scores = reranker.predict([(query, doc.page_content) for doc in initial_results])

# Sort by re-ranked scores and take top-3
reranked = sorted(zip(initial_results, scores), key=lambda x: x[1], reverse=True)
top_results = [doc for doc, score in reranked[:3]]
```

### Multi-Modal RAG

Extend to images and tables (future enhancement):

```python
# Extract images from PDFs
images = loader.load_images_from_pdf("document.pdf")

# Use multi-modal embeddings (e.g., CLIP)
image_embeddings = multi_modal_embedding_model.embed_images(images)

# Index alongside text
# Search with text queries that match visual content
```

## Related Documentation

- [Agent System](AGENT_SYSTEM.md) - How RAG integrates with agent
- [Tools Reference](TOOLS_REFERENCE.md) - RAG Tool documentation
- [Configuration](CONFIGURATION.md) - All RAG settings
- [Database Persistence](DATABASE_PERSISTENCE.md) - Session storage
