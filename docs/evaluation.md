# Değerlendirme Planı

Bu belge, sistemin doğruluk, güvenilirlik ve maliyet açısından nasıl değerlendirileceğini tanımlar. Henüz ölçüm yapılmamıştır; aşağıdaki metrikler placeholder'dır ve `tests/questions.json` içindeki soru seti genişletildikçe doldurulacaktır.

## Retrieval Metrikleri

| Metrik | Tanım | Sonuç |
|---|---|---|
| Recall@1 | Doğru chunk ilk sırada mı | TBD |
| Recall@3 | Doğru chunk ilk 3 sonuç içinde mi | TBD |
| Recall@5 | Doğru chunk ilk 5 sonuç içinde mi (config.TOP_K varsayılanı) | TBD |

## Yanıt Kalitesi

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
| Latency | Soru-yanıt döngüsü süresi (uçtan uca) | TBD |
| Token usage | İstek başına embedding + LLM token tüketimi | TBD |
| Estimated API cost | Token kullanımına dayalı tahmini OpenAI API maliyeti | TBD |

## Değerlendirme Seti

Değerlendirme, `tests/questions.json` içindeki soru/kaynak çiftleri üzerinden yürütülecektir. Sonuçlar bu belgede güncellenecektir; şu an için sonuç doldurulmamıştır.
