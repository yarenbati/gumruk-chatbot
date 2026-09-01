# Agent Kuralları

Bu depoda çalışacak kodlama ajanları (ve katkıda bulunanlar) için kurallar.

- Python 3.10+ kullanılır.
- Uygulamayı basit ve modüler tut.
- Type hint kullan.
- Public fonksiyon/sınıflara docstring ekle.
- API anahtarlarını asla hard-code etme; sadece environment değişkenleri (`.env`) üzerinden oku.
- Gerçek mevzuat kaynak belgelerini (`data/raw/` içeriği) asla commit etme.
- `LegalDocument → Article → Chunk` yapısını koru (bkz. `docs/data-model.md`).
- Chunk'lama için sabit boyutlu (arbitrary fixed-size) yaklaşım yerine mevzuat yapısına duyarlı (madde bazlı) chunk'lamayı tercih et.
- Her chunk, belge/madde/kaynak metadata'sını korumalıdır.
- Açıkça istenmedikçe LangChain, LlamaIndex, agent framework'leri, SQL veritabanları veya başka büyük framework'ler ekleme.
- Uygun olan yerlerde yeni işlevsellik için test ekle.
- Açık talimat olmadan büyük mimari değişiklikler yapma.
- Konfigürasyon merkezi olarak `src/config.py` içinde kalmalıdır.
- LLM ve embedding modelleri environment değişkenleri üzerinden konfigüre edilebilir olmalıdır.
