# Research Primer: langchain-chroma — Vector Store for RAG

**Sources:**  
- https://docs.trychroma.com/docs/collections/add-data (native API)  
- https://docs.trychroma.com/docs/querying-collections/query-and-get  
- LangChain integration: `langchain-chroma` wraps the native API  
**Retrieved:** 2026-06-24 via Context7 MCP  
**Relevance:** Indexing policy documents and retrieving relevant chunks for the compliance agent

---

## 1. Key Concepts

- **Collection** — a named set of documents with associated embeddings and metadata
- **Embedding function** — converts text to vectors (we use HuggingFace locally)
- **Persistent store** — ChromaDB can persist to disk; set `persist_directory`

---

## 2. LangChain-Chroma Integration

The `langchain-chroma` package wraps ChromaDB as a LangChain `VectorStore`. It works
with `langchain_core.documents.Document` objects.

### Indexing (first run — build the store)

```python
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "foi_policies"

embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " "],
)

documents = []
for path in Path("documents/policies").glob("*.txt"):
    text = path.read_text()
    chunks = splitter.create_documents(
        [text],
        metadatas=[{"source": path.name}],
    )
    documents.extend(chunks)

vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory=CHROMA_DIR,
    collection_name=COLLECTION_NAME,
)
print(f"Indexed {len(documents)} chunks")
```

### Loading an existing store (subsequent runs)

```python
vectorstore = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings,
    collection_name=COLLECTION_NAME,
)
```

### Retrieving relevant chunks (similarity search with scores)

```python
results = vectorstore.similarity_search_with_score(
    query="commercial interest exemption tender evaluation",
    k=5,
)
# results: list[tuple[Document, float]]
# Document.page_content — chunk text
# Document.metadata["source"] — filename
# float — distance score (lower = more similar for L2; higher = more similar for cosine)
```

**Note on scores:** ChromaDB default distance is L2 (lower = more similar). Use
`similarity_search_with_relevance_scores()` for cosine similarity normalised to [0, 1]
(higher = more similar — easier to display to operators).

```python
results = vectorstore.similarity_search_with_relevance_scores(
    query="commercial interest exemption",
    k=5,
)
# float in [0, 1]; display as "similarity: 0.82"
```

---

## 3. Native ChromaDB API (for reference)

The native API is useful if we need fine-grained control (e.g., deleting a collection
before re-indexing):

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

# Delete and recreate on re-index
try:
    client.delete_collection("foi_policies")
except Exception:
    pass
collection = client.create_collection("foi_policies")

# Add documents with pre-computed embeddings
collection.add(
    ids=["chunk-001", "chunk-002"],
    documents=["text chunk 1", "text chunk 2"],
    metadatas=[{"source": "foi-exemptions-guide.txt"}, {"source": "foi-exemptions-guide.txt"}],
)

# Query
results = collection.query(
    query_texts=["commercial interests exemption"],
    n_results=5,
    include=["documents", "metadatas", "distances"],
)
```

---

## 4. Generating chunk IDs

For the audit trail `evidence_refs` field, generate stable chunk IDs:

```python
chunk_id = f"{source_filename}:chunk-{chunk_index:03d}"
# e.g. "foi-exemptions-guide.txt:chunk-017"
```

Store in `Document.metadata["chunk_id"]` so retrieval can return them.

---

## 5. Key Packages

```
langchain-chroma>=0.1.0
langchain-huggingface>=0.1.0
chromadb>=1.0.0
sentence-transformers>=3.0.0
```

The HuggingFace embedding model is downloaded to `~/.cache/huggingface/` on first use
(~90 MB). Subsequent runs use the cache — no network required.

**Offline / proxy fallback:** Set `EMBEDDING_PROVIDER=openai` in `.env` and provide
`OPENAI_API_KEY`. The `rag.py` module should detect this and switch to
`langchain_openai.OpenAIEmbeddings`.
