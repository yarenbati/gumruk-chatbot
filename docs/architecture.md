# Mimari

Bu belge, gümrük mevzuatı RAG chatbotunun planlanan mimarisini tanımlar. Henüz uygulanmamış bileşenler de dahil olmak üzere sistemin hedef tasarımını gösterir; ekstra servis veya framework içermez.

## Genel Akış

```mermaid
flowchart TD
    A[Legal Documents] --> B[Ingestion]
    B --> C[Article-based Chunking]
    C --> D[Embeddings]
    D --> E[Chroma Vector Store]
    E --> F[Retrieval]
    F --> G[LLM]
    G --> H[Grounded Answer + Citations]
    H --> I[Streamlit UI]
```

## Indexing Flow (Offline)

Mevzuat belgelerinin sisteme kazandırıldığı, çevrimdışı çalışan hazırlık akışı.

```mermaid
flowchart LR
    A[Legal documents] --> B[Extraction]
    B --> C[Legal-structure parsing]
    C --> D[Chunks + metadata]
    D --> E[Embeddings]
    E --> F[Chroma]
```

- **Extraction**: `src/ingest.py` — ham PDF/metin belgelerinden metni çıkarır.
- **Legal-structure parsing**: belge içindeki madde/başlık yapısını tanır (ör. madde no, başlık, sayfa).
- **Chunks + metadata**: `src/chunk.py` — madde bazlı parçalama, her chunk'a kaynak metadata'sı eklenir.
- **Embeddings**: `src/embed.py` — OpenAI embedding modeli (config.EMBEDDING_MODEL) ile vektörleştirme.
- **Chroma**: yerel `PersistentClient` üzerinde koleksiyon olarak saklama (config.COLLECTION_NAME).

## Query Flow (Online)

Kullanıcının soru sorduğu anda çalışan, gerçek zamanlı akış.

```mermaid
flowchart LR
    A[User question] --> B[Query embedding]
    B --> C[Chroma retrieval]
    C --> D[Relevant legal chunks]
    D --> E[LLM]
    E --> F[Grounded answer + citations]
```

- **Query embedding**: kullanıcı sorusu aynı embedding modeliyle vektörleştirilir.
- **Chroma retrieval**: `src/retrieve.py` — en alakalı `config.TOP_K` chunk getirilir.
- **LLM**: `src/generate.py` — OpenAI LLM (config.LLM_MODEL, config.TEMPERATURE) bağlam + soru ile yanıt üretir.
- **Grounded answer + citations**: yanıt, kullanılan chunk'ların kaynak (belge/madde/sayfa) bilgisiyle birlikte döner.
- **Streamlit UI**: `app.py` — soru girişi ve yanıt + kaynak gösterimi.

## Kapsam Dışı

Bu aşamada framework (LangChain, LlamaIndex vb.), ajan mimarisi veya SQL veritabanı planlanmamaktadır. Bkz. `AGENTS.md`.
