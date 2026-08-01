# NIST AP242 test fixture

`nist_ctc_01_asme1_ap242-e1.stp` (396,445 bytes) is one file from the NIST MBE
PMI Validation and Conformance Test Suite, redistributed here unmodified.

- Source archive: https://www.nist.gov/system/files/documents/noindex/2024/06/19/NIST-PMI-STEP-Files.zip
  (reached from https://www.nist.gov/document/nist-pmi-step-files)
- Fetcher for the full suite: `scripts/fetch_nist_pmi.py`
- Terms: NIST states the test cases, CAD models and STEP files "can be used
  without any restrictions", and asks for acknowledgement.

## Why this one is committed when the rest of the suite is gitignored

The full ~14 MB suite stays out of git and is reproducible via the fetcher. This
single file is committed because it is the ONLY positive control the semantic-PMI
read path has on a fresh clone. Without it, every oracle assertion a fresh clone
runs is either a zero-count or a FileNotFoundError, and a `read_pmi_counts`
stubbed to return zeros would pass the entire suite. Design spec line 252 makes
"fresh clone, no licence, runs end-to-end" an explicit success criterion.

It is the smallest AP242 file in the suite carrying non-trivial PMI: 21
dimensions, 6 geometric tolerances, 11 datums.
