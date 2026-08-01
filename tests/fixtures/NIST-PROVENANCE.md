# NIST AP242 test fixture

`nist_ctc_01_asme1_ap242-e1.stp` is one file from the NIST MBE PMI Validation
and Conformance Test Suite, redistributed here unmodified.

- Size: 396,445 bytes
- SHA-256: `85a5752da05f53c456ca3a9e038c90358e1d5a3141d1f0d6e5f0970f2356e821`

Both are asserted by `assert_is_the_nist_original` in `tests/test_ap242_pmi.py`,
which runs with or without the `[gen]` extra. That matters: this repo has
`core.autocrlf=true`, and the first attempt to commit the fixture (d312ad6)
stored a CRLF->LF-normalised 391,739-byte blob instead. `.gitattributes` marks
`*.stp` binary to prevent that, but `.gitattributes` is last-match-wins and
nothing tests it directly, so the hash is what actually notices. The PMI reader
returns the same 21/6/11 counts from the mangled file, so the counts below
cannot detect corruption on their own.

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
