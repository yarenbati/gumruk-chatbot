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
