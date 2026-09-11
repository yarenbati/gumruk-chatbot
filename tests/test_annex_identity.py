from src.source_identity import AnnexSourceKey


def test_equivalent_annex_labels_have_one_identity() -> None:
    keys = {AnnexSourceKey.from_label(value) for value in ("EK-77/A", "EK 77 A", "EK-77-A")}
    assert len(keys) == 1
    key = next(iter(keys))
    assert str(key) == "gumruk_yonetmeligi/annex/77/a"
    assert key.label == "EK-77/A"


def test_annex_keys_and_storage_ids_are_distinct_and_scoped() -> None:
    assert AnnexSourceKey.from_label("EK-62") != AnnexSourceKey.from_label("EK-63")
    assert AnnexSourceKey.from_label("EK-62").storage_id == "gumruk_yonetmeligi-ek-62"
    assert AnnexSourceKey.from_label("EK-62", "other_document").storage_id == "other_document-ek-62"


def test_annex_keys_have_deterministic_sorting() -> None:
    assert sorted((AnnexSourceKey.from_label("EK-77/A"), AnnexSourceKey.from_label("EK-77")))[0].label == "EK-77"
