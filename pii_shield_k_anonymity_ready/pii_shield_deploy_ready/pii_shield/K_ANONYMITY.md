# Tabular k-anonymity in PII Shield India

## What this feature does

The K-Anonymity tab accepts a CSV table. The user selects:

1. **Direct identifiers to remove** (for example, name, email, phone, account number, or a person-specific ID).
2. **Quasi-identifiers (QIs)** that may identify a person in combination (for example, age, district, ward, occupation, or date).
3. A target integer `k >= 2`.
4. Optional extra columns to exclude because they are not needed for the release.

The code generalizes the selected QI columns until each distinct QI combination occurs in at least `k` rows. The released table is checked again, and the report includes the minimum equivalence-class size and generalization levels.

## Definition

A table is k-anonymous with respect to a chosen set of quasi-identifiers when every row's QI combination is shared by at least `k` rows in the released table. Rows with the same selected QI values form an equivalence class.

This property is conditional on the chosen QIs and the released dataset. If an important quasi-identifier is omitted, the result can be k-anonymous for the selected columns but still be vulnerable in context.

## Generalization strategy

The current implementation uses global recoding:
- Numeric QIs: exact values, then fixed-width ranges (5, 10, 20, 50, 100, 500), then `*`.
- Date-like QIs: exact day, year, decade, then `*`.
- Categorical QIs: exact value, then `*`.
- Missing values become a generalized wildcard when a column is generalized.

A greedy process advances one QI hierarchy at a time, preferring transformations that reduce the number of rows in equivalence classes smaller than `k`, then reduce the number of distinct QI combinations. It stops when verification passes. This is a simple prototype algorithm, not an optimal minimum-distortion anonymizer.

## What it does not guarantee

- It does not automatically detect which columns are QIs; the user must select them thoughtfully.
- It does not automatically remove every direct identifier unless those columns are selected for removal.
- It does not prove l-diversity, t-closeness, differential privacy, or protection from every linkage attack.
- It does not protect against sensitive-attribute disclosure. For example, if every person in a QI group has the same diagnosis, k-anonymity alone does not hide that diagnosis.
- It does not inspect arbitrary document metadata or transform free text/PDF/image/DOCX into a k-anonymous table.
- It does not account for all external datasets an attacker might possess.
- Generalization may make the released data less useful. Always review both privacy and utility.

## Recommended validation before a real release

1. Define the threat model and intended recipient.
2. Identify direct identifiers, quasi-identifiers, sensitive attributes, and columns not needed.
3. Use authorised/synthetic test data first.
4. Try more than one `k` value and inspect how much generalization occurs.
5. Independently verify that the minimum equivalence-class size is at least `k`.
6. Evaluate whether sensitive attributes are homogeneous within groups; consider l-diversity or t-closeness where relevant.
7. Review rare categories, missing values, metadata, free-text columns, and possible external joins.
8. Have a privacy/security reviewer approve the release.

## Tests

`tests/test_k_anonymity.py` checks the basic transformation, direct-identifier removal, `k` validation, missing values, and post-transformation verification. Passing these tests shows the implementation behaves as expected for those test cases; it is not a formal privacy proof or a real-world risk evaluation.
