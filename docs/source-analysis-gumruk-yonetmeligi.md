# Gümrük Yönetmeliği Source Analysis

## Provenance

- Main: `data\raw\gumruk-yonetmeligi.docx`, 414696 bytes, SHA256 `5ac00a49016e59dd1f63f7eec21c6a9ddda0381ef40616ef6113d97f920d52eb`.
- Annex package: `data\raw\gumruk-yonetmeligi-ekler.zip`, 2077576 bytes, SHA256 `aa3be601f14e39286edfe5cf7f4219c6563fb441fcab504bbb273f4078f97121`.
- The main text was supplied as DOCX and the annexes as a separate ZIP. Both are immutable admitted raw artifacts.
- The annex package belongs to the same `gumruk_yonetmeligi` corpus and is not 83 unrelated legal documents.
- The source material supports the regulation's basis in 4458 Gümrük Kanunu; 4458 is not the regulation's canonical identity.

- Manifest identity: gumruk_yonetmeligi; title: Gümrük Yönetmeliği; document_type: Yönetmelik; legislation_number: null.\n- Official identity: MevzuatNo=13472, MevzuatTur=7, MevzuatTertip=5; official URL: https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=13472&MevzuatTur=7&MevzuatTertip=5; retrieved_at: 2026-09-11.\n- Issuing authority is left null because the admitted provenance does not support an authoritative value without invention.\n\n## Main Regulation File

{
  "ooxml_valid": true,
  "paragraph_count": 3903,
  "non_empty_paragraph_count": 3695,
  "table_count": 2,
  "table_dimensions": [
    [
      20,
      3
    ],
    [
      42,
      3
    ]
  ],
  "table_roles": [
    "table content is outside current paragraph extractor; requires table-aware audit/ingestion",
    "table content is outside current paragraph extractor; requires table-aware audit/ingestion"
  ]
}

## Structural Hierarchy

Hierarchy counts: `{"KİTAP": 12, "KISIM": 33, "BÖLÜM": 22}`.
Examples: `{"KİTAP": ["BİRİNCİ KİTAP", "İKİNCİ KİTAP", "ÜÇÜNCÜ KİTAP", "DÖRDÜNCÜ KİTAP", "BEŞİNCİ KİTAP"], "KISIM": ["BİRİNCİ KISIM", "İKİNCİ KISIM", "BİRİNCİ KISIM", "İKİNCİ KISIM", "ÜÇÜNCÜ KISIM"], "BÖLÜM": ["BİRİNCİ BÖLÜM", "İKİNCİ BÖLÜM", "ÜÇÜNCÜ BÖLÜM", "DÖRDÜNCÜ BÖLÜM", "BEŞİNCİ BÖLÜM"]}`.
The observed dominant hierarchy is KİTAP > KISIM > BÖLÜM, with AYIRIM also present where detected. The current Article.section_context stores a combined string, so it preserves a readable context but does not provide typed hierarchy fields.

## Provision Inventory

{
  "article_like_units": 528,
  "plain_numeric_articles": 488,
  "suffixed_articles": 27,
  "temporary_articles": 13,
  "ek_articles": 0
}
- Suffix letters: A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, R, S, T, Ç, Ö, Ğ, İ, Ş.
- Numeric range: 1–593.
- Numeric gaps: 104 values; gaps are not treated as errors because repeal and structural absence are possible.
- Duplicate labels: `['1', '2', '3']`.

## Article Internal Structure

{
  "fikra_parenthesized": 750,
  "lettered_bent": 116,
  "numbered_alt_bent": 4,
  "mülga": 144,
  "degisik": 523,
  "ek_annotations": 185,
  "rg_references": 777,
  "court_annotations": 27,
  "article_titles": 483,
  "inline_footnote_reference_ids": 0
}

## Tables / Footnotes / Amendments

{
  "footnote_history": {
    "footnotes_xml_present": false,
    "amendment_history_marker_present": false,
    "history_blocks_are_not_resolved_by_current_parser": true
  },
  "table_count": 2,
  "table_dimensions": [
    [
      20,
      3
    ],
    [
      42,
      3
    ]
  ]
}

## Existing Ingestion Compatibility

The current DOCX extractor succeeded and returned 3695 non-empty body paragraphs in order. It does not include table-cell text in the paragraph stream; the two tables therefore require table-aware extraction before they can be part of a complete regulation corpus.

## Existing Parser / Chunker Compatibility

{
  "success": true,
  "error": null,
  "article_count": 524,
  "article_type_distribution": {
    "normal": 511,
    "gecici": 13
  },
  "first": {
    "article_no": "1",
    "article_type": "normal"
  },
  "last": {
    "article_no": "1",
    "article_type": "gecici"
  },
  "chunk_count": 526,
  "multi_chunk_provision_count": 2,
  "duplicate_article_ids": [],
  "duplicate_chunk_ids": [],
  "section_samples": [
    {
      "article_no": "1",
      "article_type": "normal",
      "section_context": "Birinci Kısım"
    },
    {
      "article_no": "72/A",
      "article_type": "normal",
      "section_context": "İkinci Kısım"
    },
    {
      "article_no": "580/A",
      "article_type": "normal",
      "section_context": "Birinci Kısım"
    },
    {
      "article_no": "2",
      "article_type": "gecici",
      "section_context": "Üçüncü Kısım"
    },
    {
      "article_no": "3",
      "article_type": "gecici",
      "section_context": "Üçüncü Kısım"
    },
    {
      "article_no": "4",
      "article_type": "gecici",
      "section_context": "Üçüncü Kısım"
    },
    {
      "article_no": "5",
      "article_type": "gecici",
      "section_context": "Üçüncü Kısım"
    },
    {
      "article_no": "6",
      "article_type": "gecici",
      "section_context": "Üçüncü Kısım"
    },
    {
      "article_no": "7",
      "article_type": "gecici",
      "section_context": "Üçüncü Kısım"
    },
    {
      "article_no": "10",
      "article_type": "gecici",
      "section_context": "Üçüncü Kısım"
    },
    {
      "article_no": "11",
      "article_type": "gecici",
      "section_context": "Üçüncü Kısım"
    },
    {
      "article_no": "13",
      "article_type": "gecici",
      "section_context": "Üçüncü Kısım"
    },
    {
      "article_no": "17",
      "article_type": "gecici",
      "section_context": "Üçüncü Kısım"
    },
    {
      "article_no": "18",
      "article_type": "gecici",
      "section_context": "Üçüncü Kısım"
    },
    {
      "article_no": "19",
      "article_type": "gecici",
      "section_context": "Üçüncü Kısım"
    },
    {
      "article_no": "1",
      "article_type": "gecici",
      "section_context": "Üçüncü Kısım"
    }
  ],
  "reconstruction_tested": 524,
  "reconstruction_failures": [],
  "suffix_family_present": false
}

The raw heading audit found 528 article-like starts; the current parser produced 524 Article objects. It recognized normal and Geçici Madde namespaces, but it did not recognize the Turkish suffixed labels 72/Ç, 72/Ö, 72/Ğ, and 72/Ş. These are explicit M13B parser requirements. The hierarchy is represented as a combined section_context string rather than a structured KİTAP/KISIM/BÖLÜM object; the current section branch does not preserve BÖLÜM correctly and this is an M13B requirement.

## Reconstruction Audit

Every one of 524 parsed Articles was rebuilt through the current chunker. Exact reconstruction failures: 0. Multi-chunk provisions: 2.

## Annex Package Provenance

{
  "zip_integrity": true,
  "entry_count": 87,
  "file_count": 87,
  "directory_count": 0,
  "duplicate_names": [],
  "zero_byte_files": [],
  "risk_counts": {
    "B legacy OLE Word DOC": 68,
    "D legacy spreadsheet XLS": 5,
    "F form/table-heavy Word": 7,
    "A ordinary text DOCX": 5,
    "E spreadsheet XLSX": 1,
    "C RTF / extension-mismatched text": 1
  },
  "special_signatures": {
    "EK-48.doc": "RTF"
  }
}

## Annex Archive Inventory

| Archive file | Label | Format/signature | Size | Risk | Orientation |
|---|---|---|---:|---|---|
| `EK 01.doc` | EK-1 | OLE/Compound File (likely legacy DOC) | 48640 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 02.doc` | EK-2 | OLE/Compound File (likely legacy DOC) | 41984 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 03.doc` | EK-3 | OLE/Compound File (likely legacy DOC) | 46080 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 04.doc` | EK-4 | OLE/Compound File (likely legacy DOC) | 42496 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 05.doc` | EK-5 | OLE/Compound File (likely legacy DOC) | 74752 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 06.doc` | EK-6 | OLE/Compound File (likely legacy DOC) | 73216 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 07.doc` | EK-7 | OLE/Compound File (likely legacy DOC) | 87552 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 08.doc` | EK-8 | OLE/Compound File (likely legacy DOC) | 81920 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 09.doc` | EK-9 | OLE/Compound File (likely legacy DOC) | 25088 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 10.doc` | EK-10 | OLE/Compound File (likely legacy DOC) | 381440 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 11.doc` | EK-11 | OLE/Compound File (likely legacy DOC) | 159744 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 12.doc` | EK-12 | OLE/Compound File (likely legacy DOC) | 27136 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 13.doc` | EK-13 | OLE/Compound File (likely legacy DOC) | 65024 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 14.doc` | EK-14 | OLE/Compound File (likely legacy DOC) | 1558016 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 15.doc` | EK-15 | OLE/Compound File (likely legacy DOC) | 30208 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 16.doc` | EK-16 | OLE/Compound File (likely legacy DOC) | 100864 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 17.doc` | EK-17 | OLE/Compound File (likely legacy DOC) | 24576 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 18.doc` | EK-18 | OLE/Compound File (likely legacy DOC) | 32768 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 19.doc` | EK-19 | OLE/Compound File (likely legacy DOC) | 29184 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 20.doc` | EK-20 | OLE/Compound File (likely legacy DOC) | 23552 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 21.doc` | EK-21 | OLE/Compound File (likely legacy DOC) | 22016 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 22 A.doc` | EK-22/A | OLE/Compound File (likely legacy DOC) | 46592 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 22.xls` | EK-22 | OLE/Compound File (likely legacy XLS or form) | 59392 | D legacy spreadsheet XLS | spreadsheet |
| `EK 23.doc` | EK-23 | OLE/Compound File (likely legacy DOC) | 77824 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 24 Gümrük Laboratuvarlarì Tahlil Ücretleri Listesi.docx` | EK-24 | OOXML DOCX | 26186 | F form/table-heavy Word | form/table-heavy |
| `EK 25.doc` | EK-25 | OLE/Compound File (likely legacy DOC) | 22528 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 26.doc` | EK-26 | OLE/Compound File (likely legacy DOC) | 34304 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 27.doc` | EK-27 | OLE/Compound File (likely legacy DOC) | 41472 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 28.doc` | EK-28 | OLE/Compound File (likely legacy DOC) | 40960 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 29.doc` | EK-29 | OLE/Compound File (likely legacy DOC) | 29696 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 30.doc` | EK-30 | OLE/Compound File (likely legacy DOC) | 42496 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 31.doc` | EK-31 | OLE/Compound File (likely legacy DOC) | 32256 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 32.doc` | EK-32 | OLE/Compound File (likely legacy DOC) | 235520 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 33.doc` | EK-33 | OLE/Compound File (likely legacy DOC) | 31232 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 34.doc` | EK-34 | OLE/Compound File (likely legacy DOC) | 25088 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 35.doc` | EK-35 | OLE/Compound File (likely legacy DOC) | 22528 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 36.doc` | EK-36 | OLE/Compound File (likely legacy DOC) | 24064 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 37.doc` | EK-37 | OLE/Compound File (likely legacy DOC) | 40960 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 38.doc` | EK-38 | OLE/Compound File (likely legacy DOC) | 40960 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 39.doc` | EK-39 | OLE/Compound File (likely legacy DOC) | 24064 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 40.doc` | EK-40 | OLE/Compound File (likely legacy DOC) | 24576 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 41.doc` | EK-41 | OLE/Compound File (likely legacy DOC) | 22528 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 42.doc` | EK-42 | OLE/Compound File (likely legacy DOC) | 28672 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 43.doc` | EK-43 | OLE/Compound File (likely legacy DOC) | 29184 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 44.doc` | EK-44 | OLE/Compound File (likely legacy DOC) | 23040 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 45.doc` | EK-45 | OLE/Compound File (likely legacy DOC) | 26112 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 46.doc` | EK-46 | OLE/Compound File (likely legacy DOC) | 25088 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 47.doc` | EK-47 | OLE/Compound File (likely legacy DOC) | 44544 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 53.doc` | EK-53 | OLE/Compound File (likely legacy DOC) | 40960 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 54.doc` | EK-54 | OLE/Compound File (likely legacy DOC) | 24064 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 55.xls` | EK-55 | OLE/Compound File (likely legacy XLS or form) | 61440 | D legacy spreadsheet XLS | spreadsheet |
| `EK 56.xls` | EK-56 | OLE/Compound File (likely legacy XLS or form) | 72192 | D legacy spreadsheet XLS | spreadsheet |
| `EK 57.doc` | EK-57 | OLE/Compound File (likely legacy DOC) | 46592 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 58.doc` | EK-58 | OLE/Compound File (likely legacy DOC) | 35328 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 59.doc` | EK-59 | OLE/Compound File (likely legacy DOC) | 502784 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 60.xls` | EK-60 | OLE/Compound File (likely legacy XLS or form) | 23552 | D legacy spreadsheet XLS | spreadsheet |
| `EK 61.doc` | EK-61 | OLE/Compound File (likely legacy DOC) | 356864 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 62.doc` | EK-62 | OLE/Compound File (likely legacy DOC) | 32768 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 63.doc` | EK-63 | OLE/Compound File (likely legacy DOC) | 28160 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 64.doc` | EK-64 | OLE/Compound File (likely legacy DOC) | 44032 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 65.doc` | EK-65 | OLE/Compound File (likely legacy DOC) | 23040 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 66.doc` | EK-66 | OLE/Compound File (likely legacy DOC) | 45568 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 67.doc` | EK-67 | OLE/Compound File (likely legacy DOC) | 87552 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 68.doc` | EK-68 | OLE/Compound File (likely legacy DOC) | 55808 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 69.xls` | EK-69 | OLE/Compound File (likely legacy XLS or form) | 25088 | D legacy spreadsheet XLS | spreadsheet |
| `EK 70 A.doc` | EK-70/A | OLE/Compound File (likely legacy DOC) | 62976 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 70.doc` | EK-70 | OLE/Compound File (likely legacy DOC) | 54784 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 71.doc` | EK-71 | OLE/Compound File (likely legacy DOC) | 182784 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 72.doc` | EK-72 | OLE/Compound File (likely legacy DOC) | 64512 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 73.doc` | EK-73 | OLE/Compound File (likely legacy DOC) | 27136 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 74.doc` | EK-74 | OLE/Compound File (likely legacy DOC) | 30208 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 75.doc` | EK-75 | OLE/Compound File (likely legacy DOC) | 22528 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 76.doc` | EK-76 | OLE/Compound File (likely legacy DOC) | 94720 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 77.docx` | EK-77 | OOXML DOCX | 13926 | A ordinary text DOCX | text |
| `EK 78.docx` | EK-78 | OOXML DOCX | 23929 | F form/table-heavy Word | form/table-heavy |
| `EK 79.doc` | EK-79 | OLE/Compound File (likely legacy DOC) | 36864 | B legacy OLE Word DOC | text/form (legacy binary Word; reader required) |
| `EK 80.docx` | EK-80 | OOXML DOCX | 49896 | A ordinary text DOCX | text |
| `EK 81-A.docx` | EK-81/A | OOXML DOCX | 13513 | A ordinary text DOCX | text |
| `EK 81-B.docx` | EK-81/B | OOXML DOCX | 14650 | A ordinary text DOCX | text |
| `EK 82.docx` | EK-82 | OOXML DOCX | 21739 | F form/table-heavy Word | form/table-heavy |
| `EK 83.xlsx` | EK-83 | OOXML XLSX | 15688 | E spreadsheet XLSX | spreadsheet |
| `EK-48.doc` | EK-48 | RTF | 157101 | C RTF / extension-mismatched text | text |
| `EK-49 Transit Refakat Belgesi Açìklama Notlarì.docx` | EK-49 | OOXML DOCX | 25479 | F form/table-heavy Word | form/table-heavy |
| `EK-50 Kalem listesi.docx` | EK-50 | OOXML DOCX | 24455 | F form/table-heavy Word | form/table-heavy |
| `Ek-51 Kalem Listesi ÿçin Açìklayìcì notlar ve bilgiler.docx` | EK-51 | OOXML DOCX | 20334 | A ordinary text DOCX | text |
| `EK-52 Taahhütname.docx` | EK-52 | OOXML DOCX | 256935 | F form/table-heavy Word | form/table-heavy |
| `EK-81.docx` | EK-81 | OOXML DOCX | 24892 | F form/table-heavy Word | form/table-heavy |

## EK-1–EK-83 Coverage

Direct filename coverage is available for 83/83 numeric labels. This is not a logical completeness claim because a physical file can contain multiple logical annexes.

| Annex | Direct archive file | Possible parent/embedded file | Format(s) |
|---:|---|---|---|
| 1 | EK 01.doc | — | .doc |
| 2 | EK 02.doc | — | .doc |
| 3 | EK 03.doc | — | .doc |
| 4 | EK 04.doc | — | .doc |
| 5 | EK 05.doc | — | .doc |
| 6 | EK 06.doc | — | .doc |
| 7 | EK 07.doc | — | .doc |
| 8 | EK 08.doc | — | .doc |
| 9 | EK 09.doc | — | .doc |
| 10 | EK 10.doc | — | .doc |
| 11 | EK 11.doc | — | .doc |
| 12 | EK 12.doc | — | .doc |
| 13 | EK 13.doc | — | .doc |
| 14 | EK 14.doc | — | .doc |
| 15 | EK 15.doc | — | .doc |
| 16 | EK 16.doc | — | .doc |
| 17 | EK 17.doc | — | .doc |
| 18 | EK 18.doc | — | .doc |
| 19 | EK 19.doc | — | .doc |
| 20 | EK 20.doc | — | .doc |
| 21 | EK 21.doc | — | .doc |
| 22 | EK 22 A.doc, EK 22.xls | — | .doc, .xls |
| 23 | EK 23.doc | — | .doc |
| 24 | EK 24 Gümrük Laboratuvarlarì Tahlil Ücretleri Listesi.docx | — | .docx |
| 25 | EK 25.doc | — | .doc |
| 26 | EK 26.doc | — | .doc |
| 27 | EK 27.doc | — | .doc |
| 28 | EK 28.doc | — | .doc |
| 29 | EK 29.doc | — | .doc |
| 30 | EK 30.doc | — | .doc |
| 31 | EK 31.doc | — | .doc |
| 32 | EK 32.doc | — | .doc |
| 33 | EK 33.doc | — | .doc |
| 34 | EK 34.doc | — | .doc |
| 35 | EK 35.doc | — | .doc |
| 36 | EK 36.doc | — | .doc |
| 37 | EK 37.doc | — | .doc |
| 38 | EK 38.doc | — | .doc |
| 39 | EK 39.doc | — | .doc |
| 40 | EK 40.doc | — | .doc |
| 41 | EK 41.doc | — | .doc |
| 42 | EK 42.doc | — | .doc |
| 43 | EK 43.doc | — | .doc |
| 44 | EK 44.doc | — | .doc |
| 45 | EK 45.doc | — | .doc |
| 46 | EK 46.doc | — | .doc |
| 47 | EK 47.doc | — | .doc |
| 48 | EK-48.doc | — | .doc |
| 49 | EK-49 Transit Refakat Belgesi Açìklama Notlarì.docx | — | .docx |
| 50 | EK-50 Kalem listesi.docx | — | .docx |
| 51 | Ek-51 Kalem Listesi ÿçin Açìklayìcì notlar ve bilgiler.docx | — | .docx |
| 52 | EK-52 Taahhütname.docx | — | .docx |
| 53 | EK 53.doc | — | .doc |
| 54 | EK 54.doc | — | .doc |
| 55 | EK 55.xls | — | .xls |
| 56 | EK 56.xls | — | .xls |
| 57 | EK 57.doc | — | .doc |
| 58 | EK 58.doc | — | .doc |
| 59 | EK 59.doc | — | .doc |
| 60 | EK 60.xls | — | .xls |
| 61 | EK 61.doc | — | .doc |
| 62 | EK 62.doc | — | .doc |
| 63 | EK 63.doc | — | .doc |
| 64 | EK 64.doc | — | .doc |
| 65 | EK 65.doc | — | .doc |
| 66 | EK 66.doc | — | .doc |
| 67 | EK 67.doc | — | .doc |
| 68 | EK 68.doc | — | .doc |
| 69 | EK 69.xls | — | .xls |
| 70 | EK 70 A.doc, EK 70.doc | — | .doc |
| 71 | EK 71.doc | — | .doc |
| 72 | EK 72.doc | — | .doc |
| 73 | EK 73.doc | — | .doc |
| 74 | EK 74.doc | — | .doc |
| 75 | EK 75.doc | — | .doc |
| 76 | EK 76.doc | — | .doc |
| 77 | EK 77.docx | — | .docx |
| 78 | EK 78.docx | — | .docx |
| 79 | EK 79.doc | — | .doc |
| 80 | EK 80.docx | — | .docx |
| 81 | EK 81-A.docx, EK 81-B.docx, EK-81.docx | — | .docx |
| 82 | EK 82.docx | — | .docx |
| 83 | EK 83.xlsx | — | .xlsx |

## Main-Text Annex Cross-References

The main text contains 69 distinct normalized annex references. Direct matches: 60; embedded/parent candidates: 9; unresolved after filename/content sampling: 0.
Unresolved candidate list: `['EK-10/A', 'EK-10/B', 'EK-10/C', 'EK-10/E', 'EK-10/F', 'EK-10/G', 'EK-77/A', 'EK-77/B', 'EK-77/C']`.
Sub-annex resolution remains provisional for binary legacy files whose contents cannot be read by the current environment. One physical file is not assumed to be one logical annex.

## Representative Annex Samples

EK-7 and EK-10 are legacy OLE Word documents; EK-48.doc is RTF despite its `.doc` extension; EK-62 is legacy OLE Word; EK-70 has a separate A file; EK-77.docx contains EK-77 and EK 77/A sections in one physical file; EK-81-A.docx and EK-81-B.docx are separate sub-annex files; EK-83.xlsx is a modern spreadsheet.

## Annex Format / Ingestion Risk Matrix

{
  "B legacy OLE Word DOC": 68,
  "D legacy spreadsheet XLS": 5,
  "F form/table-heavy Word": 7,
  "A ordinary text DOCX": 5,
  "E spreadsheet XLSX": 1,
  "C RTF / extension-mismatched text": 1
}

Current tooling can safely inspect OOXML DOCX structure, but legacy OLE DOC/XLS, RTF, and spreadsheet/form content require dedicated adapters or format-aware extraction. No annex was converted or ingested in M13A.

## Source Identity Considerations

The canonical main identity is `gumruk_yonetmeligi`, with provision kinds article, temporary_article, and annex. Future annex metadata should preserve `annex_no`, `annex_label`, and `annex_subpart` such as EK-62, EK-77/A, and EK-81-B. Existing DocumentSourceKey is article-shaped; M13B should assess an annex-aware extension without breaking historical identity compatibility.

## Citation Considerations

Future citations should use forms such as `Gümrük Yönetmeliği Madde 81`, `Gümrük Yönetmeliği EK-62`, `Gümrük Yönetmeliği EK-77/A`, or `Gümrük Yönetmeliği Madde 81 ve EK-62`.

## Known Limitations

The audit does not convert legacy files, resolve all binary document text, or claim legal completeness from filenames. Main-document tables and footnote/history bodies need source-aware extraction. Current parser compatibility is diagnostic and does not authorize production ingestion.

## M13A Verdict

M13A READY FOR REVIEW — SOURCE ADMITTED, M13B REQUIRED

The sources are valid and usable for continued development, but generic compatibility work is required for hierarchy preservation, annex identity, legacy/special formats, table-aware extraction, and citation provenance.

## Recommended M13B Scope

1. Preserve KİTAP/KISIM/BÖLÜM/AYIRIM hierarchy in a structured context.
2. Confirm Turkish suffixed and temporary provision identity across parser and chunker paths.
3. Define annex-aware canonical provenance and citations.
4. Add safe DOC/RTF/XLS/XLSX readers and table/form extraction.
5. Re-run reconstruction and source-reference gates on an isolated M13B corpus.

## M13B-1 Compatibility Result

M13A's baseline parser produced 524 Articles because it did not recognize the
four Turkish suffix provisions `72/Ç`, `72/Ğ`, `72/Ö`, and `72/Ş`. M13B-1
extends the generic suffix grammar and now produces all 528 raw provisions:
515 `normal` Articles and 13 `gecici` Articles, with no unparsed provision
labels.

Article and chunk storage IDs remain collision-safe. ASCII historical IDs are
unchanged; Turkish suffixes use readable deterministic tokens such as
`c-cedilla`, `g-breve`, `i-dotted`, `o-umlaut`, and `s-cedilla`. The pairs
`72/C`/`72/Ç`, `72/G`/`72/Ğ`, `72/I`/`72/İ`, `72/O`/`72/Ö`, and `72/S`/`72/Ş`
remain distinct. DocumentSourceKey derivation succeeds for all 528 Articles.

The M13A/M13B pre-fix fallback used `unknown-` when legislation_number was
null. The final M13B-1 policy uses the legislation number when present and the
canonical document_id when it is absent. Gümrük Yönetmeliği IDs therefore use
`gumruk_yonetmeligi-...`; no `unknown-` Article or Chunk IDs remain. If both
identity inputs are absent, storage ID construction fails closed.

The parser now carries `KİTAP > KISIM > BÖLÜM > AYIRIM` state with generic
reset semantics. Representative contexts include `Birinci Kitap > Birinci
Kısım`, `Birinci Kitap > İkinci Kısım > İkinci Bölüm`, and
`Üçüncü Kitap > İkinci Kısım` for the 72/* family. The real source contains
no AYIRIM heading in the accepted paragraph stream; the generic AYIRIM reset
behavior is covered by focused tests.

The corrected source run produces 530 chunks, including 2 multi-chunk
provisions, and reconstructs all 528 Articles exactly. Historical regressions
remain green: 5326 produces 53 Articles/53 chunks, 4458 produces 271
Articles/276 chunks, and 5607 produces 43 Articles/46 chunks; their accepted
Article and Chunk IDs remain unchanged.

M13B-1 does not modify the main-document table ingestion limitation. Annex
ingestion, annex identity, citation changes, embeddings, indexing, and
retrieval remain deferred to later M13 work.
