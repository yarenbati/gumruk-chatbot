# 5607 Sayılı Kaçakçılıkla Mücadele Kanunu — M12A Kaynak ve Yapı Analizi

## Sonuç

Kaynak DOCX olarak okunabildi. Mevcut parser değişiklik yapılmadan çalıştı,
ancak yapısal envanterdeki 43 article-like birimden yalnızca 1 Article üretti.
Bu nedenle 5607 parser uyumluluğu M12B kapsamındadır ve kaynak indekslemeye
hazır değildir.

## Resmî provenance ve format

- Başlık: `Kaçakçılıkla Mücadele Kanunu`
- Kanun numarası: `5607`
- Belge türü: `Kanun`
- Veren kurum: `TBMM` (mevcut proje manifest konvansiyonu)
- Resmî kaynak: `https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=5607&MevzuatTur=1&MevzuatTertip=5`
- Yerel dosya: `data/raw/5607-kacakcilikla-mucadele-kanunu.docx`
- Özgün `.doc`: çalışma alanında yok
- DOCX boyutu: `68,231` byte
- DOCX SHA-256: `47ECE3BA1B36965AF4C7931BA430E01C057693B40579140342B9C090A261762D`
- Format: ZIP/OOXML (`50 4B 03 04`), 16 paket parçası
- `python-docx`: başarıyla açıldı
- Normalizasyon: resmî kaynak → manuel Microsoft Word Save As → DOCX

DOC ve DOCX arasında byte eşdeğerliği iddia edilmemektedir. Özgün DOC mevcut
olmadığı için özgün dosyanın boyutu ve hash'i kaydedilememiştir. `retrieved_at`
olarak manuel sağlanan dosyanın çalışma alanına alındığı `2026-09-10` tarihi
kullanılmıştır.

## Manifest kabulü

Önerilen üç kayıtlı manifest, dosyaya yazılmadan önce `SourceRegistry` ile
bellekte doğrulandı: üç benzersiz `document_id`, üç benzersiz `local_file`,
belirsiz olmayan legislation number değerleri ve geçerli canonical ID bulundu.
Ardından `5607_kacakcilikla_mucadele_kanunu` kaydı eklendi. Mevcut şema aynen
korundu.

## DOCX yapısal envanteri

Envanter `scripts/audit_5607_structure.py` ile üretim parser'ından bağımsız
çıkarıldı.

| Ölçüm | Sonuç |
|---|---:|
| Toplam Word paragrafı | 275 |
| Boş olmayan paragraf | 227 |
| Kısım başlığı | 0 |
| Bölüm başlığı | 5 |
| Ayırım başlığı | 0 |
| Normal madde başlığı | 28 |
| Suffixed normal madde | 1 |
| Ek Madde | 0 |
| Geçici Madde | 15 |
| Diğer/özel article-like yapı | 0 |
| Numaralı fıkra (`(N)` veya `N.`) | 100 |
| Harfli bent | 29 |
| `Mülga` occurrences | 12 |
| Inline footnote reference | 24 |
| Footnote body | 24 |
| Tablo | 1 adet, 22 satır × 3 sütun |
| Unicode replacement character | 0 |

Bölüm başlıkları `BİRİNCİ BÖLÜM`–`BEŞİNCİ BÖLÜM` aralığındadır. Kısım veya
Ayırım seviyesi görülmedi. Tablo 21 veri satırlı değişiklik/geçmiş tablosudur.
Footnote gövdeleri `word/footnotes.xml` içinde, referanslar body OOXML'inde
ayrıdır; mevcut ingestion yalnızca referans ID'lerini korur.

## Article-like inventory

| Tür | Sayı |
|---|---:|
| Normal, suffix yok | 27 |
| Normal, suffixed | 1 |
| Ek | 0 |
| Geçici | 15 |
| Diğer/özel | 0 |
| Toplam | 43 |

Suffixed madde: `16/A`.

Geçici maddeler: `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `11`,
`12`, `13`, `14`, `15`.

Mevcut namespace'lere uymayan madde türü yoktur. Kritik biçim farkı, normal ve
geçici başlıkların çoğunun kaynakta büyük harfle (`MADDE`, `GEÇİCİ MADDE`)
yazılmasıdır. Mevcut regex'ler case-sensitive'dir. `16/A` karma yazımla
(`Madde 16/A`) bulunduğu için tek eşleşen madde olmuştur.

Temsilî yapılar: Madde 1 ve 5 gibi basit `(1)` fıkralı maddeler; Madde 3 gibi
çok fıkralı ve bentli madde; Madde 2, 3, 4, 13, 20 ve 23 çevresinde `a)`, `b)`
bentleri; altı fıkralı `16/A`; 1–4 esas metinli ve 5–15 çoğunlukla eklenme
notuyla başlayan geçici maddeler. Mülga metni Madde 6, 8, 14, 17 ve Geçici
Madde 4 dahil 12 kez görülür.

## Mevcut parser diagnostic'i

Ingestion başarıyla tamamlandı. Root `document_id` değeri
`5607_kacakcilikla_mucadele_kanunu`, `source_file` değeri manifest ile aynı,
paragraf alanı ve gerçek paragraf sayısı `227`'dir.

Mevcut parser hata vermeden tamamlandı fakat sonuç maddi biçimde uyumsuzdur:

- Article sayısı: `1`
- `normal`: `1`, `ek`: `0`, `gecici`: `0`
- Tek Article: `5607-madde-16-a`, `article_no=16/A`
- Duplicate Article ID: `0`
- Malformed article number: `0`
- Şüpheli omission: `42` article-like birim
- Tek kaydın `section_context`: `Üçüncü Bölüm`

Başlıca neden, mevcut `src/chunk.py` regex'lerinin `Madde` ve `Geçici`
yazımını case-sensitive eşleştirmesi; kaynakta 27 normal ve 15 geçici başlığın
büyük harfli olmasıdır. Parser kodu değiştirilmemiştir. Tam Article metin
rekonstrüksiyonu ve section context doğrulaması bu nedenle başarısız kabul
edilmiştir.

## Mevcut chunker diagnostic'i

Mevcut chunker yalnızca parser'ın ürettiği tek Article üzerinde offline
çalıştırıldı:

- Toplam chunk: `1`
- Unique Article ID: `1`
- Unique chunk ID: `1`
- Multi-chunk provision: `0`
- Provision başına maksimum chunk: `1`
- Maksimum chunk uzunluğu: `3,621` karakter
- Duplicate Article/Chunk ID: `0` / `0`
- Parsed Article.text rekonstrüksiyonu: `pass`
- Indivisible fıkra soft target aşımı: yok

Bu sonuç corpus uyumluluğu anlamına gelmez; 42 birim atlanmıştır. Tam chunker
kabulü M12B'ye ertelenmiştir.

## Identity ve storage-ID kontrolü

Parsed kayıt için `DocumentSourceKey("5607_kacakcilikla_mucadele_kanunu",
"normal", "16/A")` başarıyla türetilebilir. Storage ID
`5607-madde-16-a` biçimindedir. `5607-` prefix'i 5326 ve 4458 prefix'lerinden
ayrıdır; parsed subset için collision yoktur. Tam 43 birim kümesinin collision
kontrolü parser uyuşmazlığı nedeniyle M12B'ye ertelenmiştir.

## Riskler ve M12B önerisi

1. Büyük/küçük harf duyarlı başlık eşleşmesi 42 birimi atlıyor.
2. Geçici maddeler ve bazı tire biçimleri açık fixture'larla doğrulanmalı.
3. 100 fıkra ve 29 bent örneği chunker ile tam test edilmeli.
4. 24 footnote gövdesi ayrı provenance olarak ele alınmalı.
5. 22×3 değişiklik tablosu esas madde chunk'larından ayrı tutulmalı.
6. Mülga ve amendment note yapıları metin kaybı olmadan test edilmeli.

M12B parser davranışını düzelterek tam Article envanterini, section context'i,
chunk rekonstrüksiyonunu ve 5607 ID collision kontrolünü kabul testleriyle
doğrulamalıdır. M12A'da `src/*.py` değiştirilmedi; embedding, Chroma,
indexing ve retrieval çalıştırılmadı.

## M12B uyumluluk sonucu

M12A'nın ilk sonucu olan `1 / 43` Article sonucu korunmuştur. M12B'de yalnızca
article-family başlık regex'leri case-insensitive yapıldı; kaynak metni
lowercase edilmedi. Suffixed article numarası canonical olarak `16/A` tutuldu.

Gerçek 5607 DOCX üzerinde mevcut ingestion çıktısı ile parser artık tam
envanteri üretiyor:

- Article: `43`
- `normal`: `28`
- `gecici`: `15`
- `ek`: `0`
- suffixed normal: `16/A`
- Geçici Madde numaraları: `1`–`15`
- duplicate Article ID: `0`
- malformed article number: `0`
- omission: `0`

Beş bölümün tamamı doğru sınırlarda taşındı:

| Section context | Article aralığı |
|---|---|
| Birinci Bölüm | 1–2 |
| İkinci Bölüm | 3–8 |
| Üçüncü Bölüm | 9–16/A |
| Dördüncü Bölüm | 17–24 |
| Beşinci Bölüm | 25–27 ve Geçici Madde 1–15 |

Kısım ve Ayırım eklenmedi. 5607'de bulunan 100 `(N)` fıkra ve 29 harfli bent
paragrafı doğru article metinlerine bağlı kaldı; kaynakta `N.` biçimli fıkra
bulunmadı. Amendment/Mülga metni Article.text içinde kaldı ve bentler
bağlandıkları fıkradan ayrılmadı.

Mevcut chunker 46 chunk üretti. 43 Article ID ve 46 chunk ID benzersizdir.
İki multi-chunk provision vardır: `5607-madde-3` (3 chunk) ve
`5607-madde-23` (2 chunk). `5607-madde-3-chunk-001`, Article başlığı ve
amendment preamble'ı ile bütün fıkra grupları 1–11'i, fıkra 11'in a–c bentleri
dahil, aynı chunk'ta taşır. Bu chunk'ın uzunluğu Python karakter sayımıyla
`3,742` karakter, UTF-8 serileştirmesiyle `4,119` byte'tır. Article title
(`Kaçakçılık suçları`) Article.text dışında tutulur ve chunk'a girmez. En uzun
Unicode chunk `3,766` karakterdir; dolayısıyla `MAX_CHUNK_CHARS=4000` aşılmaz.
Birden fazla bütün fıkranın soft-target altında gruplanması, izin verilen fıkra
sınırlarında yapılır; tek bir indivisible fıkra da 4,000'i aşmaz. Tüm 43
Article.text değeri ordered chunk metinlerinden birebir yeniden kuruldu;
metin kaybı, tekrar veya fıkra/bent içi bölünme yoktur.

5607 Article ve Chunk storage ID kümeleri içinde ve mevcut 5326/4458 kümeleriyle
cross-document collision sayısı `0`'dır. `16/A` için ID
`5607-madde-16-a`, canonical key ise
`5607_kacakcilikla_mucadele_kanunu/normal/16/a` olarak korunmuştur.
Her 5607 Article/Chunk için `DocumentSourceKey` document_id, article_type ve
article_no alanlarından başarıyla türetilmiştir; legislation number veya
storage-ID prefix'i kullanılmamıştır.

Regresyon sonuçları: 5326 `53 Article / 53 chunk`; mevcut persisted Article ve
Chunk JSON çıktılarıyla parity `pass`. 4458 `271 Article / 276 chunk` ve türler
`normal=259`, `gecici=11`, `islenemeyen_hukum=1`; özel
`4458 SAYILI KANUNA İŞLENEMEYEN HÜKÜMLER` davranışı korunmuştur.

24 inline footnote reference ve 24 footnote body ile 22×3 değişiklik tablosu
M12A'daki gibi korunmuş/deferred durumdadır. Footnote gövdeleri Article.text'e
eklenmedi; tablo ana madde chunk'larına dönüştürülmedi.

M12B değişiklikleri:

- `src/chunk.py`: article-family recognition regex'lerinde `re.IGNORECASE`;
  suffixed article number canonicalization.
- `tests/test_chunk.py`: capitalization, section geçişi, fıkra/bent,
  amendment/Mülga ve ID testleri.

M12C kapsamı olan embedding veya indexing yapılmadı.
