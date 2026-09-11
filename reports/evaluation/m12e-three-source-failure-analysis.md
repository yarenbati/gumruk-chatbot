# M12E — Three-source retrieval failure analysis

M12E READY FOR REVIEW

Analysis only. No retrieval optimization was performed. No OpenAI/network, retrieval, embedding or Chroma operation was performed. M12D metrics and frozen datasets are unchanged.

## Evidence boundary

Missing required inputs: none; original 4458 persisted chunks artifact remains absent

The original persisted 4458 chunks.json was absent. The deterministically reconstructed 4458 chunk corpus was regenerated in memory from the accepted processed source using the current accepted chunking implementation. All 207 4458 M12D ranked-text hashes match exactly; structural invariants match the accepted 271 Articles / 276 chunks historical result. This supports text diagnostics, not a claim that this is the original historical snapshot.

Supplemental read-only inputs: M10D two-law JSON for regression; source manifest for exact titles; existing 5607 Article JSON for exact character counts (each Article verified equal to newline-joined accepted chunks). Full input hashes are in JSON.

Verified 105 saved questions / 525 ranked slots; 525 available chunk-text rank hashes match. CSV IDs/distances agree with JSON. All 207 reconstructed 4458 ranked texts are verified.

- Top5 is censored: absent means not in saved five, not absent from the whole corpus or known rank 6.
- No saved vectors/global distances or ANN trace; no causal embedding explanation or removal counterfactual is possible.
- 4458 is a deterministically reconstructed 4458 chunk corpus, not the original historical snapshot. All 207 ranked-text hashes match; unranked historical text identity is not independently proven.
- Current code and manifest document the embedding template; original embedding input bytes are not exported for every record.

## Required conclusions

1. **Indexing/provenance:** no evidence of a missing 5607 gold provision or source-identity defect. All expected sources exist in the accepted local corpus; saved M12D checks report 375 records (53/276/46) and gold-key existence. This does not independently prove every vector correct or exclude an ANN issue.
2. **Document discrimination:** all six complete misses have five 4458 slots and no 5607 slot: k5607-002/003/004/014/025/026. This is the dominant observed Top5 failure pattern, not yet a proven semantic root cause.
3. **4458 competitors:** Madde 235 occupies 9 slots across 7 of the 30 questions; 236 and 57 occupy 3 each. Among wrong-document Top1 cases, 57 wins twice; 25, 236, 141, 56 and 235 once each.
4. **003/004:** target fıkra 1 and 9 are both in Madde 3 chunk 001. Both questions closely track the gold text, so missing content or strong paraphrase mismatch is not established. Their five winners are 4458. Fıkra 9 itself explicitly cross-refers to 4458 for the <=10% exception. Semantic dilution in a broad chunk is plausible, unproven.
5. **025/026:** combine 3(1) with 4(1)/(7) or 5(2)/(3), respectively, without naming 5607. Both return 4458 Madde 57 at Top1 and no gold source by Top5. Multi-clause topical competition is a hypothesis; the reconstructed 57 text shares customs-procedure and enforcement language but does not answer organized-crime, public-health or effective-remorse conditions. This is a supported topical interpretation, not a causal estimate.
6. **Madde 3 structure:** 8,425 characters, chunks of 3,742 / 3,692 / 989 characters, covering fıkra 1–11 / 12–19 / 20–23. Its seven gold questions have four complete misses, one partial miss, and two Top1 successes (005/006). This association is confounded by topic and query composition. No Madde 3 chunk occupies any slot in the six complete misses; duplicate Madde 3 slots therefore do not directly cause those misses. Material causal contribution is unproven.
7. **Wrong document versus wrong Article:** seven Top1 wrong documents (six complete misses plus 009), five additional same-document wrong-Article Top1 cases (007/013/015/019/029). At Top5, six of seven ALL failures exclude 5607 entirely; 029 is the sole partial failure, with gold Geçici 10 at rank 4 and Madde 3 absent. No same-document complete miss occurs. Three of its five slots are 4458, while same-document Geçici 11 also competes.
8. **4458 regression:** -3.33 percentage points at every ANY/ALL cutoff, one question (gk001), not evidence of direct 5607 displacement. No 5607 chunks occur in any current 4458 Top5. Madde 210 drops from historical rank 1 despite its old distance being lower than every current slot; cause unresolved from saved evidence.
9. **Next experiments:** prioritize explicit-law normalization/title enrichment (and a separately measured explicit-law filter), source-aware provision/fıkra candidate scoring for broad/composite queries, and a pre-adoption retrieval-candidate completeness diagnostic for gk001. These are development-informed proposals, not production choices. Reconstruction gates now pass; interventions still require new evaluation.

## Document versus query embedding signal

Source: `src/embed.py` build_document_display_title/build_article_label/build_embedding_text; `src/retrieve.py` embed_query/retrieve. Manifest was inspected read-only.

Exact first-line prefixes:

- 5326: `5326 Sayılı Kabahatler Kanunu`
- 4458: `4458 Sayılı Gümrük Kanunu`
- 5607: `5607 Sayılı Kaçakçılıkla Mücadele Kanunu`

The next line is Madde N / Ek Madde N / Geçici Madde N; an Article title follows only when present, then a blank line and unchanged chunk text. For example, 5607 Madde 16/A includes `Kaçak akaryakıtın tasfiyesi`. Document IDs themselves are not an extra embedding prefix. Exact representative complete headers are stored in JSON.

Queries are embedded exactly as raw natural language: `embed_texts([query], ..., batch_size=1)`. A query saying ‘5607 sayılı Kanunda’ receives no law-aware normalization or title enrichment. The number reaches the query embedding only when already in the question. Document title enrichment exists only on the document side. The saved configuration is text-embedding-3-small, 1536 dimensions, L2, K=5, no filter/rerank/expansion or deduplication. No claim about numerical prefix strength can be established without an intervention.

## Rank and distance inventory: all 30 questions

Each JSON question records all five full chunk/document/source IDs and raw distances. Margin means best gold-source distance minus Top1 distance; a separate document margin is stored. Null means censored beyond saved Top5, not zero or a measured rank 6. Conditional Top5-distance gaps in JSON are not global ANN lower bounds.

| ID | Best ranks 5607/4458/5326 | Top1 L2 | Gold-source margin | Expected document absent @5 |
|---|---|---:|---:|---|
| k5607-001 | 1 / 2 / 3 | 0.659146 | 0.000000 | False |
| k5607-002 | None / 1 / None | 0.685378 | unavailable | True |
| k5607-003 | None / 1 / None | 0.646965 | unavailable | True |
| k5607-004 | None / 1 / None | 0.697769 | unavailable | True |
| k5607-005 | 1 / 5 / None | 0.613266 | 0.000000 | False |
| k5607-006 | 1 / None / None | 0.630068 | 0.000000 | False |
| k5607-007 | 1 / None / None | 0.664030 | 0.064863 | False |
| k5607-008 | 1 / 4 / 2 | 0.937303 | 0.000000 | False |
| k5607-009 | 3 / 1 / None | 0.781235 | 0.036444 | False |
| k5607-010 | 1 / 2 / None | 0.603463 | 0.000000 | False |
| k5607-011 | 1 / None / None | 0.586866 | 0.000000 | False |
| k5607-012 | 1 / None / None | 0.615859 | 0.000000 | False |
| k5607-013 | 1 / 3 / None | 0.761696 | 0.029788 | False |
| k5607-014 | None / 1 / None | 0.836312 | unavailable | True |
| k5607-015 | 1 / None / None | 0.633434 | 0.005666 | False |
| k5607-016 | 1 / None / None | 0.710858 | 0.000000 | False |
| k5607-017 | 1 / None / None | 0.811822 | 0.000000 | False |
| k5607-018 | 1 / None / 4 | 0.774641 | 0.000000 | False |
| k5607-019 | 1 / None / None | 0.656564 | 0.052774 | False |
| k5607-020 | 1 / None / None | 0.617933 | 0.000000 | False |
| k5607-021 | 1 / 2 / None | 0.595718 | 0.000000 | False |
| k5607-022 | 1 / 3 / 2 | 0.717782 | 0.000000 | False |
| k5607-023 | 1 / None / None | 0.773054 | 0.000000 | False |
| k5607-024 | 1 / None / None | 0.469182 | 0.000000 | False |
| k5607-025 | None / 1 / None | 0.714294 | unavailable | True |
| k5607-026 | None / 1 / None | 0.666417 | unavailable | True |
| k5607-027 | 1 / None / None | 0.647137 | 0.000000 | False |
| k5607-028 | 1 / 2 / None | 0.690133 | 0.000000 | False |
| k5607-029 | 1 / 2 / None | 0.658862 | 0.045556 | False |
| k5607-030 | 1 / None / 3 | 0.763590 | 0.000000 | False |

009: correct document/source rank 3, distance margin 0.036444128. 029: correct document at rank 1 but wrong Article; first gold source rank 4, margin 0.045555711. Controls 017/023/028/030 have a gold source at Top1 (margin zero); 030 obtains all gold sources by Top3. Successful 017 has Top1 distance 0.811821938, greater than the wrong Top1 distance of several failures: raw L2 is not a universal correctness threshold.

## Primary cases and controls: exact gold snippets and ranked competitors

### k5607-002

5607 sayılı Kanunda “gümrüklenmiş değer” nasıl tanımlanır ve ithal ve ihraç eşyası bakımından hangi değerlerin toplamı esas alınır?

Explicit 5607/query-input number: True. Expected: 5607_kacakcilikla_mucadele_kanunu/normal/2.

- `5607-madde-2-chunk-001`, fıkra 1: …ler ile diğer malî yükümlülükleri, b) Gümrüklenmiş değer: Uluslararası kıymet sözleşmesine göre belirlenecek; ithal eşyası için eşyanın CIF kıymeti ile gümrük vergileri toplamını, ihraç eşyası için FOB kıymeti ile gümrük vergileri toplamını, c) (Ek: 28/3/2013-6455/53 md.) Akaryakıt: Benzin, gaz yağı, jet yakıtı, motorin, fuel-oil, sıvılaştırılmış petrol gazları, doğal gaz gibi akaryakıt ürünleri ile akaryakıt yerine kullanılan petrol türevleri ve…

Exact normalized query/gold token overlap (no stemming, not discriminative against 4458): değer, eşyası, gümrüklenmiş, ihraç, ithal, kanunda

Exact saved competitors (text comparison follows):

- Rank 1: `4458-madde-25-chunk-001` / `4458_gumruk_kanunu/normal/25`, L2=0.685377717.
- Rank 2: `4458-madde-235-chunk-001` / `4458_gumruk_kanunu/normal/235`, L2=0.692853570.
- Rank 3: `4458-madde-126-chunk-001` / `4458_gumruk_kanunu/normal/126`, L2=0.695894063.
- Rank 4: `4458-madde-143-chunk-001` / `4458_gumruk_kanunu/normal/143`, L2=0.702990055.
- Rank 5: `4458-madde-26-chunk-001` / `4458_gumruk_kanunu/normal/26`, L2=0.703138947.

Top-ranked wrong 4458 excerpt (rank 1): d) İthal eşyasının üretiminde kullanılan malzeme ve imalat veya diğer imal işlemlerinin bedel veya kıymetleri ile Türkiye'ye ihraç edilmek üzere ihraç ülkesindeki üreticiler tarafından üretilen, kıymeti belirlenecek eşya ile aynı sınıf veya cins eşyanın satışında mutat olan kar ve genel giderlere eşit bir tutar ve 27 nci maddenin 1 inci fıkrasının (e) bendinde sayılan diğer bedel veya kıymetler toplamından oluşan hesaplanmış kıymet.

Shared query/target/competitor tokens: ihraç, ithal
Target query terms absent from competitor: değer, eşyası, gümrüklenmiş
Query terms present in wrong competitor: ihraç, ithal
Exact normalized tokens; correct terms use displayed target excerpts, wrong terms use the ranked chunk. Unique means absent from this competitor, not legally unique. Inflections are not stemmed.

SUPPORTED INTERPRETATION; token sets and excerpts OBSERVED; embedding causality UNPROVEN HYPOTHESIS: Valuation language connects 4458/25 (alternative customs valuation, sale price, calculated value) to the requested definition. The 5607 definition and import/export components remain the correct target; the explicit law number did not enforce scope.


### k5607-003

Eşyanın gümrük işlemlerine tabi tutulmadan ülkeye sokulması hangi hapis ve adlî para cezasını gerektirir; eşya gümrük kapıları dışından sokulursa ceza nasıl değişir?

Explicit 5607/query-input number: False. Expected: 5607_kacakcilikla_mucadele_kanunu/normal/3.

- `5607-madde-3-chunk-001`, fıkra 1: …eğişik: 28/3/2013-6455/54 md.) (1) Eşyayı, gümrük işlemlerine tabi tutmaksızın ülkeye sokan kişi, bir yıldan beş yıla kadar hapis ve on bin güne kadar adlî para cezası ile cezalandırılır. Eşyanın, gümrük kapıları dışından ülkeye sokulması halinde, verilecek ceza üçte birinden yarısına kadar artırılır. (2) Eşyayı, aldatıcı işlem ve davranışlarla gümrük vergileri kısmen veya tamamen ödenmeksizin ülkeye sokan kişi, iki yıldan beş yıla kadar hapis ve…

Exact normalized query/gold token overlap (no stemming, not discriminative against 4458): adlî, ceza, dışından, eşya, eşyanın, gümrük, hapis, işlemlerine, kapıları, para, sokulması, tabi, ülkeye

Exact saved competitors (text comparison follows):

- Rank 1: `4458-madde-236-chunk-001` / `4458_gumruk_kanunu/normal/236`, L2=0.646964848.
- Rank 2: `4458-madde-235-chunk-001` / `4458_gumruk_kanunu/normal/235`, L2=0.653518319.
- Rank 3: `4458-madde-239-chunk-001` / `4458_gumruk_kanunu/normal/239`, L2=0.678685904.
- Rank 4: `4458-madde-57-chunk-001` / `4458_gumruk_kanunu/normal/57`, L2=0.695006430.
- Rank 5: `4458-madde-186-chunk-001` / `4458_gumruk_kanunu/normal/186`, L2=0.706568301.

Top-ranked wrong 4458 excerpt (rank 1): Madde 236 – 1. (Değişik: 28/3/2013-6455/13 md.) Teminat alınmış olsa bile, gümrük işlemlerine başlanmadan veya bu işlemler bitirilip gümrük idaresinin izni alınmadan gümrük antrepoları veya gümrük idaresince eşya konulmasına izin verilen yerlerden kısmen veya tamamen eşya çıkarılması veya buralardaki eşyanın değiştirilmesi ya da yapılan sayımlarda kayıtlara göre eşyanın bir kısmının noksan olduğunun anlaşılması hallerinde, bu eşyanın gümrük vergilerinin yanı sıra gümrüklenmiş değerinin iki katı idari para cezası verilir.

Shared query/target/competitor tokens: eşyanın, gümrük, işlemlerine, para, tabi
Target query terms absent from competitor: adlî, ceza, dışından, hapis, kapıları, sokulması, ülkeye
Query terms present in wrong competitor: eşya, eşyanın, gümrük, işlemlerine, para, tabi
Exact normalized tokens; correct terms use displayed target excerpts, wrong terms use the ranked chunk. Unique means absent from this competitor, not legally unique. Inflections are not stemmed.

SUPPORTED INTERPRETATION; token sets and excerpts OBSERVED; embedding causality UNPROVEN HYPOTHESIS: 4458/236 concerns goods removed from warehouses before customs procedures finish and administrative fines. This is a concrete procedural/penalty parallel, but 5607 specifies entry into the country, customs gates, imprisonment and judicial fines. Close correct wording still loses; lexical mismatch is not established.


### k5607-004

İhracat gerçekleşmediği hâlde gerçekleşmiş gibi gösterilmesi veya ihraç malının cins, miktar, evsaf ya da fiyatının değiştirilmesi hangi yaptırımla karşılanır; beyandaki fark yüzde onu aşmıyorsa hangi işlem uygulanır?

Explicit 5607/query-input number: False. Expected: 5607_kacakcilikla_mucadele_kanunu/normal/3.

- `5607-madde-3-chunk-001`, fıkra 9: … cezası ile cezalandırılır. (9) İlgili kanun hükümlerine göre teşvik, sübvansiyon veya parasal iadelerden yararlanmak amacıyla ihracat gerçekleşmediği hâlde gerçekleşmiş gibi gösteren ya da gerçekleştirilen ihracata konu malın cins, miktar, evsaf veya fiyatını değişik gösteren kişi, bir yıldan beş yıla kadar hapis ve on bin güne kadar adlî para cezası ile cezalandırılır. Beyanname ve eki belgelerde gösterilen ile gerçekte ihraç edilen eşya arasın…

Exact normalized query/gold token overlap (no stemming, not discriminative against 4458): cins, evsaf, fark, gerçekleşmediği, gerçekleşmiş, gibi, hâlde, ihracat, ihraç, işlem, miktar, onu, uygulanır, yüzde

Exact saved competitors (text comparison follows):

- Rank 1: `4458-madde-141-chunk-001` / `4458_gumruk_kanunu/normal/141`, L2=0.697768688.
- Rank 2: `4458-madde-179-chunk-001` / `4458_gumruk_kanunu/normal/179`, L2=0.706388533.
- Rank 3: `4458-madde-27-chunk-001` / `4458_gumruk_kanunu/normal/27`, L2=0.715495884.
- Rank 4: `4458-madde-25-chunk-001` / `4458_gumruk_kanunu/normal/25`, L2=0.718184412.
- Rank 5: `4458-madde-24-chunk-001` / `4458_gumruk_kanunu/normal/24`, L2=0.719123363.

Top-ranked wrong 4458 excerpt (rank 1): 2. 1 inci fıkra uyarınca indirilecek tutarın hesaplanmasında geçici ihracat eşyasının, hariçte işleme rejimine ilişkin beyannamenin tescili tarihindeki miktar ve niteliği ile işlem görmüş ürünlerin yeniden serbest dolaşıma girişine ilişkin beyannamenin tescili tarihinde uygulanabilir diğer vergilendirme unsurları dikkate alınır.

Shared query/target/competitor tokens: ihracat, miktar
Target query terms absent from competitor: cins, evsaf, gerçekleşmediği, gerçekleşmiş, gibi, hâlde, ihraç
Query terms present in wrong competitor: fark, ihracat, işlem, miktar, uygulanır
Exact normalized tokens; correct terms use displayed target excerpts, wrong terms use the ranked chunk. Unique means absent from this competitor, not legally unique. Inflections are not stemmed.

SUPPORTED INTERPRETATION; token sets and excerpts OBSERVED; embedding causality UNPROVEN HYPOTHESIS: 4458/141 shares export, quantity, declaration and value/difference vocabulary, but calculates outward-processing import taxes. It does not supply the requested fictitious-export offence. 5607/3(9) closely answers the query and itself refers to 4458 for the ten-percent exception; these connections plausibly support topical competition but do not explain the ranking causally.


### k5607-005

Ulusal marker seviyenin altında olan veya hiç marker içermeyen akaryakıt bakımından hangi ticari fiiller suç kapsamındadır ve hangi yaptırım öngörülür?

Explicit 5607/query-input number: False. Expected: 5607_kacakcilikla_mucadele_kanunu/normal/3.

- `5607-madde-3-chunk-001`, fıkra 11: …eğişik: 18/6/2014-6545/89 md.) Ulusal marker uygulamasına tabi olup da, Enerji Piyasası Düzenleme Kurumunun belirlediği seviyenin altında ulusal marker içeren veya hiç içermeyen akaryakıtı; a) Ticari amaçla üreten, bulunduran veya nakleden, b) Satışa arz eden veya satan, c) Bu özelliğini bilerek ve ticari amaçla satın alan, kişi iki yıldan beş yıla kadar hapis ve yirmi bin güne kadar adli para cezası ile cezalandırılır. Ancak, marker içermeyen ve…

Exact normalized query/gold token overlap (no stemming, not discriminative against 4458): akaryakıt, altında, fiiller, hiç, içermeyen, marker, seviyenin, suç, ticari, ulusal

Exact saved competitors (text comparison follows):

- Rank 5: `4458-madde-176-chunk-001` / `4458_gumruk_kanunu/normal/176`, L2=0.989250422.

Top-ranked wrong 4458 excerpt (rank 5): Madde 176 – 1. Gemilerin, botların, diğer deniz taşıtlarının ve hava gemilerinin dış seferlerde kullanacakları yakıt ve yağları ile karaya çıkarılmamak şartıyla yurtdışından getirdikleri kumanyaları ithalat vergilerinden muaftır.

Shared query/target/competitor tokens:
Target query terms absent from competitor: altında, hiç, içermeyen, marker, seviyenin, ticari, ulusal
Query terms present in wrong competitor:
Exact normalized tokens; correct terms use displayed target excerpts, wrong terms use the ranked chunk. Unique means absent from this competitor, not legally unique. Inflections are not stemmed.

SUPPORTED INTERPRETATION; token sets and excerpts OBSERVED; embedding causality UNPROVEN HYPOTHESIS: Descriptive token comparison; no causal attribution.


### k5607-006

Kaçakçılık suçunun teşebbüs aşamasında kalması hâlinde 5607 sayılı Kanun bakımından nasıl cezalandırma yapılır?

Explicit 5607/query-input number: True. Expected: 5607_kacakcilikla_mucadele_kanunu/normal/3.

- `5607-madde-3-chunk-003`, fıkra 22: …aki fıkralarda tanımlanan fiiller, teşebbüs aşamasında kalmış olsa bile, tamamlanmış gibi cezalandırılır. (23) (Ek: 18/6/2014-6545/89 md.)Yukarıdaki fıkralarda tanımlanan suçların konusunu oluşturan eşyanın değerinin fahiş olması hâlinde, verilecek cezalar yarısından bir katına kadar artırılır. (Ek cümle:14/4/2020-7242/61 md.) Eşyanın değerinin hafif olması hâlinde verilecek cezalar yarısına kadar, pek hafif olması hâlinde ise üçte birine kadar i…

Exact normalized query/gold token overlap (no stemming, not discriminative against 4458): aşamasında, kaçakçılık, suçunun, teşebbüs, yapılır

Exact saved competitors (text comparison follows):

- No 4458 competitor in the saved five.

### k5607-009

Yolcunun üzerinde, eşyası arasında veya taşıma aracında beyanına aykırı olarak çıkan eşya hangi iki durumda 3 üncü madde hükümlerine tabi olur?

Explicit 5607/query-input number: False. Expected: 5607_kacakcilikla_mucadele_kanunu/normal/6.

- `5607-madde-6-chunk-001`, fıkra 4: …(Mülga: 28/3/2013-6455/66 md.) (4) Yolcuların, beyanlarına aykırı olarak üzerlerinde, eşyası arasında veya taşıma araçlarında çıkan eşyanın ticarî mahiyette veya ithali veya ihracının yasak olması halinde 3 üncü madde hükümleri uygulanır.…

Exact normalized query/gold token overlap (no stemming, not discriminative against 4458): arasında, aykırı, eşyası, taşıma, çıkan, üncü

Exact saved competitors (text comparison follows):

- Rank 1: `4458-madde-235-chunk-001` / `4458_gumruk_kanunu/normal/235`, L2=0.781234503.
- Rank 2: `4458-madde-167-chunk-002` / `4458_gumruk_kanunu/normal/167`, L2=0.807505012.
- Rank 4: `4458-madde-235-chunk-002` / `4458_gumruk_kanunu/normal/235`, L2=0.828294158.
- Rank 5: `4458-madde-236-chunk-001` / `4458_gumruk_kanunu/normal/236`, L2=0.831212819.

Top-ranked wrong 4458 excerpt (rank 1): 3. Yolcuların, gümrük mevzuatına göre kişisel ve hediyelik eşya kapsamı dışında olup beyanlarına aykırı olarak üzerlerinde, eşyası arasında veya taşıma araçlarında çıkan ya da başkasına ait olduğu halde kendi eşyasıymış gibi gösterdikleri eşyanın gümrük vergileri iki kat olarak alınır ve eşya sahibine teslim edilir. Gümrük vergileri ödenmediği takdirde, eşya gümrüğe terk edilmiş sayılır.

Shared query/target/competitor tokens: arasında, aykırı, eşyası, taşıma, çıkan
Target query terms absent from competitor: üncü
Query terms present in wrong competitor: arasında, aykırı, eşya, eşyası, iki, tabi, taşıma, çıkan
Exact normalized tokens; correct terms use displayed target excerpts, wrong terms use the ranked chunk. Unique means absent from this competitor, not legally unique. Inflections are not stemmed.

SUPPORTED INTERPRETATION; token sets and excerpts OBSERVED; embedding causality UNPROVEN HYPOTHESIS: 4458/235(3) closely parallels the passenger, belongings/vehicle and contrary-declaration situation, then imposes doubled customs taxes. 5607/6(4) instead supplies the two conditions for applying Article 3. This is unusually concrete overlap across distinct legal consequences.


### k5607-014

Yabancı ülkeden gelen yasak eşya yükleme veya taşıma belgelerinde gösterilerek gümrüğe getirilmişse hangi güvenlik koşulları altında nereye gönderilebilir?

Explicit 5607/query-input number: False. Expected: 5607_kacakcilikla_mucadele_kanunu/normal/12.

- `5607-madde-12-chunk-001`, fıkra 1: MADDE 12 – (1) Yabancı ülkelerden gelen yasak eşya, yükleme veya taşıma belgelerinde belirtilerek gümrüğe getirilirse, teminat altında ve gerekli güvenlik tedbirleri alınarak geldiği yere veya diğer bir ülkeye iade ve sevk olunur. (2) Kaçakçılık fiilinin konusunu, toplum ve çevre sağlığı yönünden tehlikeli ve zararlı eşya ile atık maddelerin oluşturması halinde, ilgililer hakkında soruşturma işlemleri başlatılmakla birlikte, bunlar gümrük yetkili…

Exact normalized query/gold token overlap (no stemming, not discriminative against 4458): altında, belgelerinde, eşya, gelen, gümrüğe, güvenlik, taşıma, yabancı, yasak, yükleme

Exact saved competitors (text comparison follows):

- Rank 1: `4458-madde-56-chunk-001` / `4458_gumruk_kanunu/normal/56`, L2=0.836311936.
- Rank 2: `4458-madde-235-chunk-001` / `4458_gumruk_kanunu/normal/235`, L2=0.851217151.
- Rank 3: `4458-madde-175-chunk-001` / `4458_gumruk_kanunu/normal/175`, L2=0.857413232.
- Rank 4: `4458-madde-10-a-chunk-001` / `4458_gumruk_kanunu/normal/10/a`, L2=0.877689540.
- Rank 5: `4458-madde-48-chunk-001` / `4458_gumruk_kanunu/normal/48`, L2=0.892672896.

Top-ranked wrong 4458 excerpt (rank 1): 2. Türk menşeli eşyada kullanılmak üzere ve bunların başka ülke menşeli olduğunu gösterecek veya böyle bir izlenim uyandıracak nitelikte, üzerleri yabancı dille yazılı veya basılı her türlü boş zarf, şerit, etiket, damga ve benzeri eşya ile Türkiye'de düzenlenebilecek belgeleri başka ülkelerde düzenlenmiş gibi gösterebilecek nitelikte, üzerleri imzalı veya imzasız olsun, Türkiye'de yerleşik olmayan yabancı firmalara ait proforma faturalar hariç boş faturaların Türkiye'ye ithaline izin verilmez.

Shared query/target/competitor tokens: eşya, yabancı
Target query terms absent from competitor: altında, belgelerinde, gelen, gümrüğe, güvenlik, taşıma, yasak, yükleme
Query terms present in wrong competitor: eşya, yabancı, ülkeden
Exact normalized tokens; correct terms use displayed target excerpts, wrong terms use the ranked chunk. Unique means absent from this competitor, not legally unique. Inflections are not stemmed.

SUPPORTED INTERPRETATION; token sets and excerpts OBSERVED; embedding causality UNPROVEN HYPOTHESIS: 4458/56 concerns goods barred from import and permission for transit, warehousing or re-export, whereas 5607/12 addresses prohibited goods shown in loading/transport documents and secure return/transit. Shared prohibited-goods handling plausibly connects them; the 5607 source is short and directly worded.


### k5607-017

Elkonulan ve teknik düzenlemelere uygun kaçak akaryakıtın hangi kurumlar tarafından, hangi yöntemlerle tasfiye edilmesi öngörülür?

Explicit 5607/query-input number: False. Expected: 5607_kacakcilikla_mucadele_kanunu/normal/16/a.

- `5607-madde-16-a-chunk-001`, fıkra 1: …ınca el konulan kaçak akaryakıttan teknik düzenlemelere uygun olanlar, il özel idareleri, il özel idaresi bulunmayan yerde yatırım izleme ve koordinasyon başkanlıkları tarafından, numune alınmak suretiyle kamu kurum ve kuruluşları ile mahalli idarelerin kullanımına bedelsiz tahsis edilerek veya satışı yapılarak tasfiye edilir ve teslim tutanağı ile numune en yakın gümrük idaresine teslim edilir. Kara, hava ve deniz hudut kapılarında el konulan ka…

Exact normalized query/gold token overlap (no stemming, not discriminative against 4458): akaryakıtın, düzenlemelere, kaçak, tarafından, tasfiye, teknik, uygun

Exact saved competitors (text comparison follows):

- No 4458 competitor in the saved five.

### k5607-023

Kaçak şüphesiyle eşya yakalanması hâlinde muhbir ve elkoyma ikramiyesine hak kazananlara ödeme yapılmasının temel dayanağı nedir?

Explicit 5607/query-input number: False. Expected: 5607_kacakcilikla_mucadele_kanunu/normal/23.

- `5607-madde-23-chunk-001`, fıkra 1: …zannı ile eşya yakalanması halinde muhbir ve elkoyma ikramiyesine hak kazananlara aşağıdaki esas ve usullere göre ikramiye ödenir. a) 10/7/1953 tarihli ve 6136 sayılı Ateşli Silâhlar ve Bıçaklar ile Diğer Aletler Hakkında Kanunun 12 nci maddesine aykırılık suçlarından yakalanan silâh ve mermiler ile Türk Ceza Kanununun 174 üncü maddesine muhalefet suçlarından yakalanan maddelerin olay tarihine göre Milli Savunma Bakanlığınca her yıl belirlenen de…

Exact normalized query/gold token overlap (no stemming, not discriminative against 4458): elkoyma, eşya, hak, ikramiyesine, kazananlara, kaçak, muhbir, yakalanması

Exact saved competitors (text comparison follows):

- No 4458 competitor in the saved five.

### k5607-025

Eşyayı gümrük işlemlerine tabi tutmaksızın ülkeye sokan kişi için Madde 3 fıkra 1'deki temel yaptırım nedir; aynı suç örgüt faaliyeti çerçevesinde işlenirse ve eşya toplum sağlığını tehdit edecek nitelikteyse Madde 4 fıkra 1 ve 7 hangi ek sonuçları, hangi koşulla öngörür?

Explicit 5607/query-input number: False. Expected: 5607_kacakcilikla_mucadele_kanunu/normal/3, 5607_kacakcilikla_mucadele_kanunu/normal/4.

- `5607-madde-3-chunk-001`, fıkra 1: …eğişik: 28/3/2013-6455/54 md.) (1) Eşyayı, gümrük işlemlerine tabi tutmaksızın ülkeye sokan kişi, bir yıldan beş yıla kadar hapis ve on bin güne kadar adlî para cezası ile cezalandırılır. Eşyanın, gümrük kapıları dışından ülkeye sokulması halinde, verilecek ceza üçte birinden yarısına kadar artırılır. (2) Eşyayı, aldatıcı işlem ve davranışlarla gümrük vergileri kısmen veya tamamen ödenmeksizin ülkeye sokan kişi, iki yıldan beş yıla kadar hapis ve…
- `5607-madde-4-chunk-001`, fıkra 1: … Kanunda tanımlanan suçların (…)9, bir örgütün faaliyeti çerçevesinde işlenmesi halinde, verilecek ceza iki kat artırılır. (2) Bu Kanunda tanımlanan suçların (…)9, üç veya daha fazla kişi tarafından birlikte işlenmesi halinde, verilecek ceza yarı oranında artırılır. (3) Bu Kanunda tanımlanan suçların, tüzel kişinin faaliyeti çerçevesinde veya yararına olarak işlenmesi halinde, ayrıca bunlara özgü güvenlik tedbirlerine hükmolunur. (4) Bu Kanunda t…
- `5607-madde-4-chunk-001`, fıkra 7: …venliğini bozacak ya da çevre veya toplum sağlığını tehdit edecek nitelikte olması halinde, fiil daha ağır cezayı gerektiren bir suç oluşturmadığı takdirde, verilecek hapis cezası on yıldan az olamaz. (8) (Ek: 28/3/2013-6455/55 md.)Kaçak akaryakıt satışının, 3 üncü maddenin on dördüncü fıkrasında belirtildiği şekilde sabit ya da seyyar tank, düzenek veya ekipman kullanılarak gerçekleştirilmesi halinde verilecek cezalar iki kat artırılır. (9) (Ek:…

Exact normalized query/gold token overlap (no stemming, not discriminative against 4458): aynı, edecek, ek, eşya, eşyayı, faaliyeti, gümrük, işlemlerine, kişi, sağlığını, sokan, suç, tabi, tehdit, toplum, tutmaksızın, çerçevesinde, ülkeye

Exact saved competitors (text comparison follows):

- Rank 1: `4458-madde-57-chunk-001` / `4458_gumruk_kanunu/normal/57`, L2=0.714294136.
- Rank 2: `4458-madde-167-chunk-002` / `4458_gumruk_kanunu/normal/167`, L2=0.744162977.
- Rank 3: `4458-madde-235-chunk-002` / `4458_gumruk_kanunu/normal/235`, L2=0.747076213.
- Rank 4: `4458-madde-235-chunk-001` / `4458_gumruk_kanunu/normal/235`, L2=0.760764480.
- Rank 5: `4458-madde-236-chunk-001` / `4458_gumruk_kanunu/normal/236`, L2=0.774057984.

Top-ranked wrong 4458 excerpt (rank 1): 5. Yolcuların kendi kullanımlarına mahsus kişisel eşya ile ticari mahiyette olmayan ve gümrük vergisi muafiyeti sınırları içinde kalan hediyelik eşya için bu madde hükümleri uygulanmaz. Aynı şekilde, fikri ve sınaî haklar mevzuatına göre korunması gereken haklar ile korunmuş ve hak sahibinin izni ile üretilmiş eşyanın; hak sahibinin rızası dışında bir gümrük işlemine tabi tutulması veya hak sahibinin onayladığından farklı şartlarda üretilmesi veya başka şartlarda bir marka taşıması halinde, söz konusu eşya bu madde hükümleri kapsamı dışında tutulur.

Shared query/target/competitor tokens: ek, gümrük, tabi
Target query terms absent from competitor: edecek, eşyayı, faaliyeti, işlemlerine, kişi, sağlığını, sokan, suç, tehdit, toplum, tutmaksızın, çerçevesinde, ülkeye
Query terms present in wrong competitor: aynı, ek, eşya, gümrük, tabi
Exact normalized tokens; correct terms use displayed target excerpts, wrong terms use the ranked chunk. Unique means absent from this competitor, not legally unique. Inflections are not stemmed.

SUPPORTED INTERPRETATION; token sets and excerpts OBSERVED; embedding causality UNPROVEN HYPOTHESIS: 4458/57 repeatedly describes customs procedures being stopped, goods detained, court decisions and disposal, offering general procedure/enforcement overlap. It concerns intellectual-property rights, not organized crime or public-health aggravation. The composite gold request is wholly absent from Top5; query composition and broad Article 3 dilution remain unproven causal hypotheses.


### k5607-026

Eşyayı gümrük işlemlerine tabi tutmaksızın ülkeye sokmanın Madde 3 fıkra 1'deki temel yaptırımı nedir; Madde 5 kapsamında etkin pişmanlıkla ödeme yapılırsa ödeme tutarı, soruşturma ve kovuşturma evrelerindeki indirimler ve bu imkândan yararlanamayan hâller nelerdir?

Explicit 5607/query-input number: False. Expected: 5607_kacakcilikla_mucadele_kanunu/normal/3, 5607_kacakcilikla_mucadele_kanunu/normal/5.

- `5607-madde-3-chunk-001`, fıkra 1: …eğişik: 28/3/2013-6455/54 md.) (1) Eşyayı, gümrük işlemlerine tabi tutmaksızın ülkeye sokan kişi, bir yıldan beş yıla kadar hapis ve on bin güne kadar adlî para cezası ile cezalandırılır. Eşyanın, gümrük kapıları dışından ülkeye sokulması halinde, verilecek ceza üçte birinden yarısına kadar artırılır. (2) Eşyayı, aldatıcı işlem ve davranışlarla gümrük vergileri kısmen veya tamamen ödenmeksizin ülkeye sokan kişi, iki yıldan beş yıla kadar hapis ve…
- `5607-madde-5-chunk-001`, fıkra 2: …uçlardan birini işlemiş olan kişi, etkin pişmanlık göstererek suç konusu eşyanın gümrüklenmiş değerinin iki katı kadar parayı Devlet Hazinesine; a) Soruşturma evresi sona erinceye kadar ödediği takdirde, hakkında bu Kanunda tanımlanan kaçakçılık suçlarından dolayı verilecek ceza yarı oranında, b) Kovuşturma evresinde hüküm verilinceye kadar ödediği takdirde, hakkında bu Kanunda tanımlanan kaçakçılık suçlarından dolayı verilecek ceza üçte bir oran…
- `5607-madde-5-chunk-001`, fıkra 3: …-7242/62 md.) İkinci fıkra hükmü, mükerrirler hakkında veya suçun bir örgütün faaliyeti çerçevesinde işlenmesi hâlinde uygulanmaz.…

Exact normalized query/gold token overlap (no stemming, not discriminative against 4458): etkin, eşyayı, gümrük, işlemlerine, kovuşturma, soruşturma, tabi, tutmaksızın, ülkeye

Exact saved competitors (text comparison follows):

- Rank 1: `4458-madde-57-chunk-001` / `4458_gumruk_kanunu/normal/57`, L2=0.666417122.
- Rank 2: `4458-madde-24-chunk-001` / `4458_gumruk_kanunu/normal/24`, L2=0.682329059.
- Rank 3: `4458-madde-187-chunk-001` / `4458_gumruk_kanunu/normal/187`, L2=0.683646917.
- Rank 4: `4458-madde-235-chunk-002` / `4458_gumruk_kanunu/normal/235`, L2=0.692768633.
- Rank 5: `4458-madde-234-chunk-001` / `4458_gumruk_kanunu/normal/234`, L2=0.696253419.

Top-ranked wrong 4458 excerpt (rank 1): 2. Fikri ve sınaî hakların ihlal edildiği gerekçesi ile gümrük idaresine yapılan başvurunun kabulü, söz konusu eşyanın gümrük idaresince gereğince muayene edilmeden bırakıldığı veya eşyanın alıkonulması için herhangi bir önlem alınmadığı gerekçesi ile hak sahibine tazminat hakkı doğurmaz. Fikri ve sınaî hakları ihlal eden eşya ile mücadele kapsamında, gümrük idaresince başvuru üzerine veya re’sen hareket edilmesi nedeniyle ilgili kişilerin zarara uğramasından gümrük idaresi ve yetkilileri sorumlu tutulamazlar.

Shared query/target/competitor tokens: gümrük, tabi
Target query terms absent from competitor: etkin, eşyayı, işlemlerine, kovuşturma, soruşturma, tutmaksızın, ülkeye
Query terms present in wrong competitor: gümrük, kapsamında, tabi
Exact normalized tokens; correct terms use displayed target excerpts, wrong terms use the ranked chunk. Unique means absent from this competitor, not legally unique. Inflections are not stemmed.

SUPPORTED INTERPRETATION; token sets and excerpts OBSERVED; embedding causality UNPROVEN HYPOTHESIS: 4458/57 supplies customs-procedure, goods, application and court vocabulary, but concerns intellectual-property detention, not effective remorse, payment reductions or investigation/prosecution stages. Shared procedural wording is plausible but weaker than a matching offence; why it wins remains unproven. No correct source is in Top5.


### k5607-028

16/A ve 23 üncü maddelerde belirtilen yönetmeliklerin yürürlüğe konulması için Geçici Madde 7 hangi süreyi öngörür?

Explicit 5607/query-input number: False. Expected: 5607_kacakcilikla_mucadele_kanunu/gecici/7.

- `5607-gecici-madde-7-chunk-001`, fıkra 1: … (Ek: 28/3/2013-6455/63 md.) (1) 16/A maddesinin altıncı fıkrası ile 23 üncü maddenin beşinci ve altıncı fıkralarında belirtilen yönetmelikler altı ay içinde yürürlüğe konulur.…

Exact normalized query/gold token overlap (no stemming, not discriminative against 4458): a, belirtilen, geçici, yürürlüğe, üncü

Exact saved competitors (text comparison follows):

- Rank 2: `4458-gecici-madde-7-chunk-001` / `4458_gumruk_kanunu/gecici/7`, L2=0.890407264.

Top-ranked wrong 4458 excerpt (rank 2): Geçici Madde 7 – (Ek: 12/11/2008-5810/9 md.)

Shared query/target/competitor tokens: a, yürürlüğe
Target query terms absent from competitor: belirtilen, üncü
Query terms present in wrong competitor: a, geçici, yürürlüğe
Exact normalized tokens; correct terms use displayed target excerpts, wrong terms use the ranked chunk. Unique means absent from this competitor, not legally unique. Inflections are not stemmed.

SUPPORTED INTERPRETATION; token sets and excerpts OBSERVED; embedding causality UNPROVEN HYPOTHESIS: Descriptive token comparison; no causal attribution.


### k5607-029

Madde 3 fıkra 2 hangi fiili ve yaptırımı düzenler; gümrük vergilerinin kısmen eksik ödenmesi nedeniyle açılmış kamu davalarında, Geçici Madde 10'un yürürlüğünden önce elkonulan ve müsadere kararı verilmemiş kara taşıtlarının iadesi için bu geçici hüküm hangi başvuru, ödeme ve tasfiye koşullarını arar?

Explicit 5607/query-input number: False. Expected: 5607_kacakcilikla_mucadele_kanunu/gecici/10, 5607_kacakcilikla_mucadele_kanunu/normal/3.

- `5607-madde-3-chunk-001`, fıkra 2: …ısına kadar artırılır. (2) Eşyayı, aldatıcı işlem ve davranışlarla gümrük vergileri kısmen veya tamamen ödenmeksizin ülkeye sokan kişi, iki yıldan beş yıla kadar hapis ve on bin güne kadar adlî para cezası ile cezalandırılır. (3) Transit rejimi çerçevesinde taşınan serbest dolaşımda bulunmayan eşyayı, rejim hükümlerine aykırı olarak gümrük bölgesinde bırakan kişi, bir yıldan üç yıla kadar hapis ve beş bin güne kadar adlî para cezası ile cezalandı…
- `5607-gecici-madde-10-chunk-001`, fıkra 1: …ddesinin ikinci fıkrası uyarınca gümrük vergilerinin kısmen eksik ödenmesi nedeniyle açılan kamu davalarında, bu maddenin yürürlüğe girdiği tarihten önce el konulan ve müsadere kararı verilmemiş kara taşıtları ile ilgili olarak; a) Taşıtın tasfiyesinin tamamlanmamış olması, b) Bu maddenin yürürlüğe girdiği ayı takip eden altıncı ayın sonuna kadar ilgili gümrük idaresine başvurulması ve taşıtın ilk iktisabında ödenmesi gereken özel tüketim vergisi…

Exact normalized query/gold token overlap (no stemming, not discriminative against 4458): başvuru, davalarında, eksik, geçici, gümrük, kamu, kara, kararı, kısmen, müsadere, nedeniyle, vergilerinin, verilmemiş, ödenmesi, önce

Exact saved competitors (text comparison follows):

- Rank 2: `4458-gecici-madde-9-chunk-001` / `4458_gumruk_kanunu/gecici/9`, L2=0.679323077.
- Rank 3: `4458-gecici-madde-10-chunk-001` / `4458_gumruk_kanunu/gecici/10`, L2=0.701902628.
- Rank 5: `4458-madde-180-chunk-001` / `4458_gumruk_kanunu/normal/180`, L2=0.723948896.

Top-ranked wrong 4458 excerpt (rank 2): Bu maddenin yürürlüğe girdiği tarihten önce bu Kanunun 235 inci maddesi uyarınca el konularak mülkiyetin kamuya geçirilmesi kararı verilen kara ulaşım araçları ile ilgili olarak bu maddenin yürürlüğe girdiği ayı takip eden altıncı ayın sonuna kadar ilgili gümrük idaresine başvurulması ve taşıtın ilk iktisabında ödenen özel tüketim vergisinin %25’ine tekabül eden tutarın, başvuru tarihinden itibaren bir ay içinde ilgili tahsil dairesine ödenmesi halinde, el konularak mülkiyetin kamuya geçirilmesi kararı kaldırılır ve el konulan araç, sahibine iade edilir. Bu karar gümrük idaresi tarafından ilgili mahkemeye bildirilir. Tasfiyesi tamamlanmış ulaşım araçları için bu fıkra kapsamında başvurular kabul edilmez.

Shared query/target/competitor tokens: gümrük, kara, kararı, ödenmesi, önce
Target query terms absent from competitor: davalarında, eksik, kamu, kısmen, müsadere, nedeniyle, vergilerinin, verilmemiş
Query terms present in wrong competitor: başvuru, geçici, gümrük, kara, kararı, ödenmesi, önce
Exact normalized tokens; correct terms use displayed target excerpts, wrong terms use the ranked chunk. Unique means absent from this competitor, not legally unique. Inflections are not stemmed.

SUPPORTED INTERPRETATION; token sets and excerpts OBSERVED; embedding causality UNPROVEN HYPOTHESIS: 4458 transitional Article 9 also addresses seized land vehicles, application deadlines, payment, return and completed liquidation exclusions. Its Article 235/confiscated-public-property and special-consumption-tax scheme differs from the requested 5607 transitional Article 10. The actual Top1 is 5607 transitional Article 11; this 4458 competitor is rank 2.


### k5607-030

Madde 5 fıkra 2(b) uyarınca kovuşturma evresinde hangi ödeme karşılığında ne oranda ceza indirimi uygulanır; Geçici Madde 12 fıkra 1 bu imkânı hüküm verilmiş ve dosyası infaz aşamasındaki kişilere hangi ödeme ve geçici süre koşullarıyla tanır?

Explicit 5607/query-input number: False. Expected: 5607_kacakcilikla_mucadele_kanunu/gecici/12, 5607_kacakcilikla_mucadele_kanunu/normal/5.

- `5607-madde-5-chunk-001`, fıkra 2: …ı verilecek ceza yarı oranında, b) Kovuşturma evresinde hüküm verilinceye kadar ödediği takdirde, hakkında bu Kanunda tanımlanan kaçakçılık suçlarından dolayı verilecek ceza üçte bir oranında, indirilir. Bu husus, soruşturma evresinde Cumhuriyet savcısı tarafından şüpheliye ihtar edilir. Soruşturma evresinde ihtar yapılmaması hâlinde kovuşturma evresinde hâkim tarafından sanığa ihtar yapılır. (3) (Ek:14/4/2020-7242/62 md.) İkinci fıkra hükmü, mük…
- `5607-gecici-madde-12-chunk-001`, fıkra 1: …a hüküm verilmiş olup da dosyası infaz aşamasında olanlar, bu maddenin yürürlüğe girdiği tarihten itibaren doksan gün içinde suç konusu eşyanın gümrüklenmiş değerinin iki katı kadar parayı Devlet Hazinesine ödedikleri takdirde Kanunun 5 inci maddesinin ikinci fıkrasının (b) bendinde bu maddeyi ihdas eden Kanunla yapılan düzenlemeden faydalanabilir. (2) Bu maddenin yürürlüğe girdiği tarihte bu Kanunun kapsamına giren suçlardan dolayı kanun yolu in…

Exact normalized query/gold token overlap (no stemming, not discriminative against 4458): b, ceza, dosyası, evresinde, geçici, hüküm, infaz, kovuşturma, verilmiş

Exact saved competitors (text comparison follows):

- No 4458 competitor in the saved five.

## Evidence-backed taxonomy

Classification describes observed properties, not measured causal attribution. A (cross-document terminology), B (generic legal wording as a cause), C (more like 4458), and G (strong paraphrase mismatch) are not assigned: causal attribution is not established; descriptive cross-document overlap is supplied above. D is limited to observed failure of an explicit number to enforce document choice, not a demonstrated weak vector prefix. E/F/H/I evidence follows.

- **k5607-002 / D — Explicit number did not enforce document discrimination; prefix weakness itself is unproven:** Raw query explicitly includes 5607 and gümrüklenmiş değer, yet all five ranked documents are 4458. Document prefix includes 5607 Sayılı Kaçakçılıkla Mücadele Kanunu; no query enrichment or law filter exists.
- **k5607-003 / E — Observed broad expected source; causal contribution unproven:** Madde 3: 8,425 article characters, 23 numbered fıkra positions in 3 chunks. Target text is in chunk 001 (fıkra 1/2/9). The same chunk succeeds for k5607-005.
- **k5607-003 / I — Close paraphrase still loses the expected document:** Query tabi tutulmadan ülkeye sokulması / gümrük kapıları parallels 3(1) tabi tutmaksızın ülkeye sokan / gümrük kapıları. Strong wording mismatch is not demonstrated.
- **k5607-004 / E — Observed broad expected source; causal contribution unproven:** Madde 3: 8,425 article characters, 23 numbered fıkra positions in 3 chunks. Target text is in chunk 001 (fıkra 1/2/9). The same chunk succeeds for k5607-005.
- **k5607-004 / H — Observed cross-reference/composite requirement, not a causal estimate:** Madde 3(9) explicitly refers to 4458 for the <=10% discrepancy exception.
- **k5607-007 / I — Observed same-document, wrong-Article Top1:** Madde 3 wins over gold Madde 4 (rank 3); query asks örgüt/three-person aggravation, gold 4(1)-(2).
- **k5607-009 / H — Observed cross-reference/composite requirement, not a causal estimate:** Question asks when Madde 3 applies; its gold is Madde 6(4), which explicitly refers to Madde 3.
- **k5607-009 / F — Observed slot competition; counterfactual replacement unknown:** 4458 Madde 235 occupies two Top5 slots for k5607-009 and k5607-025; only four distinct provisions remain. No 5607 Madde 3 duplicates occur in any complete miss.
- **k5607-013 / I — Observed same-document, wrong-Article Top1:** Madde 10 wins over gold Madde 11 (rank 2); query asks delivery tutanak, while Madde 10 addresses seizure/vehicle handling.
- **k5607-014 / I — Close paraphrase still loses the expected document:** Query yasak eşya / yükleme veya taşıma belgeleri parallels 12(1) closely. Gold is only 504 characters and one chunk, ruling out broad-Article structure as a universal explanation.
- **k5607-015 / I — Observed same-document, wrong-Article Top1:** Madde 10 wins over gold Madde 13 (rank 2); 10(2) explicitly cites 13(1)(a), connecting the provisions.
- **k5607-019 / I — Observed same-document, wrong-Article Top1:** Madde 24 wins over gold Madde 19 (rank 2); 24(1) repeats önlenme, izlenme ve araştırılması but addresses laboratories.
- **k5607-025 / E — Observed broad expected source; causal contribution unproven:** Madde 3: 8,425 article characters, 23 numbered fıkra positions in 3 chunks. Target text is in chunk 001 (fıkra 1/2/9). The same chunk succeeds for k5607-005.
- **k5607-025 / H — Observed cross-reference/composite requirement, not a causal estimate:** Query asks simultaneously for 3(1), 4(1) and 4(7); all five returned chunks belong to 4458.
- **k5607-025 / F — Observed slot competition; counterfactual replacement unknown:** 4458 Madde 235 occupies two Top5 slots for k5607-009 and k5607-025; only four distinct provisions remain. No 5607 Madde 3 duplicates occur in any complete miss.
- **k5607-026 / E — Observed broad expected source; causal contribution unproven:** Madde 3: 8,425 article characters, 23 numbered fıkra positions in 3 chunks. Target text is in chunk 001 (fıkra 1/2/9). The same chunk succeeds for k5607-005.
- **k5607-026 / H — Observed cross-reference/composite requirement, not a causal estimate:** Query asks for 3(1) and 5(2)-(3); all five returned chunks belong to 4458.
- **k5607-029 / E — Observed broad expected source; causal contribution unproven:** Madde 3: 8,425 article characters, 23 numbered fıkra positions in 3 chunks. Target text is in chunk 001 (fıkra 1/2/9). The same chunk succeeds for k5607-005.
- **k5607-029 / H — Observed cross-reference/composite requirement, not a causal estimate:** Query requires 3(2) and Geçici 10. Geçici 11 wins Top1; its wording also concerns 3(2), underpaid customs taxes and vehicles, and explicitly references 4458 Geçici 10.

## Article length and chunk structure

Exact lengths come from accepted local Article text checked against concatenated chunks. All failed expected provisions exist in the local corpus. Fıkra locations and individual chunk IDs/ranges are in JSON and case snippets above.

| ID | Expected source | Article characters | Chunks | Multi-chunk |
|---|---|---:|---:|---|
| k5607-002 | 5607_kacakcilikla_mucadele_kanunu/normal/2 | 682 | 1 | False |
| k5607-003 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | 8425 | 3 | True |
| k5607-004 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | 8425 | 3 | True |
| k5607-005 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | 8425 | 3 | True |
| k5607-006 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | 8425 | 3 | True |
| k5607-007 | 5607_kacakcilikla_mucadele_kanunu/normal/4 | 2070 | 1 | False |
| k5607-009 | 5607_kacakcilikla_mucadele_kanunu/normal/6 | 322 | 1 | False |
| k5607-013 | 5607_kacakcilikla_mucadele_kanunu/normal/11 | 3309 | 1 | False |
| k5607-014 | 5607_kacakcilikla_mucadele_kanunu/normal/12 | 504 | 1 | False |
| k5607-015 | 5607_kacakcilikla_mucadele_kanunu/normal/13 | 1080 | 1 | False |
| k5607-017 | 5607_kacakcilikla_mucadele_kanunu/normal/16/a | 3329 | 1 | False |
| k5607-019 | 5607_kacakcilikla_mucadele_kanunu/normal/19 | 1418 | 1 | False |
| k5607-023 | 5607_kacakcilikla_mucadele_kanunu/normal/23 | 7509 | 2 | True |
| k5607-025 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | 8425 | 3 | True |
| k5607-025 | 5607_kacakcilikla_mucadele_kanunu/normal/4 | 2070 | 1 | False |
| k5607-026 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | 8425 | 3 | True |
| k5607-026 | 5607_kacakcilikla_mucadele_kanunu/normal/5 | 1352 | 1 | False |
| k5607-028 | 5607_kacakcilikla_mucadele_kanunu/gecici/7 | 192 | 1 | False |
| k5607-029 | 5607_kacakcilikla_mucadele_kanunu/gecici/10 | 1057 | 1 | False |
| k5607-029 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | 8425 | 3 | True |
| k5607-030 | 5607_kacakcilikla_mucadele_kanunu/gecici/12 | 830 | 1 | False |
| k5607-030 | 5607_kacakcilikla_mucadele_kanunu/normal/5 | 1352 | 1 | False |

Madde 3 chunk 001 surrounds the targeted import and export offences with transit, temporary import, prohibited goods, fuel and marker offences. The target is present and concentrated within its fıkra, but the vector covers all 11 fıkras. Madde 23 is also broad: 7,509 characters split 3,766/3,742 (fıkra 1–4 / 5–9); k5607-023 succeeds on chunk 001 and no saved Top5 repeats this source. Multi-chunk structure alone is therefore not sufficient to predict failure.

## Slot competition: all 105 saved rankings

6 questions have repeated DocumentSourceKeys through different chunk IDs; each has 4 distinct provisions in 5 slots (6 redundant slots total). Different Articles are not duplicates.

- q041: {'5607_kacakcilikla_mucadele_kanunu/normal/3': 2}
- gk012: {'4458_gumruk_kanunu/normal/167': 2}
- gk026: {'4458_gumruk_kanunu/gecici/6': 2}
- k5607-005: {'5607_kacakcilikla_mucadele_kanunu/normal/3': 2}
- k5607-009: {'4458_gumruk_kanunu/normal/235': 2}
- k5607-025: {'4458_gumruk_kanunu/normal/235': 2}

By repeated provision document: 4458=4 question cases, 5607=2, 5326=0. Of the six complete 5607 misses, only 025 has duplicates (4458/235); 009 also repeats 4458/235 but finds gold rank 3. No duplicate-source competition in 029. Diversification would increase distinct-source count but its effect on gold coverage cannot be recovered from Top5 alone. No deduplication was performed.

## Failure versus successful controls

Groups are descriptive and small. Question-length tokenizer excludes numeric strings; explicit 5607 is measured separately. Exact token overlap ignores Turkish inflections and says nothing about vector similarity. Direct/paraphrase style is not inferred as a binary psychological category; explicit references and frozen case categories are stored per question.

```json
{
  "complete_misses": {
    "count": 6,
    "ids": [
      "k5607-002",
      "k5607-003",
      "k5607-004",
      "k5607-014",
      "k5607-025",
      "k5607-026"
    ],
    "explicit_5607_count": 1,
    "multi_source_count": 2,
    "mean_query_tokens": 25.5,
    "mean_exact_query_gold_overlap": 0.5875420875420876,
    "mean_top1_distance": 0.707855741182963,
    "mean_document_intrusion_at5": 1.0,
    "mean_expected_article_chars": 4695.333333333333,
    "mean_expected_source_chunks": 2
  },
  "all_source_top5_successes": {
    "count": 23,
    "ids": [
      "k5607-001",
      "k5607-005",
      "k5607-006",
      "k5607-007",
      "k5607-008",
      "k5607-009",
      "k5607-010",
      "k5607-011",
      "k5607-012",
      "k5607-013",
      "k5607-015",
      "k5607-016",
      "k5607-017",
      "k5607-018",
      "k5607-019",
      "k5607-020",
      "k5607-021",
      "k5607-022",
      "k5607-023",
      "k5607-024",
      "k5607-027",
      "k5607-028",
      "k5607-030"
    ],
    "explicit_5607_count": 5,
    "multi_source_count": 3,
    "mean_query_tokens": 18.782608695652176,
    "mean_exact_query_gold_overlap": 0.5462979157887625,
    "mean_top1_distance": 0.6832512992879619,
    "mean_document_intrusion_at5": 0.2608695652173913,
    "mean_expected_article_chars": 2108.891304347826,
    "mean_expected_source_chunks": 1.2173913043478262
  },
  "requested_controls": {
    "count": 4,
    "ids": [
      "k5607-017",
      "k5607-023",
      "k5607-028",
      "k5607-030"
    ],
    "explicit_5607_count": 0,
    "multi_source_count": 1,
    "mean_query_tokens": 19.5,
    "mean_exact_query_gold_overlap": 0.5318223443223443,
    "mean_top1_distance": 0.7596498429775238,
    "mean_document_intrusion_at5": 0.1,
    "mean_expected_article_chars": 3030.25,
    "mean_expected_source_chunks": 1.25
  }
}
```

Complete misses include one explicitly numbered query (002), whereas all four requested successful controls omit 5607. Thus lack of a number is neither necessary nor sufficient for failure. Short one-chunk 2 and 12 also fail. Geçici 7 succeeds; composite Geçici 12 + Madde 5 succeeds; Geçici 10 + Madde 3 partially fails. A blanket transitional-provision explanation is unsupported.

## Offline lexical statistics

Turkish I/İ-aware lowercase; Unicode alphabetic tokens; exact contiguous phrase frequency / 10,000 body tokens and chunk DF. No stemming: gümrük does not count gümrüğe; phrases do not count inflected variants. Descriptive only, not embedding causality.

Descriptive lexical evidence, not embedding-causality evidence. 4458 uses the deterministically reconstructed corpus; 5607 uses accepted chunks.

| Law | Term | Occurrences | Per 10k tokens | Chunk DF | Chunk DF rate |
|---|---|---:|---:|---:|---:|
| 4458 | gümrük | 1134 | 352.47 | 231 / 276 | 83.6957% |
| 4458 | eşya | 290 | 90.14 | 118 / 276 | 42.7536% |
| 4458 | gümrük vergileri | 70 | 21.76 | 42 / 276 | 15.2174% |
| 4458 | ithalat | 140 | 43.51 | 69 / 276 | 25.0000% |
| 4458 | ihracat | 71 | 22.07 | 38 / 276 | 13.7681% |
| 4458 | tasfiye | 18 | 5.59 | 7 / 276 | 2.5362% |
| 4458 | müsadere | 3 | 0.93 | 2 / 276 | 0.7246% |
| 4458 | gümrük işlemleri | 17 | 5.28 | 13 / 276 | 4.7101% |
| 4458 | taşıt | 14 | 4.35 | 11 / 276 | 3.9855% |
| 4458 | yasak eşya | 0 | 0.00 | 0 / 276 | 0.0000% |
| 5607 | gümrük | 67 | 107.32 | 23 / 46 | 50.0000% |
| 5607 | eşya | 38 | 60.87 | 17 / 46 | 36.9565% |
| 5607 | gümrük vergileri | 5 | 8.01 | 3 / 46 | 6.5217% |
| 5607 | ithalat | 1 | 1.60 | 1 / 46 | 2.1739% |
| 5607 | ihracat | 1 | 1.60 | 1 / 46 | 2.1739% |
| 5607 | tasfiye | 22 | 35.24 | 6 / 46 | 13.0435% |
| 5607 | müsadere | 15 | 24.03 | 7 / 46 | 15.2174% |
| 5607 | gümrük işlemleri | 0 | 0.00 | 0 / 46 | 0.0000% |
| 5607 | taşıt | 5 | 8.01 | 3 / 46 | 6.5217% |
| 5607 | yasak eşya | 2 | 3.20 | 2 / 46 | 4.3478% |

## Strongest 4458 competitors

Topics below summarize actual text; they are not invented Article titles. Question counts deduplicate multiple slots from the same provision.

| Article | Topic | Questions | Top1 wins | Relevant exact query terms |
|---|---|---:|---:|---|
| 235 | Administrative penalties for prohibited/restricted imports/exports, declaration discrepancies and passenger goods | 7 | 1 | alınır, arasında, aykırı, ek, eşya, eşyanın, eşyası, gelen, gümrük, gümrüklenmiş, gümrüğe, hükümlerine, idaresine, ihraç, iki, kapsamında, para, tabi, taşıma, çıkan, ülkeye |
| 57 | Intellectual-property goods: detention, suspension of customs procedures and disposal | 3 | 2 | aynı, ek, eşya, eşyanın, gümrük, kapsamında, tabi |
| 236 | Warehouse irregularities, unauthorized removal and administrative fines | 3 | 1 | ek, eşya, eşyanın, gümrük, hükümlerine, iki, işlemlerine, para, tabi, çıkan |
| 25 | Alternative customs valuation methods | 2 | 1 | cins, ihraç, ithal |
| 24 | Customs transaction value and sale-price conditions | 2 | 0 | gibi, gümrük, ihraç, tabi, ödeme |
| 167 | Customs tax exemptions, including personal and passenger goods | 2 | 0 | ek, eşya, eşyası, eşyayı, gümrük, iki, kişi, tabi, taşıma, çerçevesinde, çıkan |

235 is plausible for valuation, import/export penalties and passenger questions; 57 for customs-procedure suspension/enforcement wording; 236 for goods moved before procedures finish; 24/25 for valuation; 167 for personal/passenger tax exemptions. Their legal consequences differ from the 5607 targets. Exact opening excerpts and affected question IDs are retained in JSON.

## Evidence levels

- **OBSERVED:** Seven of 12 wrong Top1 results are wrong-document (58.33%); five are same-document wrong Article (41.67%). Six of seven ALL@5 failures exclude 5607 (85.71%); one is partial. All 525 saved rank-text hashes match local/reconstructed texts. No demonstrated source omission/provenance defect.
- **SUPPORTED INTERPRETATION:** Document discrimination dominates observed Top5 failures. Actual 4458 procedure, valuation, passenger and vehicle provisions supply plausible cross-law competition. Broad Madde 3 mixes offence families in a shared vector input; this is a plausible contributor, not a demonstrated material effect.
- **UNPROVEN HYPOTHESIS:** Embedding causality, dilution effect size, effects of reranking/diversification, and the cause of gk001 omission remain unproven. No 5607 displacement of gk001 is observed.

5326 normalized statistics are also provided in JSON. Counts use body text only, excluding enrichment prefixes and avoiding artificial title repetitions.

## Historical 4458 regression

| Metric | M10D @1/3/5 | M12D @1/3/5 | Delta (percentage points) |
|---|---|---|---|
| ANY | 56.67 / 73.33 / 80.00 | 53.33 / 70.00 / 76.67 | -3.33 / -3.33 / -3.33 |
| ALL | 46.67 / 66.67 / 76.67 | 43.33 / 63.33 / 73.33 | -3.33 / -3.33 / -3.33 |

gk001 alone accounts for all six -3.33 percentage-point changes. No 5607 chunk in any of the 150 current 4458 slots. Old Madde 210 at 0.727341 disappears; old ranks 2-5 retain exactly their distances and move to 1-4. Direct 5607 displacement is not supported; ANN candidate omission or another unobserved retrieval-state difference remains unresolved, not diagnosed.

All 30 paired old/current rankings and changes are stored in JSON. We cannot infer that adding 5607 caused the gk001 omission merely because it occurred later. A future authorized candidate-completeness investigation should precede attributing this regression to semantic competition.

## Future experiments — analysis only

No production winner is selected. M10E B2 was NOT validated and is not a production candidate by default. Every newly designed candidate informed by M12D/M12E is development-informed; **future adoption requires a new unseen holdout**, in addition to these diagnostic development questions.

| Direction | Target / likely benefit | Risk | Production semantics change if adopted? | Re-embedding required? | New unseen holdout? |
|---|---|---|---|---|---|
| Explicit-law query normalization/title enrichment; separately test an explicit-law filter | Document discrimination, especially explicit 002; make named scope usable | Wrong user number, cross-law questions, query drift; only a minority of failures name 5607 | Yes, query input or candidate scope | No corpus re-embedding; query embeddings change for normalization | Yes |
| Source-aware reranking / fıkra-focused candidate scoring; separately test broad-Article chunking | Madde 3 topical breadth and composite 025/026/029, same-law Article mistakes | Gold cannot be recovered if absent from candidate pool; overfitting, lost context | Yes, ranking or index representation | Reranking alone: no; changed chunks/document embedding text: yes | Yes |
| Larger candidate K plus completeness diagnostic before downstream selection | Censored complete misses and unexplained gk001 omission | Cost/noise; saved evidence cannot estimate recovery | Yes if adopted for retrieval; offline diagnostic alone no | No corpus re-embedding | Yes for adoption |
| Distinct-source diversification | Six repeated-slot cases, especially 009/025 | May remove complementary fıkra evidence; most complete misses have no duplicates | Yes | No | Yes |
| Hybrid lexical+dense | Close gold phrasing in 003/004/014; hypothesis supported by descriptive text comparison, not tested | Shared terms may strengthen wrong law; M10E B2 not validated | Yes | No dense re-embedding; lexical index required | Yes |
| Document routing | Six complete wrong-document misses | Routing errors hide correct law; cross-document questions; must route on evidence, not gold labels | Yes | Depends on route implementation; not inherently | Yes |

No interventions were implemented or benchmarked. The top three investigation directions are the first three rows; ordering is informed by the verified competitor texts, with benefits still untested.

## Review boundary

Only this analysis Markdown/JSON, the human-auditable CSV matrix and the offline analysis script using the accepted parser/chunker are created. No production module, frozen dataset or M12D report is modified. No commit. Test-gate outcome is reported at delivery.
