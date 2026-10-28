import pandas as pd
import pytest

from privacy.k_anonymity import anonymize_dataframe, verify_k_anonymity


def sample():
    return pd.DataFrame({
        "name": ["A", "B", "C", "D", "E", "F"],
        "age": [21, 22, 23, 44, 45, 46],
        "district": ["North", "North", "North", "South", "South", "South"],
        "condition": ["X", "Y", "X", "Z", "Z", "Y"],
    })


def test_generalization_produces_verified_k_anonymity_and_drops_direct_id():
    df = sample()
    out, report = anonymize_dataframe(df, ["age", "district"], k=2, direct_identifier_columns=["name"])
    assert "name" not in out.columns
    assert report["verified_k_anonymity"] is True
    assert report["minimum_equivalence_class_size"] >= 2
    assert verify_k_anonymity(out, ["age", "district"], 2)["verified_k_anonymity"] is True


def test_k_three_and_numeric_qi_generalization():
    df = pd.DataFrame({"person_id": list("ABCDEFGH"), "age": [21, 22, 23, 24, 42, 43, 44, 45],
                       "ward": ["A", "A", "A", "A", "B", "B", "B", "B"]})
    out, report = anonymize_dataframe(df, ["age", "ward"], k=3, direct_identifier_columns=["person_id"])
    assert report["minimum_equivalence_class_size"] >= 3
    assert report["verified_k_anonymity"]
    assert "person_id" not in out.columns


def test_requires_k_at_least_two():
    with pytest.raises(ValueError):
        anonymize_dataframe(sample(), ["age"], k=1)


def test_requires_at_least_k_rows():
    with pytest.raises(ValueError):
        anonymize_dataframe(sample().head(2), ["age"], k=3)


def test_requires_quasi_identifier():
    with pytest.raises(ValueError):
        anonymize_dataframe(sample(), [], k=2)


def test_direct_identifier_and_qi_cannot_overlap():
    with pytest.raises(ValueError):
        anonymize_dataframe(sample(), ["name", "age"], k=2, direct_identifier_columns=["name"])


def test_missing_values_can_be_generalized():
    df = pd.DataFrame({"id": ["1", "2", "3", "4"], "age": [None, 20, None, 20], "district": ["A", "A", "B", "B"]})
    out, report = anonymize_dataframe(df, ["age", "district"], k=2, direct_identifier_columns=["id"])
    assert report["verified_k_anonymity"]
    assert report["minimum_equivalence_class_size"] >= 2


def test_sensitive_attribute_is_not_silently_claimed_protected():
    df = sample()
    out, report = anonymize_dataframe(df, ["age", "district"], k=2, direct_identifier_columns=["name"])
    assert "condition" in out.columns
    assert "l-diversity" in report["warning"]
