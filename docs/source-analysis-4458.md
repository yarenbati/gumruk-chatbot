# 4458 Gümrük Kanunu kaynak ve yapı analizi (M10A)

## 1. Kaynak kimliği ve dönüşüm provenance'ı

- Belge: **Gümrük Kanunu**
- Kanun numarası: **4458**
- Belge türü / yetkili makam: **Kanun / TBMM**
- Resmî mevzuat sayfası: <https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=4458&MevzuatTur=1&MevzuatTertip=5>
- Resmî indirme uç noktası: <http://www.mevzuat.gov.tr/MevzuatMetin/1.5.4458.doc> (sunucu HTTPS'e yönlendirir)
- Erişim tarihi: **2026-09-03**

| Dosya | Rol | Boyut | SHA-256 |
|---|---|---:|---|
| `data/raw/4458-gumruk-kanunu.doc` | Değiştirilmeden korunan resmî legacy Word kaynağı | 828.928 bayt | `9F125CB2DD0C1084FF2B2A854C729B2D71B171E6A75644038B57CDD53B2DA98A` |
| `data/raw/4458-gumruk-kanunu.docx` | Pipeline için normalize edilmiş çalışma türevi | 177.526 bayt | `2B1A63B1D80FD32A7E223BC4146CE38DC84EB4A70A1BE11FCF51B7661BB4BED3` |

Dönüşüm zinciri: resmî mevzuat.gov.tr legacy DOC → Microsoft Word'de elle
**Farklı Kaydet** → normalize DOCX. DOCX doğrudan mevzuat.gov.tr'den indirilmiş
gibi değerlendirilmez. Özgün `.doc` silinmemiş veya değiştirilmemiştir.

DOCX imzası `50 4B 03 04 14 00 06 00` olup dosya geçerli bir ZIP/OOXML
paketidir. `[Content_Types].xml`, `_rels/.rels`, `word/document.xml` ve
`word/_rels/document.xml.rels` mevcuttur; `python-docx` belgeyi doğrudan açmıştır.
Pakette ayrıca `word/footnotes.xml` ve `word/endnotes.xml` parçaları vardır.

## 2. Bağımsız DOCX yapı envanteri

Bu bölümün ölçümleri `src.chunk.parse_articles()` kullanılmadan, `python-docx`
paragraf/tablo görünümü ve doğrudan OOXML parçaları üzerinden çıkarılmıştır.

| Ölçüm | Sonuç |
|---|---:|
| Word paragrafı | 1.878 |
| Boş olmayan paragraf | 1.586 |
| Tablo | 1 |
| Kısım başlığı | 13 |
| Bölüm başlığı | 37 |
| Ayırım başlığı | 14 |
| Normal, suffix içermeyen `Madde` | 248 |
| Suffixed/lettered `Madde` | 11 |
| `Ek Madde` | 0 |
| Ana kanuna ait `Geçici Madde` | 11 |
| Kanuna işlenemeyen hüküm altındaki özel `Geçici Madde` | 1 |
| Toplam article-like unit | 271 |

Ana hiyerarşi 13 Kısım ve bunların altında 37 Bölümden oluşur. Belge ayrıca
14 `AYIRIM` düzeyi ile `A.`, `B.`, `I.`, `II.` gibi alfabetik/Roma rakamlı
alt başlıklar kullanır. Paragrafların çoğu `Nor.` stilindedir; başlıklar için
`kısımbölüm`, `kısımbölümaltı` ve `Madde Baslığı` stilleri kullanılmıştır.
Stiller kusursuz semantik işaret değildir: bazı gerçek madde başlıkları ve
gövdeleri `kısımbölümaltı`, Madde 222 ise `Normal (Web)` stilindedir; bir normal
gövde paragrafı da `Madde Baslığı` stilindedir.

Suffixed numaralar:

`5/A`, `10/A`, `35/A`, `35/B`, `35/C`, `165/A`, `165/B`, `165/C`, `165/D`,
`191/A`, `218/A`.

İlk dokuzunda kaynak yazımı sayı ile slash arasında boşluk içerir (`Madde 35 /A –`);
son ikisi bitişiktir (`Madde 191/A –`). Beklenmeyen fakat tutarlı biçim budur.
Başlıklarda 267 en dash ve 4 ASCII hyphen kullanılmıştır. 271 article-like
başlığın hepsinde dash sonrasında aynı paragrafta en az bir metin/not vardır;
220'sinde baştaki değişiklik notları çıkarıldıktan sonra da esas hüküm metni
aynı satırda başlar, 51'i yalnız değişiklik/mülga notuyla başlar.

Ana kanunun 11 Geçici Maddesinden sonra Madde 247 ve 248 gelir. Ardından
`4458 SAYILI KANUNA İŞLENEMEYEN HÜKÜMLER` başlığı altında başka bir kanunun
`Geçici Madde 1` metni yer alır. Bu bir ana-kanun Geçici Madde 1 tekrarı olarak
sınıflandırılmamalı; provenance/namespace'i ayrı bir özel article türüdür.

## 3. Fıkra, bent, mülga ve değişiklik yapıları

- Kaynak fıkraları `(1)` biçiminde değil, ağırlıkla `1.`, `2.` biçiminde ayrı
  paragraflardır: bu desene uyan **450** paragraf vardır; `(N)` ile başlayan
  paragraf sayısı **0**'dır.
- Harfli bent olarak `a)`, `b)` vb. ile başlayan **454** paragraf vardır.
- Numaralı alt düzeylerin metinde `1.`, `2.` biçimi kullanması, fıkra ile numaralı
  alt bendin salt regex ile her zaman ayrıştırılamayacağı anlamına gelir; bağlam
  korunarak ele alınmalıdır.
- `Mülga` sözcüğü içeren **20** paragraf vardır. Madde 42, 43, 44, 222, 240,
  244 ve 245 başlıklarında görülür; Madde 244 aynı başlıkta yeniden düzenleme
  notu da taşır. Diğer örnekler mülga fıkra/bentlerdir. Mevcut parser başlıkta
  yakaladıklarını genel madde olarak tutar ve önde gelen notu `amendment_note`
  alanına kopyalar; ayrı bir yürürlük/mülga durumu modeli yoktur.
- Inline `(Değişik: ...)`, `(Ek: ...)`, `(Mülga: ...)` veya `(İptal: ...)`
  işareti içeren **190** paragraf vardır. Mevcut parser yalnız tanıdığı madde
  başlığındaki öndeki notlar için **43** `amendment_note` alanı üretir; diğer
  notlar çoğunlukla `Article.text` içinde kalır.

## 4. Dipnotlar, endnote'lar ve tablo

- Gövde OOXML'inde **154** `footnoteReference` öğesi ve `footnotes.xml` içinde
  **154** gerçek dipnot gövdesi vardır. Referanslarda 153 benzersiz ID bulunur;
  bir ID birden fazla yerde kullanılmıştır.
- Ingest bütün 153 benzersiz referans ID'sini ilgili paragraf metadata'sında
  korur, ancak dipnot gövdelerini paragraf metnine eklemez.
- Parser-produced Articles üzerinde 148 benzersiz ID kalır. ID `1`, `2`, `35`,
  `38`, `124`; belge başlığı veya Kısım/Bölüm başlıklarına bağlı oldukları için
  hiçbir Article'a taşınmaz.
- `word/endnotes.xml` pakette bulunur fakat gerçek endnote referansı ve gövdesi
  **0**'dır (yalnız Word'ün ayırıcı altyapısı vardır).
- Tek tablo 35 satır × 3 sütundur; 105 hücrenin tamamı doludur. Tablo, değiştiren
  kanun/KHK/AYM kararı, değişen maddeler ve yürürlük tarihlerini gösteren hukuken
  anlamlı değişiklik geçmişidir. `Document.paragraphs` ve mevcut ingest tabloyu
  dışarıda bırakır. Parser zaten hemen önceki `4458 SAYILI KANUNA EK VE
  DEĞİŞİKLİK...` marker'ında durur; esas madde metniyle karışmaz, fakat değişiklik
  provenance'ı pipeline çıktısında bulunmaz.

## 5. Ingestion dry run

`python -m src.ingest data/raw/4458-gumruk-kanunu.docx` başarıyla çalıştı ve
`data/processed/4458-gumruk-kanunu.paragraphs.json` dosyasına 1.586 paragraf
yazdı. Çıktı ignored çalışma ürünüdür.

- Boş olmayan DOCX paragrafları ile ingest çıktısı sıra, özgün paragraf index'i
  ve normalize metin bakımından **1.586/1.586 bire bir aynıdır**.
- Türkçe `ı, ğ, Ğ, ş, Ş, ö, Ö, ü, Ü, ç, Ç, İ` karakterleri gözlenmiştir;
  Unicode replacement karakteri yoktur.
- Madde ve başlık paragrafları görünür kalmıştır.
- Paragraf akışında belirgin metin kaybı yoktur.
- Bilinen kapsam dışı yapılar: 154 dipnot gövdesi ve 35×3 değişiklik tablosu.
  Bunlar sessizce esas madde metni sayılmamış, yukarıda risk olarak kaydedilmiştir.

## 6. Mevcut parser ile dry run karşılaştırması

Bağımsız envanter **271**, mevcut parser **262** Article üretmiştir: 250 normal
(248 base + yalnız 2 tanınan suffix) ve 12 `gecici`.

Somut farklar:

1. Parser `Madde N/A` biçimini tanır, fakat `Madde N /A` biçimini tanımaz.
   Eksik dokuz unit: `5/A`, `10/A`, `35/A`, `35/B`, `35/C`, `165/A`, `165/B`,
   `165/C`, `165/D`.
2. `5/A` ve `10/A`, açık olan Madde 5 ve 10 gövdelerine başlıklarıyla birlikte
   yutulur. `35/A-C` bir Bölüm başlığından, `165/A-D` bir Kısım başlığından sonra
   geldiği için açık Article yoktur ve bu maddelerin bütün metni atlanır.
3. `191/A` ve `218/A` doğru tanınır.
4. `4458 SAYILI KANUNA İŞLENEMEYEN HÜKÜMLER` altındaki ayrı `Geçici Madde 1`,
   ana kanunun Geçici Madde 1'i gibi sınıflanır. Sonuçta
   `4458-gecici-madde-1` ve `...-chunk-001` duplicate ID olur.
5. Madde 248, işlenemeyen hükümler başlığını ve kaynak açıklama satırını kendi
   gövdesine alır; bu bir sınır hatasıdır.
6. Parser ordinal sözlüğü yalnız Onuncu'ya kadardır. `ONBİRİNCİ`, `ONİKİNCİ`,
   `ONÜÇÜNCÜ KISIM` tanınmaz; Madde 231'den sonraki **30 parser kaydı** eski
   `Onuncu Kısım` bağlamını taşır.
7. `AYIRIM` ve alfabetik/Roma rakamlı alt başlıklar `section_context` içinde
   modellenmez. 14 Ayırım başlığı önceki madde metnine karışabilir; alt başlıklar
   çoğu zaman yalnız takip eden ilk maddenin `article_title` alanına dönüşür.
8. Genel title sezgiseli üç yasal gövde satırını yanlışlıkla sonraki maddenin
   başlığı yapar: Madde 188→189, 190→191 ve 221→222 sınırlarında kısa
   `(Mülga ...)` satırları semantik olarak yanlış Article'a taşınır. Madde 222
   ayrıca `İKİNCİ AYIRIM` metnini gövdesine alır.
9. Boş veya 40 karakterden küçük Article/Chunk yoktur. Hatalı sınırlar nedeniyle
   bazı metinler mevcut olmakla birlikte yanlış Article'a bağlıdır; bazı suffixed
   maddeler ise bütünüyle yoktur.

## 7. Uyumluluk matrisi

| Construct | 4458 örneği / oluşum | Mevcut destek ve gözlenen sonuç | Risk | M10B eylemi |
|---|---|---|---|---|
| `Madde N` | 248 base; `Madde 1 – ...` | Tanınıyor | Düşük; alt yapı/sınır riskleri ayrı | Regresyon testi |
| Bitişik suffix | `191/A`, `218/A` | Tanınıyor | Düşük | Mevcut davranışı koru |
| Boşluklu suffix | 9 adet; `Madde 35 /A –` | Tanınmıyor | İki madde birleşiyor, yedi madde tamamen kayboluyor | Slash çevresinde whitespace kabul et; 9 fixture testi |
| `Ek Madde` | Yok | Kod desteği var ama 4458 kanıtı yok | Yok | 4458'e özgü değişiklik gerekmez |
| Ana `Geçici Madde` | 11 | Tanınıyor | Sonraki özel hükümle ID çakışması | Belge-sonu özel bölüm sınırı/type desteği |
| İşlenemeyen hüküm | Ayrı `Geçici Madde 1` | Ana `gecici` olarak yanlış sınıflanıyor | Duplicate article/chunk ID | Özel heading marker ve provenance namespace'i |
| Aynı satır başlık/gövde | 220 esas metinli, 51 note-only | Tanınıyor | Düşük | Regresyon testi |
| Numaralı fıkra | 450 adet `1.` biçimi; `(1)` yok | Chunker yalnız `(N)` tanır | Uzun maddeler bölünmüyor | Noktalı fıkra örüntüsünü bağlam-duyarlı destekle |
| Harfli bent | 454 adet `a)` vb. | Metinde korunuyor | Fıkra ayrımı olmadığı için büyük blokta kalıyor | Parent fıkra ile atomik tutan testler |
| Numaralı alt düzey | `1.`, `2.` yoğun | Ayrı semantik seviye yok | Fıkra/alt bent belirsizliği | Kaynak sırası ve bağlamla sınıflandır |
| Kısım/Bölüm | 13/37 | Kısmen; yalnız Kısım 1–10 | 30 kayıtta yanlış Kısım | Ordinal desteğini en az 13'e genişlet |
| Ayırım/alt başlık | 14 Ayırım + alfabetik/Roma başlıkları | `section_context` desteği yok | Başlık gövdeye karışıyor veya title'a indirgeniyor | Hiyerarşik context modelini genişlet |
| Mülga | 20 paragraf; 7 madde başlığı | Metin/not olarak kısmen korunuyor | Durum metadata'sı yok; title sezgiseli üç satırı taşır | Mülga durumunu ve title sınırını test et |
| Değişiklik notu | 190 paragraf | Başlıkta 43 structured note; kalanı metin | Eksik structured provenance | Inline notları kaybetmeden ayrı metadata tasarla |
| Dipnot | 154 ref/154 body | Ref ID ingestte; body yok; 5 ID Article'a ulaşmıyor | Değişiklik açıklaması erişilemez | Footnote body map ve document/section düzeyi refs |
| Endnote | Gerçek içerik yok | Gerek yok | Yok | Değişiklik gerekmez |
| Tablo | 1 adet, 35×3 değişiklik geçmişi | Ingest görmez; parser marker'da durur | Amendment provenance dışarıda | Esas chunklardan ayrı diagnostic/provenance modeli |
| Title sezgiseli | 3 yanlış `(Mülga...)` transferi | Yanlış Article title ve sınır | Semantik sahiplik bozulur | Stil/yapı temelli, muhafazakâr title tespiti |

## 8. Chunking ve rekonstrüksiyon diagnostic'i

Mevcut 262 parser Article'ından **262 aday Chunk** üretilmiştir. Kaynakta
chunker'ın beklediği `(N)` fıkra biçimi hiç bulunmadığı için hiçbir Article kendi
başına birden fazla chunk üretmemiştir.

- En büyük Article ve Chunk: `4458-madde-3`, **7.847 karakter**.
- `MAX_CHUNK_CHARS=4000` üstündeki chunk: **5** — Madde 3 (7.847), Madde 241
  (6.906), Madde 235 (6.316), Madde 167 (5.930), Geçici Madde 6 (5.787).
- Boş veya 40 karakterden küçük chunk: **0**.
- Duplicate article ID: `4458-gecici-madde-1`.
- Duplicate chunk ID: `4458-gecici-madde-1-chunk-001`.

Her Article tek chunk olduğundan mekanik `Chunk.text == Article.text` kontrolü
**262/262 pass, 0 fail** vermiştir. Bununla birlikte yukarıdaki kaynak sınırı
hataları nedeniyle bu sonuç parser doğruluğunu kanıtlamaz. Dokuz eksik unit hiç
kontrole giremez; yanlış birleşme/title/özel-bölüm etkisindeki 11 parser kaydı
kaynak-semantik rekonstrüksiyon açısından güvenilir kabul edilmemiştir.

## 9. Çok-belgeli ID kontrolü

4458 gerçek diagnostic çıktısı `4458-madde-13-chunk-001` biçimindedir. Üretim
Chroma'daki 53 adet 5326 ID'si ile 4458 aday ID kümesinin kesişimi **0**'dır.
Belge kapsamlandırması çalışmaktadır; tek collision, yukarıdaki aynı belge içindeki
iki farklı `Geçici Madde 1`in yanlış aynı tipe alınmasından kaynaklanır.

## 10. M10B gerekli değişiklikleri

1. **Boşluklu suffix tanıma:** mevcut regex `N/A` bekliyor; 4458 dokuz kez
   `N /A` kullanıyor ve madde kaybı/birleşmesi doğuruyor. Slash çevresi whitespace
   toleranslı yapılmalı; 5/A, 10/A, 35/A-C, 165/A-D örnekleri test edilmeli.
2. **Noktalı fıkra chunking'i:** mevcut chunker yalnız `(N)` sınırında böler;
   4458'de 450 `N.` paragrafı ve sıfır `(N)` vardır. Fıkra/numaralı alt bent bağlamı
   ayrıştırılmalı, harfli bentler parent fıkradan koparılmamalı; beş oversized
   madde ve kayıpsız rekonstrüksiyon test edilmeli.
3. **Kısım ordinal kapsamı:** parser Onbirinci–Onüçüncü Kısım başlıklarını
   kaçırıp 30 kayda yanlış context veriyor. Ordinal tanıma genişletilmeli ve
   Madde 231/242/246/Geçici 1/247 fixture'ları eklenmeli.
4. **Ayırım ve alt-hiyerarşi:** 14 Ayırım ile alfabetik/Roma rakamlı başlıklar
   mevcut modele alınmalı veya en azından madde metnine karışmaları engellenmeli;
   nested section-context ve Madde 4/222 sınır testleri eklenmeli.
5. **İşlenemeyen hükümler sınırı/type'ı:** ayrı Geçici Madde 1 ana kanunla
   çakışıyor ve Madde 248 kirleniyor. Marker ve ayrı provenance/type/namespace
   tasarlanmalı; duplicate ID ile Madde 248 sınır testi eklenmeli.
6. **Muhafazakâr title tespiti:** kısa mülga gövde satırları Madde 189, 191 ve
   222'ye title olarak taşınıyor. Stil ve structural heading kanıtı gerektiren
   title kuralı uygulanmalı; üç negatif fixture eklenmeli.
7. **Dipnot/değişiklik provenance'ı:** 154 footnote body erişilebilir olduğu halde
   Article modelinde yok ve heading refs kayboluyor. Esas madde metnine karıştırmadan
   body map/document-level provenance tasarlanmalı; 5 kayıp heading ref'i ve 154
   gövde eşleme testi eklenmeli.
8. **Değişiklik tablosu:** 35×3 tablo esas retrieval chunk'ı yapılmamalı, fakat
   source provenance diagnostic'inde kaybolmamalı. Ayrı amendment-history çıktısı
   ve tablo-sıra/başlık testi eklenmeli.

Bu belge M10A sonunda **indekslemeye hazır ilan edilmemiştir**. Hiçbir embedding
üretilmemiş, Chroma'ya yazılmamış ve üretim RAG davranışı değiştirilmemiştir.

## 11. M10B parser/chunker uyumluluk sonucu

### M10A'da gözlenen sorunlar

M10A; slash çevresindeki boşluk nedeniyle dokuz suffix'li maddenin
tanınmadığını, `N.` fıkralarında bölme yapılmadığını, 11–13. Kısım ve
Ayırım bağlamının kaybolduğunu, işlenemeyen hükümlerdeki ikinci Geçici
Madde 1'in ID çakışması yarattığını ve üç kısa Mülga fıkranın sonraki
maddeye başlık olarak taşındığını saptamıştı.

### M10B'de uygulanan düzeltmeler

- `Madde N/A`, `N /A`, `N/ A` ve `N / A` aynı canonical `N/A` değerine
  normalize edilir; ID biçimi değişmemiştir.
- Parenthesized `(N)` desteği korunmuş, `N.` için madde içinde 1'den başlayan
  ve ardışık ilerleyen bağlamsal fıkra dizisi eklenmiştir. Harfli bent ve
  devam satırları bir sonraki geçerli fıkra sınırına kadar sahibiyle atomiktir.
- Ordinal desteği Onbirinci, Onikinci ve Onüçüncü'ye genişletilmiş;
  Ayırım mevcut `section_context` yoluna üçüncü seviye olarak eklenmiştir.
- `KANUNA İŞLENEMEYEN HÜKÜMLER` altındaki birim nötr yapısal
  `islenemeyen_hukum` türüyle modellenir. ID
  `4458-islenemeyen-hukum-gecici-madde-1`, bölüm marker'ı
  `section_context`, kaynak açıklama satırı ise `article_title` olarak korunur.
- Title sezgiseli parantez veya `N.` ile başlayan gövde satırlarını title
  kabul etmez. Meşru kısa başlıklar korunur.

### Post-fix doğrulama

Bağımsız 271 article-like birimin tamamı 271 `Article` kaydına eşlendi:
259 `normal` (248 suffix'siz + 11 suffix'li), 11 ana-kanun `gecici` ve 1
`islenemeyen_hukum`. Eksik birim ve duplicate Article/Chunk ID sayısı sıfırdır.
On bir suffix'in tamamı (`5/A`, `10/A`, `35/A`, `35/B`, `35/C`, `165/A`,
`165/B`, `165/C`, `165/D`, `191/A`, `218/A`) temsil edilir.

Varsayılan 4000 karakterlik yumuşak hedefte 276 aday chunk ve 5 multi-chunk
Article oluştu. En büyük Article Madde 3 (7847), en büyük Chunk Madde 24
chunk-001 (3992) oldu; 4000 üstü chunk kalmadı. Bu bir sert limit sonucu
değil, gerçek fıkra sınırlarının elvermesinin sonucudur. 271/271 Article
chunklardan metin kaybı, tekrar veya sıra değişikliği olmadan bire bir yeniden
kuruldu. Madde 231 Onbirinci, 242 Onikinci, 246 ve 247 Onüçüncü Kısım
bağlamı taşır; Onuncu Kısım sızıntısı kalmadı. 188→189, 190→191 ve
221→222 Mülga sınırları doğrulandı.

5326 regresyonunda 53 Article ve 53 mevcut deterministic Chunk ID aynen
korundu; 53/53 canonical Article metni yeniden kuruldu. Normal testler ham
4458 DOCX'e bağlı değildir; yerel processed diagnostic testi dosya yoksa skip
olur. M10B embedding veya indeksleme yapmamış, üretim Chroma koleksiyonunu
değiştirmemiştir.

### Ertelenen kapsam

Dipnot gövdelerinin ve heading-level dipnot provenance'ının ayrı modeli ile
35×3 değişiklik tablosunun ayrı provenance çıktısı sonraki kilometre taşına
ertelenmiştir. Inline değişiklik notları ve mevcut dipnot referansları
korunur; dipnot gövdeleri Article metnine enjekte edilmez ve tablo semantic RAG
chunk'ı yapılmaz. Bu sonuç parser/chunker uyumluluğunu destekler; 4458'in
indekslenmesi M10C kapsamındadır.
