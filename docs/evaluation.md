


CSV raporundaki bu alanlar evaluator tarafından boş bırakılır:

- Hukuki doğruluk: 0 yanlış, 1 kısmen doğru, 2 doğru.
- Eksiksizlik: 0 maddi ölçüde eksik, 1 kısmen eky
- Atıf ilgisi: 0 desteklemiyor, 1 kısmen ilgili, 2 ilgili.
- Yeterlilik kararı: `correct`, `incorrect` veya `uncertain`.
- Güvensiz aşırı iddia: `yes` veya `no`.
- İnceleyen notları: serbest metin.

Bu puanlar yalnız insan/uzman incelemesinden sonra doldurulur. M9A bunları
otomatik doldurmaz ve hukuki cevap doğruluğunu tesis etmez.

Mevcut baseline'da yapısal öncelikli inceleme 1/15 (%6,7), tamamlanmış
insan/uzman hukuki incelemesi 0/15 ve bekleyen inceleme 15/15'tir. Diğer 14
yanıt hukuken incelenmiş, doğru veya uzman incelemesine ihtiyaç duymuyor
olarak sınıflandırılmaz.

## Yanıt Kalitesi (insan/uzman incelemesi gerekir)

| Metrik | Tanım | Sonuç |
|---|---|---|
| Answer correctness | Üretilen yanıtın referans yanıtla anlam olarak örtüşmesi | TBD |
| Citation correctness | Gösterilen kaynakların (belge/madde/sayfa) doğruluğu | TBD |
| Hallucination rate | Bağlamda olmayan bilgi üretme oranı | TBD |

## Kapsam Dışı / Sınır Durumlar

| Metrik | Tanım | Sonuç |
|---|---|---|
| Negative / out-of-scope questions | Gümrük mevzuatı dışı veya cevaplanamaz sorulara verilen tepki (uygun şekilde reddetme) | TBD |

## Performans ve Maliyet

| Metrik | Tanım | Sonuç |
|---|---|---|
| Ortalama retrieval latency | Soru başına retrieval süresi | 448,7 ms |
| Ortalama generation latency | Soru başına generation süresi | 2888,3 ms |
| Ortalama pipeline latency | Soru başına uçtan uca süre | 3347,2 ms |
| Token usage | Embedding / generation toplamı | 427 / 47088 |
| Estimated API cost | Token kullanımına dayalı tahmini OpenAI API maliyeti | TBD |

## Değerlendirme Seti

Değerlendirme doğrudan `tests/questions.json` içindeki 15 soru/kaynak çifti
üzerinden yürütülür; evaluator bu dosyayı değiştirmez veya çoğaltmaz.

## M9B: provisional benchmark ve iki aşamalı insan incelemesi

M9A'nın 15 soruluk tarihsel baseline'ı ve `e2e-baseline.*` artifact'ları
dondurulmuştur. M9B, bunları değiştirmeden `evaluation/questions_m9b.json`
içinde q016-q045 aralığında 30 yeni soru ekler. Açıkça seçilen
`python -m src.evaluate_e2e --benchmark m9b` modu seed ve extension
dosyalarını bu sırayla yükleyerek 45 soruluk provisional structural benchmark
çalıştırır; argümansız komut hâlâ yalnız 15 soruluk M9A baseline'ıdır.

Extension'daki izinli `case_type` değerleri `paraphrase`,
`exception_condition`, `multi_part`, `long_tail` ve `ambiguity_resistant`;
zorluk değerleri `easy`, `medium` ve `hard` ile sınırlıdır.

`source_verified=true`, soru ile beklenen madde eşlemesinin yerel işlenmiş
5326 Kabahatler Kanunu metninden doğrudan kontrol edildiğini belirtir. Bu,
bir hukuk/gümrük uzmanı onayı değildir. `expert_validated=false`, gerçek bir
uzman karar verene kadar otomatik olarak değiştirilemez.

İnsan incelemesi iki bağımsız aşamadır:

1. `m9b-question-review.csv`, benchmark sorusunun açıklığını, doğallığını,
   beklenen maddesini, mevcut corpus'tan cevaplanabilirliğini ve belirsizliğini
   inceler. Bütün satırlar `review_status=pending` başlar; otomatik onay yoktur.
2. `m9b-answer-review.csv`, 45 sistem cevabının hukuki doğruluğu,
   eksiksizliği, groundedness'ı, atıf ilgisi, yeterlilik kararı ve güvensiz
   aşırı iddia bakımından daha sonra insanlarca puanlanması içindir. Puanlar
   başlangıçta boştur.

M9B Recall@K, beklenen madde presence/cited oranları ve priority-review
işaretleri yalnız yapısal tanılamadır. Bunlar chatbot accuracy veya hukuki
cevap doğruluğu değildir. M9B yeni mevzuat eklemez; yalnız mevcut 5326
corpus'una ilişkin değerlendirme kapsamını genişletir.

## M10D: çok kanunlu retrieval değerlendirme sözleşmesi

M10D retrieval-only değerlendirmedir; cevap üretimi veya hukuki cevap
puanlaması içermez. M9A/M9B'nin tarihsel semantiği ve donmuş sonuçları değişmez.

`QualifiedSourceKey = (legislation_number, article_type, normalized_article_no)`.
Madde numarası mevcut `normalize_article_no` kuralıyla normalize edilir.
`article_no` tek başına yeterli değildir: farklı kanunların aynı numaralı
maddeleri ve aynı kanundaki normal, ek ve geçici maddeler farklı kaynaklardır.

K = 1, 3, 5 için metrikler:

- **ANY Qualified Recall@K:** Top-K içinde beklenen QualifiedSourceKey
  kümesinden en az biri bulunan soruların oranı.
- **ALL Qualified Match@K:** Beklenen benzersiz QualifiedSourceKey'lerin
  tamamı Top-K içinde bulunan soruların oranı. Aynı kaynaktan birden fazla
  chunk gelmesi ek bir beklenen kaynak karşılamaz.
- **Legislation Hit@K:** Top-K içinde beklenen kanunlardan en az birinin
  bulunduğu soruların oranı; doğru maddeyi bulma koşulu aranmaz.
- **Top-1 legislation retrieval confusion matrix:** Satır beklenen kanun,
  sütun ilk getirilen chunk'ın kanunudur. Eksik Top-1 metadata ve retrieval
  hataları ayrıca raporlanır; birden fazla kanun bekleyen sorular dışlanır.
- **non-expected-legislation share@5 / cross-law intrusion diagnostic:**
  İlk beş sonuçtaki kullanılabilir kanun metadata'sına sahip chunk'lar
  arasında beklenen kanun kümesi dışındakilerin payıdır. Payda kullanılabilir
  sonuç sayısıdır; hiç yoksa değer `null` olur. Özet, tanımlı soru paylarının
  ortalamasıdır. Diğer kanundan sonuç hukuken ilgili olabileceğinden bu,
  hukuki hata oranı değildir.

### Donmuş 5326 PRE / POST regresyon yöntemi

Aynı 45 soru ve beklenen kaynaklar korunur. PRE soru bazlı sıralı sonuçları
yalnız donmuş [m9b-provisional.json](../reports/evaluation/m9b-provisional.json)
dosyasından gelir; retrieval yeniden çalıştırılmaz. Tarihsel
`retrieved_chunk_ids`, saklanan 5326 chunk kimlik metadata'sıyla eşleştirilerek
normal/ek/geçici ayrımı çözülür; yalnız madde numarasından tür çıkarılmaz.
Bu adaptasyon tarihsel M9B raporunu veya evaluator semantiğini değiştirmez.
POST, 4458 eklendikten sonraki kabul edilmiş ortak corpus çalıştırmasının
5326 alt kümesidir. Soru ID kümeleri tam eşleşmelidir; ANY ve ALL @1/3/5
oranları, farkları ve iyileşen/kötüleşen soru ID'leri karşılaştırılır.
PRE sonuçları anlatıdan veya toplu skorlardan türetilmez.

### İnceleme durumu ve kapsam

`source_verified`, soru/beklenen kaynak eşlemesinin kaynak metinden kontrol
edildiğini belirtir. `gold_human_approved`, benchmark sorusu ve beklenen
kaynakların insan tarafından gold olarak onaylanmasını ifade eder;
`source_verified` bunu kendiliğinden sağlamaz. `expert_validated`, ayrı bir
uzman doğrulamasıdır ve gerçek uzman incelemesi olmadan true yapılamaz.
Bu durumlar birbirinin yerine geçmez ve retrieval başarısı hukuki cevap
onayı sağlamaz. Her iki kanundan birlikte kanıt gerektiren gerçek cross-law
sorular ertelenmiştir.

### Donmuş M10D baseline

Yetkili sonuçlar: [JSON](../reports/evaluation/m10d-two-law-retrieval.json)
ve [CSV](../reports/evaluation/m10d-two-law-retrieval.csv).
Aşağıdaki değerler yüzdedir:

| Alt küme | Soru | ANY@1 / @3 / @5 | ALL@1 / @3 / @5 |
|---|---:|---|---|
| 5326 POST | 45 | 75.6 / 86.7 / 95.6 | 64.4 / 82.2 / 88.9 |
| 4458 | 30 | 56.7 / 73.3 / 80.0 | 46.7 / 66.7 / 76.7 |
| Combined | 75 | 68.0 / 81.3 / 89.3 | 57.3 / 76.0 / 84.0 |

Top-1 legislation hit: **72/75 = 96.0%**.
**These are retrieval metrics, not legal-answer accuracy.**

JSON'un soru bazlı `expected_sources` kümesi ile ilk beş `ranks` kaydının
`qualified_source_key` kümesi kesişimi boş olan **8 soru** vardır:
q002, q042, gk004, gk012, gk014, gk019, gk020, gk028.
Bu sayı ANY@5 başarısızlığıdır; kısmi çok-kaynak eşleşmeleri dahil tüm
ALL@5 başarısızlıklarının sayısı değildir.

Donmuş raporun önce/sonra üretim Chroma envanteri aynıdır:
5326 = 53, 4458 = 276, toplam = 329. Bu kayıt canlı Chroma erişimi
gerektirmeden rapor metadata'sından kontrol edilebilir.
