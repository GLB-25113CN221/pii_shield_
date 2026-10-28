"""Tabular k-anonymity through global generalization of selected quasi-identifiers.

This is a demonstrator for structured tables (CSV/DataFrame), not free-text documents.
It removes explicitly selected direct-identifier columns, generalizes selected QIs,
and checks that every equivalence class has at least k rows. It does not guarantee
l-diversity, t-closeness, differential privacy, or protection against all attacks.
"""
from __future__ import annotations

from typing import Any
import math
from collections import Counter
import pandas as pd

NUMERIC_WIDTHS = [5, 10, 20, 50, 100, 500]
DATE_LEVELS = 3  # exact day -> year -> decade -> wildcard
CATEGORICAL_LEVELS = 1  # exact category -> wildcard


def _kind(series: pd.Series) -> str:
    """Infer a conservative generalization family for a column."""
    nonnull = series.dropna()
    if nonnull.empty:
        return "categorical"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    sample = nonnull.astype(str).head(50)
    numeric_like = pd.to_numeric(sample.str.replace(",", "", regex=False), errors="coerce")
    if len(sample) and float(numeric_like.notna().mean()) >= 0.9:
        return "numeric"
    # Only treat strings as dates when most non-empty values look date-like.
    dateish = sample.str.contains(r"^\s*\d{4}[-/]\d{1,2}[-/]\d{1,2}\s*$|^\s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\s*$", regex=True)
    if len(sample) and float(dateish.mean()) >= 0.7:
        return "date"
    # Numeric-looking string columns are often identifiers, so keep as categorical.
    return "categorical"


def _max_level(kind: str) -> int:
    if kind == "numeric":
        return len(NUMERIC_WIDTHS) + 1  # exact, bins, then wildcard
    if kind == "date":
        return DATE_LEVELS
    return CATEGORICAL_LEVELS


def _generalize(series: pd.Series, kind: str, level: int) -> pd.Series:
    """Return display-safe generalized values while retaining row alignment."""
    if level <= 0:
        return series.map(lambda x: "<MISSING>" if pd.isna(x) else str(x))
    if kind == "categorical":
        return series.map(lambda x: "<MISSING>" if pd.isna(x) and level <= 0 else "*")
    if kind == "numeric":
        if level > len(NUMERIC_WIDTHS):
            return series.map(lambda x: "<MISSING>" if pd.isna(x) and level <= 0 else "*")
        width = NUMERIC_WIDTHS[level - 1]
        def num_bin(value: Any) -> str:
            if pd.isna(value):
                return "<MISSING>"
            try:
                number = float(value)
                low = math.floor(number / width) * width
                high = low + width - 1
                return f"{low:g}-{high:g}"
            except (TypeError, ValueError, OverflowError):
                return "*"
        return series.map(num_bin)
    # date levels: exact date -> year -> decade -> wildcard
    if level >= 3:
        return series.map(lambda x: "<MISSING>" if pd.isna(x) and level <= 0 else "*")
    parsed = pd.to_datetime(series, errors="coerce", dayfirst=True)
    def date_value(original: Any, dt: Any) -> str:
        if pd.isna(original):
            return "<MISSING>"
        if pd.isna(dt):
            return "*"
        if level == 1:
            return dt.strftime("%Y-%m-%d")
        if level == 2:
            return dt.strftime("%Y")
        return f"{(dt.year // 10) * 10}s"
    return pd.Series(
        [date_value(orig, dt) for orig, dt in zip(series.tolist(), parsed.tolist())],
        index=series.index, dtype="object"
    )


def _equivalence_sizes(qi_frame: pd.DataFrame) -> pd.Series:
    """Group size for each row's QI tuple, with missing values treated as a category."""
    if qi_frame.shape[1] == 0:
        return pd.Series([len(qi_frame)] * len(qi_frame), index=qi_frame.index, dtype="int64")
    keys = [tuple(row) for row in qi_frame.astype(str).itertuples(index=False, name=None)]
    counts = Counter(keys)
    return pd.Series([counts[key] for key in keys], index=qi_frame.index, dtype="int64")


def _violating_rows(qi_frame: pd.DataFrame, k: int) -> int:
    sizes = _equivalence_sizes(qi_frame)
    return int((sizes < k).sum())


def anonymize_dataframe(
    dataframe: pd.DataFrame,
    quasi_identifier_columns: list[str],
    k: int = 3,
    direct_identifier_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Generalize QIs until every retained row belongs to a group of size >= k.

    Direct identifier columns are dropped first. The algorithm greedily chooses
    the next one-column generalization that reduces violating rows, then reduces
    distinct combinations; it terminates because every QI has a wildcard level.
    """
    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("dataframe must be a pandas DataFrame")
    if not isinstance(k, int) or isinstance(k, bool) or k < 2:
        raise ValueError("k must be an integer of at least 2")
    if len(dataframe) < k:
        raise ValueError(f"Dataset has {len(dataframe)} rows; at least k={k} rows are required.")
    direct_identifier_columns = list(direct_identifier_columns or [])
    quasi_identifier_columns = list(dict.fromkeys(quasi_identifier_columns or []))
    all_cols = list(dataframe.columns)
    unknown = [c for c in direct_identifier_columns + quasi_identifier_columns if c not in all_cols]
    if unknown:
        raise ValueError(f"Unknown column(s): {unknown}")
    overlap = set(direct_identifier_columns) & set(quasi_identifier_columns)
    if overlap:
        raise ValueError(f"Columns cannot be both direct identifiers and quasi-identifiers: {sorted(overlap)}")
    if not quasi_identifier_columns:
        raise ValueError("Select at least one quasi-identifier column.")
    if set(dataframe.columns).issubset(set(direct_identifier_columns)):
        raise ValueError("Dropping direct identifiers would leave no columns.")

    working = dataframe.drop(columns=direct_identifier_columns).copy()
    qcols = [c for c in quasi_identifier_columns if c in working.columns]
    kinds = {c: _kind(working[c]) for c in qcols}
    levels = {c: 0 for c in qcols}

    def current_qi() -> pd.DataFrame:
        return pd.DataFrame(
            {c: _generalize(working[c], kinds[c], levels[c]) for c in qcols},
            index=working.index,
        )

    iterations = 0
    initial_violating = _violating_rows(current_qi(), k)
    # Greedy global recoding: advance one QI hierarchy at a time.
    while _violating_rows(current_qi(), k) > 0:
        candidates = []
        for col in qcols:
            if levels[col] >= _max_level(kinds[col]):
                continue
            levels[col] += 1
            candidate_frame = current_qi()
            violation_count = _violating_rows(candidate_frame, k)
            distinct_count = int(candidate_frame.drop_duplicates().shape[0])
            # Prefer fewer violating rows, then fewer equivalence classes, then
            # smaller total hierarchy depth; stable column order breaks ties.
            candidates.append(((violation_count, distinct_count, sum(levels.values())), col))
            levels[col] -= 1
        if not candidates:
            raise RuntimeError("Could not generalize selected quasi-identifiers to k-anonymity.")
        _, chosen = min(candidates, key=lambda item: item[0])
        levels[chosen] += 1
        iterations += 1
        if iterations > sum(_max_level(kinds[c]) for c in qcols):
            raise RuntimeError("Generalization exceeded its safe iteration bound.")

    generalized_qi = current_qi()
    # Replace QI columns in output with generalized values.
    output = working.copy()
    for col in qcols:
        output[col] = generalized_qi[col]

    sizes = _equivalence_sizes(generalized_qi)
    minimum_class_size = int(sizes.min()) if len(sizes) else 0
    verified = bool(minimum_class_size >= k)
    report = {
        "method": "global generalization of selected quasi-identifiers",
        "k": k,
        "input_rows": int(len(dataframe)),
        "output_rows": int(len(output)),
        "direct_identifier_columns_dropped": direct_identifier_columns,
        "quasi_identifier_columns": qcols,
        "generalization_levels": levels.copy(),
        "generalization_kinds": kinds,
        "initial_rows_in_classes_smaller_than_k": initial_violating,
        "generalization_iterations": iterations,
        "equivalence_classes": int(generalized_qi.drop_duplicates().shape[0]),
        "minimum_equivalence_class_size": minimum_class_size,
        "verified_k_anonymity": verified,
        "warning": (
            "This verifies k-anonymity only for the selected quasi-identifiers in this released table. "
            "It does not guarantee l-diversity, t-closeness, differential privacy, resistance to all "
            "linkage attacks, or protection from sensitive-attribute disclosure. Review columns, "
            "metadata, small datasets, external information, and intended release context."
        ),
    }
    if not verified:
        raise RuntimeError("Internal verification failed: output did not meet requested k.")
    return output, report


def verify_k_anonymity(dataframe: pd.DataFrame, quasi_identifier_columns: list[str], k: int) -> dict:
    """Verify a table against k-anonymity for selected QI columns."""
    if not isinstance(k, int) or isinstance(k, bool) or k < 2:
        raise ValueError("k must be an integer of at least 2")
    if not quasi_identifier_columns:
        raise ValueError("Select at least one quasi-identifier column.")
    missing = [c for c in quasi_identifier_columns if c not in dataframe.columns]
    if missing:
        raise ValueError(f"Unknown column(s): {missing}")
    sizes = _equivalence_sizes(dataframe[quasi_identifier_columns].copy())
    minimum = int(sizes.min()) if len(sizes) else 0
    return {
        "k": k,
        "rows": int(len(dataframe)),
        "equivalence_classes": int(dataframe[quasi_identifier_columns].astype(str).drop_duplicates().shape[0]),
        "minimum_equivalence_class_size": minimum,
        "verified_k_anonymity": bool(len(dataframe) > 0 and minimum >= k),
    }
