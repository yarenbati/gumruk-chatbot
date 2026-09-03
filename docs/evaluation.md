# Değerlendirme Planı

Bu belge retrieval ölçümünü ve M9A uçtan uca yapısal QA sınırını tanımlar.
Mevcut 15 soru kaynak metinden türetilmiştir ve tümünde
`expert_validated=false` değerindedir. Sonuçlar hukuki doğrulama veya
profesyonel kullanıma uygunluk kanıtı değildir.

## Retrieval Metrikleri

| Metrik | Tanım | Sonuç |
|---|---|---|
| Recall@1 | Beklenen maddelerden herhangi biri ilk sırada mı | 12/15 = %80,0 |
| Recall@3 | Beklenen maddelerden herhangi biri ilk 3 sonuç içinde mi | 13/15 = %86,7 |
| Recall@5 | Beklenen maddelerden herhangi biri ilk 5 sonuç içinde mi | 14/15 = %93,3 |

## M9A uçtan uca yapısal QA

`src/evaluate_e2e.py`, her soruda üretim bileşimi `rag.run_rag(question)`
fonksiyonunu bir kez çağırır. Otomatik ölçülen alanlar: beklenen maddenin
retrieval içinde bulunması ve ilk sırası; YETERLI/YETERSIZ durumu; doğrulanmış
atıfların varlığı, etiket yapısı ve madde numaraları; beklenen maddenin
doğrulanmış atıflar arasında bulunması; latency, sağlayıcının bildirdiği token
kullanımı ve operasyonel hatalardır.

`expected_article_cited_rate`, yalnızca "beklenen bir madde doğrulanmış atıf
metadata'sında bulundu" demektir; bir accuracy veya hukuki doğruluk metriği
değildir. `requires_priority_review` yalnızca deterministik yapısal triyaj
bayrağıdır. `requires_priority_review=false`, sadece "otomatik bir yapısal
anomali öncelikli incelemeyi tetiklemedi" anlamına gelir. İnsan/hukuk
incelemesinin gereksiz olduğu anlamına gelmez.

Tarihsel `Recall@1`, `Recall@3` ve `Recall@5`, soru düzeyinde ANY-match
metrikleridir: ilk K sonuçta beklenen maddelerden en az birinin bulunması
yeterlidir. Çok maddeli sorular için ayrıca `all_match_at_1/3/5` raporlanır;
bu metrik, normalize edilmiş beklenen madde kümesinin ilk K retrieval madde
kümesinin alt kümesi olmasını, yani bütün beklenen maddelerin bulunmasını
gerektirir. ALL-match doğrudan ilk K kümesinden hesaplanır; ilk beklenen sıra
alanından türetilmez.

Benzer şekilde `expected_article_cited_rate` en az bir beklenen maddenin,
`all_expected_articles_cited_rate` ise bütün beklenen maddelerin doğrulanmış
atıflar arasında bulunma oranıdır. ANY ve ALL ölçümleri yapısal tanılamadır;
hiçbiri hukuki accuracy değildir.

M9A ikinci bir model çağırmaz ve LLM-as-judge kullanmaz. Hukuki doğruluk,
yorumun eksiksizliği, her iddianın semantik olarak kanıtlanması, hukuken en
iyi kaynağın seçilmesi, yeterlilik kararının hukuken doğruluğu ve profesyonel
kullanım güvenliği insan/uzman incelemesi gerektirir.

## İnsan inceleme rubriği

CSV raporundaki bu alanlar evaluator tarafından boş bırakılır:

- Hukuki doğruluk: 0 yanlış, 1 kısmen doğru, 2 doğru.
- Eksiksizlik: 0 maddi ölçüde eksik, 1 kısmen eksik, 2 yeterince eksiksiz.
- Kaynağa dayanma: 0 maddi ölçüde desteksiz, 1 karışık/belirsiz, 2 sunulan kanıtlarla destekli.
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
