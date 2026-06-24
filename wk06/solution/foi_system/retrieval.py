"""Policy retrieval via ChromaDB vector search."""

from foi_system.config import CHROMA_PATH, COLLECTION, RAG_TOP_K
from foi_system.indexing import embed_query, get_collection
from foi_system.models import RetrievedChunk


def search_policies(
    query: str,
    k: int = RAG_TOP_K,
    path: str = CHROMA_PATH,
    name: str = COLLECTION,
) -> list[RetrievedChunk]:
    """Search the policy index for chunks nearest to query.

    Returns up to k RetrievedChunk instances ordered nearest-first (lowest
    cosine distance first).  Returns [] when the collection is empty or no
    results are available — never raises.

    query is embedded with embed_query (which applies the nomic search_query:
    prefix internally) — never pre-summarise the query before passing it here.
    """
    col = get_collection(path, name)

    try:
        res = col.query(
            query_embeddings=[embed_query(query)],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        return []

    documents = res.get("documents") or [[]]
    metadatas = res.get("metadatas") or [[]]
    distances = res.get("distances") or [[]]

    doc_list = documents[0] if documents else []
    meta_list = metadatas[0] if metadatas else []
    dist_list = distances[0] if distances else []

    if not doc_list:
        return []

    chunks: list[RetrievedChunk] = []
    for text, meta, distance in zip(doc_list, meta_list, dist_list):
        raw_section = meta.get("section", "") if meta else ""
        section = raw_section if raw_section else None  # "" -> None

        chunks.append(
            RetrievedChunk(
                text=str(text),
                source=str(meta.get("source", "")) if meta else "",
                section=section,
                chunk_index=int(meta.get("chunk_index", 0)) if meta else 0,
                distance=float(distance),
            )
        )

    return chunks
