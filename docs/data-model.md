# Veri Modeli

Bu belge, sistemin domain modelini tanımlar. Chroma bir vektör veritabanı olduğu için burada ilişkisel bir SQL şeması değil, kavramsal bir domain modeli tarif edilmektedir.

Bu sürüm, `docs/source-analysis-5326.md` (M1) analizinin önerdiği alanları
modele işler — `src/ingest.py` (M2) zaten `ExtractedParagraph.index` alanı
üzerinden orijinal paragraf konumunu koruyor; `source_paragraph_start`/`_end`
alanları doğrudan bu indekslere karşılık gelecek şekilde tasarlanmıştır.
Henüz parsing/chunking kodu yazılmadı (M3); bu, yalnızca gelecekteki kodun
hedef alacağı veri sözleşmesidir.

## Varlıklar (Entities)

### LegalDocument
- `document_id`
- `title`
- `document_type`
- `source_file`
- `version` / `effective_date` (varsa)

### Article
- `article_id`
- `document_id`
- `article_no` (ör. `"2"`, `"42/A"`, `"1"` — Ek/Geçici madde için de kendi sayacındaki numara)
- `article_type` — `normal` | `ek` | `gecici`
- `title` (madde başlığı paragrafı, ör. `"Sorumluluk"`; bazı Ek/Geçici maddelerde olmayabilir)
- `section_context` (opsiyonel; maddenin içinde bulunduğu Kısım/Bölüm'ün **birleşik** bağlamı, ör. `"Birinci Kısım > İkinci Bölüm"` — tek bir başlık değil, hiyerarşik yol)
- `text`
- `page` (opsiyonel, genellikle `null` — DOCX reflowable format olduğu için güvenilir değil, bkz. `docs/source-analysis-5326.md` §2)
- `source_paragraph_start` (bu maddenin başladığı `ExtractedParagraph.index`)
- `source_paragraph_end` (bu maddenin bittiği `ExtractedParagraph.index`)
- `amendment_note` (opsiyonel; madde başlığındaki parantez içi değişiklik notu, ör. `"(Değişik: 6/12/2006-5560/31 md.)"`)
- `footnote_references` (opsiyonel; bu maddeye bağlı dipnot ID'lerinin listesi, `word/footnotes.xml`'den)

### Chunk
- `chunk_id`
- `article_id`
- `legislation_number` (ör. `"5326"`)
- `article_no`
- `article_type`
- `article_title`
- `section_context` (opsiyonel; bkz. Article)
- `text`
- `paragraph_numbers` (opsiyonel; chunk içindeki numaralı fıkra kimliklerinin listesi, ör. `["1", "2"]`. Maddenin numaralı fıkrası yoksa boş liste/`null` olabilir)
- `source_paragraph_start`
- `source_paragraph_end`
- `metadata` (diğer serbest-form alanlar için; yukarıdaki alanlar zaten en sık kullanılan durumları kapsar)

### Query
- `query_id`
- `text`

### RetrievedChunk
- `chunk`
- `similarity_score`
- `rank`

### Answer
- `text`
- `citations`

### Citation
- `document_name`
- `legislation_number`
- `article_no`
- `paragraph_no`
- `page` (opsiyonel)
- `chunk_id`

## Not: Section ve Paragraph ayrı varlık değildir

**Section** (Kısım/Bölüm) ve **Paragraph** (fıkra), `docs/source-analysis-5326.md`
§11'de belirtildiği gibi, ayrı domain varlıkları değil; parsing/metadata
kavramlarıdır. Section, `Article.section_context` alanına birleşik bir yol
olarak; Paragraph, `Chunk.paragraph_numbers` alanına opsiyonel bir kimlik
listesi olarak yansıtılır. Bu, mimariyi değiştirmez — `LegalDocument →
Article → Chunk` hiyerarşisi aynen korunur.

## İlişkiler

- `LegalDocument` 1 → many `Article`
- `Article` 1 → many `Chunk`
- `Query` → many `RetrievedChunk`
- `Answer` → many `Citation`
- `Citation` → kaynak `Chunk` / `Article`

## Diyagram

```mermaid
classDiagram
    class LegalDocument {
        +document_id
        +title
        +document_type
        +source_file
        +version
        +effective_date
    }

    class Article {
        +article_id
        +document_id
        +article_no
        +article_type
        +title
        +section_context
        +text
        +page
        +source_paragraph_start
        +source_paragraph_end
        +amendment_note
        +footnote_references
    }

    class Chunk {
        +chunk_id
        +article_id
        +legislation_number
        +article_no
        +article_type
        +article_title
        +section_context
        +text
        +paragraph_numbers
        +source_paragraph_start
        +source_paragraph_end
        +metadata
    }

    class Query {
        +query_id
        +text
    }

    class RetrievedChunk {
        +chunk
        +similarity_score
        +rank
    }

    class Answer {
        +text
        +citations
    }

    class Citation {
        +document_name
        +legislation_number
        +article_no
        +paragraph_no
        +page
        +chunk_id
    }

    LegalDocument "1" --> "many" Article
    Article "1" --> "many" Chunk
    Query --> "many" RetrievedChunk
    RetrievedChunk --> Chunk
    Answer --> "many" Citation
    Citation --> Chunk
    Citation --> Article
```

## Not

Bu model Chroma koleksiyonundaki metadata alanlarına (ör. `document_id`, `legislation_number`, `article_no`, `article_type`, `page`, `chunk_id`) doğrudan karşılık gelecek şekilde tasarlanmıştır; ayrı bir ilişkisel veritabanı planlanmamaktadır.
