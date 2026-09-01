# Kaynak Analizi: 5326 Sayılı Kabahatler Kanunu (M1)

Bu belge, `data/raw/` içindeki ilk resmi kaynak belgenin yapısal analizini
özetler. Analiz `scripts/inspect_docx_structure.py` çalıştırılarak
üretilmiştir; bu script tek seferlik analiz aracıdır, üretim ingestion/chunking
pipeline'ı değildir (bkz. `AGENTS.md`).

## 0. Kaynak Format Durumu (Çözüldü)

Mevzuat, resmi kaynak olan **mevzuat.gov.tr**'den temin edilmiştir (bkz.
`data/source_manifest.json` → `official_source_url`). Oradan ilk elde edilen
dosya eski ikili Word biçimindeydi (`.doc`, OLE/Compound Document File V2) —
`python-docx` bu dosyayı açamıyordu (bkz. bu belgenin önceki sürümü / git
geçmişi). Bu durum, dosyanın **Microsoft Word kullanılarak elle `.docx`
biçimine dönüştürülmesiyle** çözüldü; dosya boşluksuz olarak yeniden
adlandırıldı.

**Önemli netlik:** `data/raw/5326-kabahatler-kanunu.docx`, mevzuat.gov.tr'den
doğrudan `.docx` olarak indirilmiş bir dosya **değildir**. Orijinal `.doc`
kaynağının elle normalize edilmiş, çalışmaya uygun bir türevidir.

*(Not: dosya ilk yeniden adlandırmada geçici olarak `5326-kabahatlar-kanunu.docx`
olarak kaydedilmişti — "kabahat**la**r" / "kabahat**le**r" yazım hatası.
Kullanıcıyla doğrulanıp o dosyanın kullanılması onaylanmış, ardından dosya
doğru yazımla `5326-kabahatler-kanunu.docx` olarak yeniden adlandırılmıştır;
`data/source_manifest.json` ve bu belge güncel/doğru dosya adını referans
alıyor.)*

Bu `.docx` geçerli bir OOXML/zip paketi olduğu için `scripts/inspect_docx_structure.py`
artık onu **doğrudan `python-docx` ile** okuyor:

```
STEP 1: open with python-docx
OK: python-docx opened '5326-kabahatler-kanunu.docx' directly (no fallback used).
  paragraphs: 340, tables: 1
```

`antiword`, LibreOffice veya başka bir harici CLI aracı **artık ne analiz
scriptinde ne de önerilen üretim ingestion tasarımında** gerekli değil.
Tek bağımlılık `requirements.txt` içindeki `python-docx` paketi — bu,
Streamlit Community Cloud dahil planlanan tüm Python ortamlarında taşınabilir
(sadece deklare edilen bağımlılığın kurulu olması yeterli).

## 1. Kaynak Yapısı

- Belge başlığı: `KABAHATLER KANUNU`, `Kanun Numarası: 5326`
- `python-docx` ile 340 paragraf, 1 tablo tespit edildi (281 boş olmayan paragraf)
- `BİRİNCİ KISIM` / `İKİNCİ KISIM` gibi **Kısım** başlıkları dahil toplam
  **6 Kısım/Bölüm başlığı**
- Belge sonunda, kanunda değişiklik yapan mevzuatın yürürlük tarihlerini
  listeleyen gerçek bir **Word tablosu** (`Document.tables[0]`): 20 satır
  (1 başlık + 19 veri satırı) × 3 sütun
- Belge sonunda **13 gerçek Word dipnotu** (`word/footnotes.xml`), madde
  metinleri içinde **13 `<w:footnoteReference>` elemanı** ile bağlanıyor
  (bkz. §4 — bu, antiword'ün ürettiği düz metin gösteriminden yapısal olarak
  farklı ama içerik olarak eşdeğer)

## 2. Çıkarım (Extraction) Kalitesi

- `python-docx` dosyayı doğrudan ve güvenilir biçimde açıyor; ek çıkarım
  adımı/dönüştürme gerekmiyor.
- **Türkçe karakterler korunuyor**: `ığĞşŞöÖüÜçÇİı` örnek kümesinin tamamı
  hem paragraf metninde hem dipnot metninde doğrulandı, `�` (bozuk karakter)
  tespit edilmedi.
- **Sayfa numaraları güvenilir şekilde çıkarılamıyor.** `docProps/app.xml`
  içinde uygulama tarafından hesaplanmış bir `<Pages>18</Pages>` değeri var
  (Word'ün kelime sayısı gibi belge geneli bir özet istatistiği), ancak bu
  belirli bir yazdırma düzenine bağlı türetilmiş bir değerdir; madde/paragraf
  düzeyinde bir alıntı (citation) anahtarı değildir. `python-docx`,
  paragraf başına sayfa numarası hiç sunmuyor (DOCX reflowable/yeniden akışlı
  bir formattır, sayfa kırılması render zamanı bilgisidir, belgede kalıcı
  olarak saklanmaz).
  **Sonuç: birincil alıntı (citation) çapası `legislation_number` +
  `article_no` olmalı** (gerektiğinde `paragraph_no` ile birlikte), `page`
  değil. `docs/data-model.md`'deki `Article.page` ve `Citation.page`
  alanları bu kaynak için `null`/boş kalmalı.

## 3. Tespit Edilen Madde Kalıpları

| Kalıp | Regex (özet) | Sayı |
|---|---|---|
| Normal madde | `Madde N-` | 45 |
| Harfli/ek madde numarası | `Madde N/A-` (ör. 42/A, 43/A, 43/B, 43/C) | 4 |
| Ek Madde | `Ek Madde N-` | 1 |
| Geçici Madde | `Geçici Madde N-` | 3 |
| Numaralı fıkra | `(N) ...` paragraf başında | 105 |

- Harfli madde numaraları: `42/A, 43/A, 43/B, 43/C` — bunlar sonradan eklenen
  maddeler için orijinal numaralamayı bozmadan araya eklenmiş maddeler.
- Ek Madde: `Ek Madde 1`
- Geçici Madde: `Geçici Madde 1, 2, 3`
- Her madde genelde kendi başlık paragrafı (ör. `Tanım`, `Sorumluluk`) ile
  başlıyor, ardından `Madde N- (Değişiklik notu varsa parantez içinde) ...`
  paragrafı geliyor. **Önemli parsing kuralı**: `python-docx` ile her fıkra
  ve alt bent (`a) b) c)`) kendi ayrı paragrafı olarak geliyor (antiword'deki
  gibi sabit genişlikte satırlara sarılmış tek blok değil); başlık paragrafı
  her zaman kendi `Madde N-` paragrafından **hemen önce** gelir — bir sonraki
  maddenin başlığı, önceki maddenin metnine değil, kendi `Madde N-`
  paragrafına bitişik olarak ele alınmalıdır.
- Fıkralar `(1)`, `(2)` ... şeklinde kendi paragrafları olarak numaralanıyor;
  bazı maddelerde fıkra içinde `a) b) c)` gibi harfli alt bentler de ayrı
  paragraflar olarak var (bkz. Madde 1 örneği, §6).

## 4. Değişiklik Notları / Dipnotlar

- Madde metni içinde değişiklik geçmişi doğrudan parantez içinde belirtiliyor,
  ör: `Madde 3- (Değişik: 6/12/2006-5560/31 md.)`, `Ek Madde 1- (Ek:
  11/5/2005-5348/5 md.)`. Bu kısım normal paragraf metninin parçası, ayrıca
  bir işlem gerektirmiyor.
- Ayrı olarak, belgede **13 gerçek Word dipnotu** var — bunlar `word/footnotes.xml`
  adlı ayrı bir OOXML parçasında saklanıyor. **`python-docx`'in yüksek
  seviyeli `Document.paragraphs` API'si bu içeriği göstermiyor** — dipnot
  metnine ulaşmak için `document.part.package` üzerinden ilgili parçayı bulup
  `lxml` (zaten bir `python-docx` bağımlılığı) ile ayrıştırmak gerekti; bu,
  script içinde `extract_footnote_definitions()` fonksiyonuyla yapıldı,
  herhangi bir harici araç kullanılmadı.
- Madde metni içinde **13 adet `<w:footnoteReference>`** elemanı var (her
  dipnot numarasına bir referans) — bu, antiword'ün düz metin çıktısındaki
  "26 satır-içi `[N]` referansı" sayısından farklı görünüyor, ancak
  **içerik kaybı yok**: eski sayı hem gövde içi referansları hem de dipnot
  tanımlarının kendi satır başlarını (`[N] ...` ile başlayan 13 satır) aynı
  düz metin akışında saydığı için şişkindi (13 + 13 = 26). Yeni temsilde bu
  ikisi yapısal olarak ayrı: 13 gerçek referans + 13 gerçek tanım — aynı
  içerik, daha temiz/doğru bir yapı.
- Bu dipnotlar, ilgili fıkranın *önceki* halinin ne olduğunu ve hangi kanunla
  değiştirildiğini açıklıyor — hukuki doğruluk için değerli ama chunk
  metninden ayrı, ilişkili bir meta veri/ek içerik olarak ele alınmalı.

## 5. Tablo / Paragraf-Dışı Yapılar

- Belgenin sonunda bir **değişiklik/yürürlük tarihi tablosu** var — artık
  `Document.tables[0]` üzerinden gerçek bir Word tablosu olarak okunuyor:
  **20 satır (1 başlık + 19 veri satırı) × 3 sütun**. Sütunlar: değiştiren
  kanun/KHK (veya Anayasa Mahkemesi kararı), değişen/iptal edilen madde,
  yürürlüğe giriş tarihi.
  - Eski antiword tabanlı analizde bu tablo "42 pipe-delimited satır" olarak
    raporlanmıştı; bu sayı, antiword'ün uzun hücre metnini sabit genişlikte
    birden çok görsel satıra sarmasından kaynaklanan bir gösterim
    artefaktıydı — aynı 19 veri satırı, tam içerikle doğrulandı (bkz. script
    çıktısı), içerik kaybı yok.
- Bu tablo madde metninin bir parçası değil; ayrı bir referans yapısı olarak
  ele alınmalı (chunk'lanmamalı veya ayrı bir "amendment history" chunk türü
  olarak işaretlenmeli). `python-docx` ile artık madde akışından tamamen
  ayrı bir nesne (`Document.tables`) olduğu için, regex tabanlı madde
  parser'ının bu tabloyu yanlışlıkla bir madde/paragraf olarak algılama
  riski antiword'e göre daha düşük.

## 6. Örnekler

Aşağıdaki örnekler doğrudan `python-docx` paragraf listesinden alınmıştır
(script §8 çıktısı); önceki antiword tabanlı örneklerle karşılaştırıldığında
**metinsel içerik birebir aynı**, yalnızca satır sarma (word-wrap) farkı var.

**Normal madde (Madde 2):**
```
Madde 2- (1) Kabahat deyiminden; kanunun, karşılığında idarî yaptırım
uygulanmasını öngördüğü haksızlık anlaşılır.
```

**Çok fıkralı madde (Madde 11):**
```
Madde 11- (1) Fiili işlediği sırada onbeş yaşını doldurmamış çocuk
hakkında idarî para cezası uygulanamaz.
(2) Akıl hastalığı nedeniyle, işlediği fiilin hukukî anlam ve
sonuçlarını algılayamayan veya bu fiille ilgili olarak davranışlarını
yönlendirme yeteneği önemli derecede azalmış olan kişi hakkında idarî para
cezası uygulanmaz.
```

**Uzun madde, harfli alt bentli (Madde 1):**
```
Madde 1- (1) Bu Kanunda; toplum düzenini, genel ahlâkı, genel sağlığı,
çevreyi ve ekonomik düzeni korumak amacıyla;
a) Kabahatlere ilişkin genel ilkeler,
b) Kabahatler karşılığında uygulanabilecek olan idarî yaptırımların
türleri ve sonuçları,
c) Kabahatler dolayısıyla karar alma süreci,
d) İdarî yaptırıma ilişkin kararlara karşı kanun yolu,
e) İdarî yaptırım kararlarının yerine getirilmesine ilişkin esaslar,
Belirlenmiş ve çeşitli kabahatler tanımlanmıştır.
```

**Harfli madde (Madde 42/A):**
```
Madde 42/A- (2/7/2018-KHK-703/20 md.) (Başlığı ile Birlikte
Değişik:8/5/2025-7547/13 md.)
(1) 112 Acil Çağrı Merkezini meşgul etmek amacıyla arayarak görevlilerle
konuşan veya ısrarla çağrı bırakan kişiye, il valileri tarafından binbeşyüz
Türk Lirası idari para cezası verilir.
(2) 112 Acil Çağrı Merkezine yapılan ihbarın asılsız olduğunun olay yerine
giden ekiplerce tutanakla tespit edilmesi halinde kişiye, il valileri
tarafından onbeşbin Türk Lirası idari para cezası verilir.
(3) Bu maddede yazılı fiillerin bir yıl içinde tekrarı halinde idari para
cezası iki katı olarak uygulanır.
```

**Ek Madde örneği (Ek Madde 1):**
```
Ek Madde 1- (Ek: 11/5/2005-5348/5 md.)
(1) 4.1.1961 tarihli ve 213 sayılı Vergi Usul Kanununda yer alan vergi
mahkemelerinin görevine ilişkin hükümler saklıdır.
```

**Geçici Madde örneği (Geçici Madde 1):**
```
Geçici Madde 1- (1) Bu Kanunda ve 1 Haziran 2005 tarihinden sonra
yürürlüğe giren diğer kanunlardaki idarî para cezaları ile ilgili olarak
geçen "Türk Lirası" ibaresi karşılığında, uygulamada, 28.1.2004 tarihli ve
5083 sayılı Türkiye Cumhuriyeti Devletinin Para Birimi Hakkında Kanun
hükümlerine göre ülkede tedavülde bulunan para "Yeni Türk Lirası" olarak
adlandırıldığı sürece bu ibare kullanılır.
```

## 7. Korunabilecek Metadata

Madde/paragraf düzeyinde çıkarılabilecek ve `Article`/`Chunk` metadata'sına
taşınabilecek alanlar:

- `article_no` (ör. `"2"`, `"42/A"`, `"Ek Madde 1"`, `"Geçici Madde 1"`)
- `article_title` (madde başlığı paragrafı, ör. `"Sorumluluk"`) — çoğu
  maddede mevcut, bazı Ek/Geçici maddelerde başlık olmayabilir
- `document_id`, `document_type`, `legislation_number` (`data/source_manifest.json`'dan)
- Değişiklik notu (varsa, madde başlığındaki parantez içi ifade, ör.
  `"(Değişik: 6/12/2006-5560/31 md.)"`)
- Dipnot metni (varsa, `word/footnotes.xml`'den `python-docx`'in
  parça/lxml erişimiyle çıkarılabilir; ilgili `article_no` ile
  ilişkilendirilmeli — bkz. §9)
- `page`: **güvenilir değil**, birincil anahtar olarak kullanılmamalı (bkz. §2)

## 8. Ayrıştırma (Parsing) Riskleri

- **Regex kırılganlığı**: "Madde N-" kalıbı `-`, `–`, `—` gibi farklı tire
  karakterleriyle karşımıza çıkabilir; script bunu göz önünde bulundurdu
  ancak gerçek belge yalnızca `-` kullanıyor gibi görünüyor — başka
  kanunlarda farklılık gösterebilir.
- **Harfli madde numaraları** (`42/A`, `43/B`) normal `Madde N-` regex'i ile
  aynı önek altında yakalanabiliyor ama `article_id` üretirken `"/"`
  karakterinin dosya adı / Chroma metadata anahtarı olarak güvenli
  kullanılabilmesi için normalize edilmesi gerekecek (ör. `"42_A"`).
  - Ek Madde ve Geçici Madde, ana `Madde N` numaralandırmasından bağımsız,
   kendi içinde ayrı sayaçlar; `article_no` alanında bunları ayırt eden bir
   önek (`"ek-1"`, `"gecici-1"`) gerekecek, aksi halde `Ek Madde 1` ile
   `Madde 1` çakışabilir.
- **Dipnotlar ayrı bir OOXML parçasında**: `word/footnotes.xml` içeriği
  `Document.paragraphs` üzerinden **görünmez**; `ingest.py` bunu açıkça
  `document.part.package` + `lxml` ile okumazsa dipnot içeriği sessizce
  atlanır (hata vermez, sadece eksik kalır). Ayrıca bir dipnotun *hangi*
  maddeye ait olduğunu bulmak için `<w:footnoteReference w:id="N">`
  elemanının bulunduğu paragrafın en yakın önceki `Madde N-` paragrafına
  ait olduğu çıkarılmalı (referans ID'si dipnot tanımındaki `w:id` ile
  eşleştirilerek).
- **Başlık paragrafı sıralaması**: bir maddenin başlık paragrafı, önceki
  maddenin gövdesinden sonra değil, kendi `Madde N-` paragrafından hemen
  önce gelir (bkz. §3) — basit "bir sonraki `Madde` paragrafına kadar her
  şeyi al" mantığı, bir sonraki maddenin başlığını yanlışlıkla mevcut
  maddenin gövdesine dahil edebilir; parser başlığı bir sonraki `Madde N-`
  paragrafına *bitişik* olarak tanımalı.
- **Tablo yapısı** madde/fıkra akışının tamamen dışında; `Document.tables`
  ile ayrı bir nesne olarak geldiği için madde bazlı parser'ın bunu bir
  "madde" sanma riski düşük, ama yine de açıkça hariç tutulmalı.
- **Sayfa numarası yok**: yukarıda belirtildiği gibi, `page` alanı bu kaynak
  için doldurulamaz.

## 9. Önerilen Ingestion Stratejisi

Format normalizasyonu tamamlandı — kaynak artık geçerli bir `.docx`.
Önerilen `ingest.py` tasarımı:

1. `data/raw/` içinden `.docx` kaynağını bul, `python-docx` ile aç (harici
   CLI aracı yok, tek bağımlılık `requirements.txt`'teki `python-docx`).
2. `Document.paragraphs` üzerinde sırayla ilerleyip `KISIM`/`BÖLÜM`
   başlıklarını, `Madde N-`/`Ek Madde N-`/`Geçici Madde N-` kalıplarını her
   paragrafın **başında** (`re.match`, çok satırlı gövde metni değil, tek
   paragraf metni üzerinde) tanıyan bir state machine kurmak; her madde
   başlangıcının **hemen önceki** boş olmayan paragrafı başlık olarak almak.
3. Değişiklik geçmişi tablosunu `Document.tables` üzerinden madde akışından
   tamamen ayrı çıkarmak (chunk'lamaya dahil etmemek ya da ayrı işaretlemek).
4. Dipnotları `document.part.package` üzerinden `word/footnotes.xml`
   parçasını bulup `lxml` ile ayrıştırarak toplamak; her dipnotu, gövdedeki
   `<w:footnoteReference>` elemanının bağlı olduğu maddeye
   (`article.amendment_notes` gibi bir listeye) ilişkilendirmek, ana chunk
   metninden ayrı tutmak.
5. `page` alanını bu kaynak için `null` bırakmak; `legislation_number` +
   `article_no`'yu birincil anahtar yapmak.

## 10. Önerilen Chunk'lama Stratejisi

- **Madde bazlı chunk'lama** (AGENTS.md'de zaten belirtildiği gibi sabit
  boyutlu değil, mevzuat yapısına duyarlı):
  - Kısa/normal maddeler (ör. Madde 2, tek fıkra) → 1 madde = 1 chunk.
  - Çok fıkralı uzun maddeler (ör. çok sayıda `(N)` fıkrası olan maddeler)
    → gerekirse fıkra gruplarına bölünebilir, ama her parçada `article_no`
    ve madde başlığı (context olarak) korunmalı.
  - Harfli alt bentler (`a) b) c)`) bir fıkranın parçası olarak aynı chunk
    içinde kalmalı, ayrı chunk'lara bölünmemeli (anlam bütünlüğü için).
  - Ek Madde / Geçici Madde, normal maddelerle aynı mantıkla ama ayrı
    `article_no` önekiyle (`ek-1`, `gecici-1`) chunk'lanmalı.
- Her chunk'a en az şu metadata eklenmeli: `document_id`, `article_no`,
  `article_title`, `chunk_id`; `page` bu kaynak için mevcut değil.
- Artık güvenilir biçimde çıkarılabilen dipnot metni, ilgili maddenin
  chunk metadata'sına ek bilgi (`amendment_notes`) olarak eklenebilir.
- Değişiklik/dipnot tablosu ayrı, isteğe bağlı bir chunk türü olarak ele
  alınabilir ya da ilk sürümde tamamen atlanabilir (retrieval için düşük
  değer, ama "hangi madde ne zaman değişti" sorularına yanıt için ileride
  faydalı olabilir).

## 11. LegalDocument → Article → Chunk Modelinin Yeterliliği

`docs/data-model.md`'deki mevcut `LegalDocument → Article → Chunk` modeli bu
kaynak için **temelde yeterli**; mimariyi bu aşamada değiştirmeye gerek yok.
Ancak analiz iki ek kavramın **metadata veya parsing seviyesinde** faydalı
olacağını gösteriyor (mimari değişikliği değil, uygulama ayrıntısı olarak):

- **Section (Kısım/Bölüm) — metadata olarak faydalı:** Madde'nin hangi
  `KISIM`/`BÖLÜM` altında olduğu bilgisi (ör. "Birinci Kısım, İkinci Bölüm")
  bağlamsal bir sinyal olarak `Article` metadata'sına eklenebilir
  (`section_title` gibi bir alan). Bu, ayrı bir varlık/tablo gerektirmez;
  `Article` üzerinde isteğe bağlı bir alan olarak yeterlidir.
- **Paragraph (fıkra) — parsing kavramı olarak faydalı, ayrı varlık olarak
  gerekli değil:** Numaralı fıkralar (`(1)`, `(2)`...) madde içi
  chunk'lamada bölünme noktası olarak kullanılabilir (uzun maddeleri
  fıkra sınırlarında bölmek için). Bu bir *parsing/chunking mantığı*
  olarak `chunk.py` içinde ele alınabilir; `Chunk.metadata` içine
  `paragraph_no` gibi isteğe bağlı bir alan eklenmesi yeterli, ayrı bir
  `Paragraph` varlığına gerek yok.

Sonuç: **mimari değişmiyor**; `Article.metadata`/`Chunk.metadata` için
isteğe bağlı `section_title` ve `paragraph_no` alanları ileride
`chunk.py`/`ingest.py` uygulanırken eklenmesi önerilen ayrıntılardır.

## 12. Sayım Özeti ve Antiword Karşılaştırması

Aşağıdaki karşılaştırma, önceki antiword-tabanlı analiz (M1 ilk sürüm) ile
şimdiki `python-docx`-tabanlı analizin sonuçlarını gösteriyor.

| Ölçüm | Eski (antiword, `.doc`) | Yeni (`python-docx`, `.docx`) | Durum |
|---|---|---|---|
| Normal madde (`Madde N-`) | 45 | 45 | Aynı |
| Harfli madde (`Madde N/A-`) | 4 (42/A, 43/A, 43/B, 43/C) | 4 (42/A, 43/A, 43/B, 43/C) | Aynı |
| Ek Madde | 1 | 1 | Aynı |
| Geçici Madde | 3 | 3 | Aynı |
| **Toplam madde benzeri birim** | **53** | **53** | Aynı |
| Numaralı fıkra (`(N)`) | 105 | 105 | Aynı |
| Kısım/Bölüm başlığı | 6 | 6 | Aynı |
| Türkçe karakter korunumu | Doğrulandı | Doğrulandı | Aynı |
| Dipnot tanımı | 13 (metin bloğu) | 13 (`word/footnotes.xml`) | Aynı sayı, farklı temsil (bkz. §4) |
| Satır içi dipnot referansı | 26 (düz metin, `[N]` regex) | 13 (`<w:footnoteReference>`) | **Farklı görünüyor ama açıklanabilir** — bkz. aşağıda |
| Tablo satırı | 42 (pipe-delimited, satır sarmalı) | 20 (1 başlık + 19 veri, gerçek tablo) | **Farklı görünüyor ama açıklanabilir** — bkz. aşağıda |
| Form-feed/sayfa işareti | 0 | 0 (+ `docProps/app.xml` `Pages=18`, aynı türde güvenilmez istatistik) | Aynı sonuç |

**İki "farklı" satırın açıklaması:**
- *Satır içi dipnot referansı (26 → 13):* Eski sayı, antiword'ün düz metin
  çıktısında hem gövde içindeki referansları hem de dipnot tanımlarının
  kendi satır başlangıçlarını (`[N] ...`) aynı anda saydığı için şişkindi
  (13 gövde referansı + 13 tanım satırı = 26). Yeni sayı yalnızca gerçek
  gövde içi referansları (`<w:footnoteReference>`) sayıyor; tanımlar ayrıca
  13 olarak doğrulandı. **İçerik kaybı yok**, temsil daha doğru.
- *Tablo satırı (42 → 20):* Eski sayı, antiword'ün uzun hücre metnini sabit
  genişlikte birden fazla görsel satıra sarmasından kaynaklanıyordu. Yeni
  sayı gerçek mantıksal satır sayısı (1 başlık + 19 veri). Tüm 19 veri
  satırının içeriği tek tek karşılaştırıldı (script çıktısı) ve eski
  antiword dökümüyle **birebir örtüştüğü** doğrulandı. **İçerik kaybı yok**.

**Sonuç: dönüşüm yapısal olarak kayıpsız (structurally lossless)
görünüyor.** Tüm doğrudan karşılaştırılabilir sayımlar (madde sayıları,
fıkra sayısı, bölüm başlığı sayısı, dipnot tanım sayısı, Türkçe karakter
korunumu) birebir eşleşiyor; iki temsil farkı (dipnot referans sayımı, tablo
satır sayımı) tamamen açıklanabilir gösterim farklılıkları, içerik
kaybına işaret etmiyor. Bu belge, hukuki içeriğin doğruluğu üzerine bir
yargı içermiyor — yalnızca yapısal/metinsel korunumu değerlendiriyor.
