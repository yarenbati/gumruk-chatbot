# Demo guide

Five representative questions for demonstrating the RAG pipeline: three
**success demos** that show clean retrieval/citation behavior, and two
**limitation demos** that intentionally show where the current system is
weaker (a documented benchmark miss, and an untested edge case). All
questions are in Turkish, matching the corpus and the assistant's fixed
output language.

Run any of them via the Streamlit app (`python -m streamlit run app.py`) or
the CLI:

```powershell
$env:RUN_OPENAI_INTEGRATION_TESTS = "1"
python -m src.rag "<question>"
```

Both require `OPENAI_API_KEY` and `RUN_OPENAI_INTEGRATION_TESTS=1`.

Retrieval-side numbers below (rank, hit@1) come from the frozen M13D-B
benchmark (`reports/evaluation/m13db-four-source-retrieval.json`) — that run
performed retrieval only, no generation. The generation-side behavior
(`DURUM: YETERLI`/`YETERSIZ`, citation labels) described for each question is
what the citation model in `src/generate.py` is *designed* to produce; it has
not itself been re-verified against a live model run as part of this guide.

## Success demos

### 1. Simple article question

> **Gümrük Yönetmeliğinin amacı ve kapsamı nedir?**

Gold ID `gy-001`. A single expected article (`gumruk_yonetmeligi/normal/1`)
retrieved at rank 1 (hit@1 = true). Demonstrates the baseline case: one
clear source, one clean citation.

### 2. Annex question

> **Geçici depolama yeri ve antrepoya alınması bakımından özellik gösteren tehlikeli eşyaya ilişkin liste hangi sınıflandırmaya dayanır?**

Gold ID `gy-017`. Expects `gumruk_yonetmeligi/annex/62` (EK-62), retrieved
at rank 1. Demonstrates that annex identity (`AnnexSourceKey`) is retrieved
and cited distinctly from article identity, even though both live in the
same `gumruk_yonetmeligi` document.

### 3. Mixed article + annex question

> **Bağlayıcı tarife bilgisine başvuru kaç kalem eşya için yapılabilir ve kullanılacak başvuru formunda başvuru sahibi nasıl tanımlanır?**

Gold ID `gy-025`. Expects both `gumruk_yonetmeligi/normal/28` (rank 1) and
its referenced annex form `gumruk_yonetmeligi/annex/1` (rank 2) — full
two-source coverage in the top-5. Demonstrates an answer that should cite
two different `[KAYNAK N]` blocks from two different structural parts of the
same regulation.

## Limitation demos

### 4. Cross-document ambiguity (known M13D-B partial-coverage case)

> **Serbest dolaşımda bulunmayan eşyanın antrepoda elleçlenmesine izin verilmesine ilişkin hüküm ile bu faaliyetlerin tarife pozisyonuna etkisini sınırlayan ek birlikte nerede düzenlenmiştir?**

Gold ID `gy-027`, one of the two documented M13D-B mixed-question partials
(the other is `gy-026`). This is a **known limitation**, included
deliberately so a viewer sees a real miss, not only successes. Expects both
`gumruk_yonetmeligi/normal/334` and `gumruk_yonetmeligi/annex/63`; only the
annex is found in the top-5 (rank 1). A `4458_gumruk_kanunu` chunk appears
at rank 2, and the second expected `gumruk_yonetmeligi` source is absent
from the top-5 — consistent with possible cross-document semantic
competition, but the benchmark only observes the resulting ranks, so that
cause is not proven, only plausible. Good for showing that retrieval can be
confidently right about one expected source while missing the other, with a
different-document chunk present in between.

### 5. Insufficient-evidence question (untested edge case, not a promised refusal)

> **Antrepo işletmecisinin gümrük vergilerinden doğan mali sorumluluğu için hangi sigorta prim oranı uygulanır?**

Not a gold-set question — chosen because no indexed provision appears to
specify an insurance premium rate for bonded-warehouse operators, so it is
plausibly outside what the four sources actually support. Per the citation
model's design (see README § *Source and citation model*), the intended
behavior is `DURUM: YETERSIZ` with an explicit statement that the sources do
not establish an answer, rather than an invented rate. **This has not been
verified against a live run** — M13D-B measured retrieval only, with zero
generation calls, and no end-to-end check of this specific question has been
performed. Treat a live run of this question as an open test of intended
behavior, not a demonstration of a confirmed refusal.
