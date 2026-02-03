# Pinecone Migration Guide

This guide explains how to migrate from FAISS (local vector store) to Pinecone (cloud vector database) for production deployment.

---

## 🎯 Why Migrate to Pinecone?

### FAISS (Local)
- ✅ **Free** - No costs
- ✅ **Fast** - In-memory operations
- ✅ **Simple** - File-based storage
- ❌ **Not scalable** - Limited by single machine
- ❌ **No persistence** - Requires manual backup
- ❌ **No filtering** - Limited metadata search
- ❌ **Single-user** - No concurrent access

### Pinecone (Cloud)
- ✅ **Scalable** - Serverless, auto-scaling
- ✅ **Persistent** - Always available, no data loss
- ✅ **Fast** - Optimized vector search
- ✅ **Metadata filtering** - Advanced search capabilities
- ✅ **Multi-tenant** - Concurrent users supported
- ✅ **Managed** - No infrastructure to maintain
- ✅ **Global** - Distributed across regions
- ❌ **Paid** - ~$70/month for 100k vectors (but free tier available)

**When to migrate:**
- Production deployment
- Multiple users
- Need for reliability/uptime
- Scaling beyond single machine
- Advanced filtering requirements

---

## 📋 Prerequisites

1. **Pinecone Account** - Sign up at [https://app.pinecone.io](https://app.pinecone.io)
2. **API Key** - Get from Pinecone console
3. **Existing FAISS data** - Have documents indexed in FAISS
4. **Python packages** - Install Pinecone dependencies

---

## ⚙️ Step 1: Install Dependencies

```bash
pip install pinecone-client langchain-pinecone
```

Or update from requirements.txt:

```bash
pip install -r requirements.txt
```

---

## 🔧 Step 2: Configure Pinecone

### 1. Get API Key

Go to [https://app.pinecone.io](https://app.pinecone.io) and:
1. Sign up / Log in
2. Navigate to **API Keys**
3. Copy your API key

### 2. Update .env

Add to your `.env` file:

```bash
# Enable Pinecone
USE_PINECONE=true

# Pinecone Configuration
PINECONE_API_KEY=your_api_key_here
PINECONE_INDEX_NAME=rag-agent
PINECONE_NAMESPACE=  # Optional: leave empty for default
PINECONE_METRIC=cosine  # cosine, euclidean, dotproduct
PINECONE_CLOUD=aws  # aws, gcp, azure
PINECONE_REGION=us-east-1  # Region closest to you
```

**Region Options:**
- **AWS:** us-east-1, us-west-2, eu-west-1, ap-southeast-1
- **GCP:** us-central1, europe-west4, asia-southeast1
- **Azure:** eastus, westus, westeurope

Choose the region closest to your users for lowest latency.

---

## 🚀 Step 3: Run Migration Script

We provide an automated migration script that:
1. Loads documents from FAISS
2. Creates Pinecone index (if needed)
3. Uploads vectors to Pinecone
4. Verifies migration
5. Tests search comparison

### Run Migration

```bash
# Make sure USE_PINECONE=false in .env (migration validates this)
python migrate_to_pinecone.py
```

**Expected Output:**

```
================================================================================
FAISS to Pinecone Migration Tool
================================================================================

🔍 Validating configuration...
✅ Configuration validated

📦 Initializing managers...
✅ Managers initialized

================================================================================
Step 1: Load FAISS Documents
================================================================================

📖 Loading documents from FAISS...
Loading vector store from data/vector_store...
Vector store loaded successfully
✅ Loaded 152 documents from FAISS

================================================================================
Step 2: Migrate to Pinecone
================================================================================

⚠️  You are about to migrate 152 documents to Pinecone
   Index: rag-agent
   Namespace: default
   Region: us-east-1

Proceed with migration? (y/n): y

📤 Migrating 152 documents to Pinecone...
   Batch 1/2: Processing 100 documents...
   ✓ Batch 1 completed
   Batch 2/2: Processing 52 documents...
   ✓ Batch 2 completed
✅ Migration complete! Added 152 documents to Pinecone

================================================================================
Step 3: Verify Migration
================================================================================

🔍 Verifying migration...
   FAISS vectors: 152
   Pinecone vectors (total): 152
✅ Migration verified successfully!

================================================================================
Step 4: Test Search
================================================================================

🔍 Testing search comparison...

   Query: 'What is machine learning?'

   FAISS Results:
   1. Machine learning is a subset of artificial intelligence that enables...
   2. ML algorithms learn from data to make predictions...
   3. Common types include supervised, unsupervised, and reinforcement...

   Pinecone Results:
   1. Machine learning is a subset of artificial intelligence that enables...
   2. ML algorithms learn from data to make predictions...
   3. Common types include supervised, unsupervised, and reinforcement...

✅ Search test complete

================================================================================
Migration Complete!
================================================================================
✅ Your documents have been migrated to Pinecone

📝 Next Steps:
   1. Update .env: Set USE_PINECONE=true
   2. Restart your application
   3. Test document search functionality
   4. (Optional) Delete local FAISS data to save space:
      rm -rf data/vector_store

💡 Tip: Keep FAISS data as backup until you verify Pinecone works
```

---

## 🔄 Step 4: Switch to Pinecone

### 1. Update Configuration

Edit `.env`:

```bash
# Change from false to true
USE_PINECONE=true
```

### 2. Restart Application

```bash
streamlit run main_v3.py
```

### 3. Verify

The system should now use Pinecone. You'll see in the logs:

```
📦 Document Manager initialized with PINECONE backend
```

---

## 🧪 Testing

### Test Search

```python
from src.document_manager import get_document_manager

# Create document manager (auto-detects Pinecone from config)
doc_manager = get_document_manager()

# Test search
results = doc_manager.similarity_search("What is machine learning?", k=3)

for doc in results:
    print(doc.page_content[:200])
```

### Test Statistics

```python
# Get index stats
stats = doc_manager.get_stats()
print(f"Backend: {stats['backend']}")
print(f"Total vectors: {stats['total_vectors']}")
print(f"Index: {stats['index_name']}")
```

### Test Filtering (Pinecone-only feature)

```python
# Search with metadata filter
results = doc_manager.similarity_search(
    query="machine learning",
    k=5,
    filter={"source": "ml_textbook.pdf"}
)
```

---

## 📊 Cost Estimation

Pinecone pricing (as of 2026):

### Serverless Plan (Pay-as-you-go)
- **Read requests:** $0.30 per 1M requests
- **Write requests:** $2.00 per 1M requests
- **Storage:** $0.45 per GB-month

### Example Costs

| Vectors | Storage | Reads/Month | Writes/Month | Cost/Month |
|---------|---------|-------------|--------------|------------|
| 10K | 0.5 GB | 100K | 1K | ~$1 |
| 100K | 5 GB | 1M | 10K | ~$5 |
| 1M | 50 GB | 10M | 100K | ~$30 |

**Free Tier:**
- 1 free serverless index
- Limited throughput

---

## 🔍 Advanced Features

### 1. Metadata Filtering

Pinecone supports advanced metadata filtering:

```python
# Filter by source
results = doc_manager.similarity_search(
    "machine learning",
    filter={"source": "ml_textbook.pdf"}
)

# Filter by date range
results = doc_manager.similarity_search(
    "recent developments",
    filter={
        "date": {"$gte": "2024-01-01", "$lt": "2025-01-01"}
    }
)

# Combine filters
results = doc_manager.similarity_search(
    "neural networks",
    filter={
        "$and": [
            {"source": "ml_textbook.pdf"},
            {"topic": "deep learning"}
        ]
    }
)
```

### 2. Namespaces

Organize vectors into separate namespaces:

```python
from src.vector_store_pinecone import PineconeVectorStoreManager
from src.embeddings import EmbeddingManager

# Create manager with namespace
embedding_mgr = EmbeddingManager()
pinecone_mgr = PineconeVectorStoreManager(
    embedding_mgr,
    namespace="user-123"  # User-specific namespace
)

# Add documents
pinecone_mgr.add_documents(documents)

# Search within namespace
results = pinecone_mgr.similarity_search("query", k=5)
```

**Use cases for namespaces:**
- Multi-tenancy (one namespace per user)
- Document categories
- Environment separation (dev/staging/prod)

### 3. Batch Operations

```python
# Upsert documents (update or insert)
ids = doc_manager.upsert_documents(documents, batch_size=100)

# Delete by filter
doc_manager.delete_by_filter({"source": "old_document.pdf"})

# Delete all
doc_manager.delete_all()  # Deletes current namespace
```

### 4. Index Management

```python
# Get index statistics
stats = doc_manager.get_stats()
print(f"Total vectors: {stats['total_vectors']}")
print(f"Namespaces: {stats['namespaces']}")

# List all namespaces
namespaces = doc_manager.list_namespaces()
print(f"Namespaces: {namespaces}")
```

---

## 🔒 Security Best Practices

### 1. Protect API Key

Never commit API keys to git:

```bash
# Add to .gitignore
echo ".env" >> .gitignore
```

Use environment variables in production:

```bash
export PINECONE_API_KEY=your_key
```

### 2. Network Security

For production, use:
- VPC peering (Pinecone Enterprise)
- Private endpoints
- IP whitelisting

### 3. Access Control

Use separate API keys for:
- Development
- Staging
- Production

Rotate keys regularly.

---

## 🆘 Troubleshooting

### Migration fails with "Index not ready"

**Issue:** Index creation takes 30-60 seconds.

**Solution:**
```python
# The migration script waits automatically, but if you're creating manually:
import time
from pinecone import Pinecone

pc = Pinecone(api_key=api_key)
pc.create_index(...)

# Wait for index to be ready
while not pc.describe_index(index_name).status['ready']:
    time.sleep(1)
```

### "DimensionMismatch" error

**Issue:** Index dimension doesn't match embedding dimension.

**Solution:**
```python
# Check embedding dimension
from src.embeddings import EmbeddingManager

embedding_mgr = EmbeddingManager()
sample = embedding_mgr.embedding_model.embed_query("test")
print(f"Embedding dimension: {len(sample)}")  # e.g., 384

# Create index with correct dimension
pc.create_index(
    name="rag-agent",
    dimension=384,  # Match your embedding dimension
    metric="cosine"
)
```

### Slow queries

**Issue:** High latency on searches.

**Solutions:**
1. Choose region closest to your users
2. Use metadata filtering to reduce search space
3. Increase batch size for bulk operations
4. Consider caching frequent queries

### High costs

**Issue:** Unexpected charges.

**Solutions:**
1. Monitor usage in Pinecone console
2. Use namespaces to partition data
3. Delete unused vectors
4. Batch write operations
5. Cache read results
6. Use free tier for development

---

## 📈 Performance Comparison

Based on 100K vectors with 384 dimensions:

| Operation | FAISS (Local) | Pinecone (Cloud) |
|-----------|---------------|------------------|
| **Query latency** | 10-50ms | 50-150ms (network) |
| **Throughput** | 1K QPS | 10K+ QPS |
| **Concurrent users** | 1 | Unlimited |
| **Reliability** | Single point of failure | 99.9% uptime |
| **Scaling** | Manual | Automatic |
| **Cost** | Hardware costs | ~$5-30/month |

---

## 🔄 Rolling Back to FAISS

If you need to switch back:

### 1. Update Configuration

```bash
# In .env
USE_PINECONE=false
```

### 2. Ensure FAISS Data Exists

```bash
ls data/vector_store/
# Should show: index.faiss, index.pkl
```

### 3. Restart Application

```bash
streamlit run main_v3.py
```

---

## 🌐 Production Deployment

### Environment Variables

For production (e.g., Railway, Render, Heroku):

```bash
# Set in deployment platform
PINECONE_API_KEY=your_api_key
USE_PINECONE=true
PINECONE_INDEX_NAME=rag-agent-prod
PINECONE_NAMESPACE=production
PINECONE_REGION=us-east-1
```

### Health Checks

Add health check endpoint:

```python
from src.document_manager import get_document_manager

def health_check():
    doc_manager = get_document_manager()
    return {
        "status": "healthy" if doc_manager.is_available() else "unhealthy",
        "backend": doc_manager.get_backend_type(),
        "stats": doc_manager.get_stats()
    }
```

### Monitoring

Monitor:
- Query latency
- Error rates
- Vector count growth
- Costs (via Pinecone console)

---

## 📚 Additional Resources

- **Pinecone Documentation:** [https://docs.pinecone.io](https://docs.pinecone.io)
- **Pinecone Console:** [https://app.pinecone.io](https://app.pinecone.io)
- **LangChain Pinecone Integration:** [https://python.langchain.com/docs/integrations/vectorstores/pinecone](https://python.langchain.com/docs/integrations/vectorstores/pinecone)
- **Migration Script:** [migrate_to_pinecone.py](migrate_to_pinecone.py)
- **Document Manager:** [src/document_manager.py](src/document_manager.py)
- **Pinecone Vector Store:** [src/vector_store_pinecone.py](src/vector_store_pinecone.py)

---

*Last updated: 2026-02-03*
