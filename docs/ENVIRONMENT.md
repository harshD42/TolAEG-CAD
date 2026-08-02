# Environment: bare machine to green suite

**Everything below was measured on 2026-08-01 at commit `30eb333` (branch `main`), on the
development laptop (Windows 11 Home 26200), unless a line says `UNVERIFIED`.**

Canonical values for contested research quantities live in
`docs/superpowers/specs/2026-08-01-ledger-reconciliation.md`. This document does not restate
them; it tells you how to reproduce the environment they were measured in.

**Verified end state:** `pytest` → 428 passed, exit 0. `python scripts/gate_a.py` → 7 PASS
(5 measured, 2 attested) / 0 FAIL / 3 SKIP, **exit 1**. CI reported green on `ubuntu-latest` and
`windows-latest` (`UNVERIFIED` from this machine — the `gh` CLI is not installed here; confirm
with `gh run list --limit 5`).

---

## 1. Verified toolchain

Measured with `python --version` and `importlib.metadata.version()` against the ambient
interpreter this repo actually runs on.

| Package | Version here | Declared in `pyproject.toml` | Load-bearing? |
|---|---|---|---|
| CPython | **3.13.14** | `requires-python = ">=3.11"` | Partly — see below |
| pip | 26.0.1 | — | No |
| **numpy** | **2.4.1** | `numpy==2.4.1` (exact) | **YES — see §1.1** |
| pytest | 9.0.2 ambient / **9.1.1** on a fresh install today | `pytest>=8.0` | No |
| pytest-cov | 7.1.0 | `pytest-cov>=5.0` | No |
| coverage | 7.15.2 | (transitive) | No |
| cosmic-ray | 8.4.6 | `cosmic-ray>=8.3` | **YES — Layer 2 refuses to skip** |
| cadquery | 2.8.0 | `cadquery>=2.8` (`[gen]`) | Optional; 31 tests gate on it |
| **OCP** | provided by **`cadquery-ocp` 7.9.3.1.1** | transitive via cadquery | Optional |
| scipy | 1.17.0 | transitive via cadquery | No — nothing in this repo imports it |
| numba | 0.66.0 | transitive via cadquery | No, but see §1.2 |
| pypdf | 6.14.2 | **not declared anywhere** | Needed only by `scripts/verify_literature.py` |

There is **no distribution named `OCP`**. `pip show OCP` prints
`WARNING: Package(s) not found: OCP`; the importable `OCP` module ships inside the `cadquery-ocp`
wheel. Code that must know whether the extra is present asks
`importlib.util.find_spec("OCP")` (see `tests/test_ap242_pmi.py:20`, and the comment there
explaining why a bare `except ImportError` was wrong).

Python 3.13 is what CI pins (`.github/workflows/ci.yml`, `python-version: "3.13"`) and what every
recorded measurement used. `pyproject.toml` allows ≥3.11, but **no measurement in this repo was
ever taken on 3.11 or 3.12** — treat those as UNVERIFIED (confirmed by adding them to the CI
matrix and getting 428 passed).

### 1.1 Why numpy is pinned exactly at 2.4.1

The pre-registered Tier 1 difficulty ladder and the corpus SHA-256 digest are produced by
`scripts/measure_ladder.py`, which draws from `numpy.random.Generator` through
`tolcad.gen.sampler.sample_assembly`. **NEP 19 guarantees bit-stream stability only for the legacy
`RandomState`, not for `Generator`.** A numpy upgrade may therefore silently change every ladder
count and the digest, invalidating a number the paper pre-registers.

The project's response (decision D-C) was to pin numpy exactly rather than switch to
`RandomState`. `tests/gen/test_ladder_pin.py` is the executable guard: it asserts all four
`(failures, total)` pairs and the digest exactly, and its failure message prints the running
`numpy.__version__` so the first thing you see on a version bump is the cause.

**Do not relax `numpy==2.4.1` to a range.** If numpy must move, all four ladder levels and the
digest must be re-measured together and re-pinned, and the pre-registration re-issued.

### 1.2 Latent dependency trap: numba caps numpy at `<2.5`

`cadquery` pulls in `numba`, and the installed `numba 0.66.0` declares `numpy<2.5,>=1.22`. Our
exact pin `numpy==2.4.1` sits one minor release below that ceiling. Today the resolver satisfies
both. The moment a future `cadquery` requires a `numba` that needs `numpy>=2.5`,
`pip install -e ".[dev,gen]"` becomes **unresolvable** while the numpy pin stands, and the pin is
the one thing that must not move. If that happens, install `[dev]` only (the core suite is 397
tests without `[gen]`, see §2.5) and containerize the `[gen]` path rather than loosening the pin.

---

## 2. Setup from scratch

The repo currently has **no `.venv`**; the ambient interpreter has `tolcad` installed editable
(`pip install -e .` into the Windows Store Python user site-packages). That is a historical
accident, not a recommendation. Use a venv.

### 2.1 Linux (RHEL / Ubuntu)

```bash
git clone https://github.com/harshD42/TolAEG-CAD.git tolcad
cd tolcad
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,gen]"
python -m pytest -q          # expect: 426 passed, 2 skipped
```

`.venv/` is gitignored.

### 2.2 Windows 11

```powershell
git clone https://github.com/harshD42/TolAEG-CAD.git tolcad
cd tolcad
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,gen]"
python -m pytest -q          # expect: 426 passed, 2 skipped
```

Windows notes, all measured:

- **Measured install time: 112 s** for `pip install -e ".[dev,gen]"` into a bare venv with a warm
  pip cache. Almost all of it is `cadquery-ocp` (≈94 MB of `OCP` alone on disk) plus `vtk`,
  `numba`, `casadi` and the `trame` stack. Cold, expect several minutes.
- **Measured venv size on disk: 1.2 GB with `[dev,gen]`, 120 MB with `[dev]` only.** Budget the
  disk before cloning onto a small drive, especially alongside the 1.17 GB literature corpus.
- The **Windows Store Python** (`%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe`) works — it is
  what every number in this document was measured on — but it installs packages under
  `%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python.3.13_*\LocalCache\local-packages`,
  which is easy to mistake for a broken install. A normal python.org install or a venv avoids the
  confusion.
- Several tests shell out to **`git`**, so `git` must be on `PATH` for `pytest`, not just in your
  shell profile (`tests/conftest.py`, `tests/test_gitattributes_clone.py`,
  `tests/test_tree_cleanliness.py`).
- `scripts/fetch_literature.sh` is **bash + curl**. Git for Windows supplies both
  (`/usr/bin/bash`, `/mingw64/bin/curl`); run it from Git Bash, not PowerShell.

### 2.3 Payload 1 — NIST PMI conformance suite (gitignored)

```
python scripts/fetch_nist_pmi.py
```

- Downloads `NIST-PMI-STEP-Files.zip` from nist.gov. **Measured: 13,976,599 bytes (14.0 MB)** —
  that is the *archive*. Extracted, `data/nist_pmi/` holds **33 `.stp` files, 54.3 MB**, and
  **68.3 MB total** with the archive left in place.
- `data/nist_pmi/` is gitignored in full (`.gitignore`, and `tests/test_fetch_nist.py:24` asserts
  the ignore rule is still there).
- Exit 0 on success. **Exits 1 with a `WARNING:` on stderr if it does not find exactly 17 AP242
  files** — that branch means the upstream archive changed and the files must not be trusted as
  an oracle. It is a real non-zero path, not a crash.
- NIST states the files "can be used without any restrictions" and asks for acknowledgement. This
  is why Gate A needs no commercial CAD licence.

**Tests that skip without it: exactly two**, both in `tests/test_ap242_pmi.py`:
`test_reads_semantic_pmi_from_nist_ftc06` (line 89) and
`test_the_fixture_and_the_fetched_suite_disagree_about_counts` (line 134), both reporting
`NIST suite not fetched; run scripts/fetch_nist_pmi.py`.

### 2.4 Payload 2 — literature corpus (gitignored)

```
bash scripts/fetch_literature.sh
python scripts/verify_literature.py        # requires pypdf, which pyproject does NOT declare
```

- **Measured on disk: 111 PDFs, 1,165,927,667 bytes ≈ 1.17 GB.** `papers/literature/INDEX.md`
  says "~1 GB" and is right; **`.gitignore`'s "~617MB" comment is stale** and so is
  `papers/literature/_fetch_log.txt`, whose last line still reads `downloaded=69 failed=0
  total=69` from an earlier, smaller corpus. The fetch script currently declares **111** arXiv
  IDs. Both stale artifacts are tracked; neither is asserted by any test.
- Tracked: `papers/literature/INDEX.md` and `papers/literature/_fetch_log.txt`. Ignored:
  `papers/literature/*.pdf`.
- **No test reads `papers/` at all.** Grep confirms: the only references are inside
  `scripts/verify_literature.py`. The corpus is a citation-hygiene artifact, not a test input.
  **A missing literature corpus causes zero skips.**
- `verify_literature.py` imports `pypdf`, which is in no dependency list. `pip install pypdf`
  before running it.

### 2.5 What a correct data-less run looks like

Measured by actually cloning `main` into a scratch directory (`git clone --no-local`) — a fresh
clone contains **no `data/` directory at all** and no PDFs:

| Install | Result | Time |
|---|---|---|
| `pip install -e ".[dev,gen]"` | **426 passed, 2 skipped**, exit 0 | 66.4 s |
| `pip install -e ".[dev]"` (no gen) | **397 passed, 7 skipped**, exit 0 | 44.8 s |
| Fully provisioned (this machine) | **428 passed, 0 skipped**, exit 0 | 78.6 s |

Without `[gen]`, three whole files are skipped at module level by
`pytest.importorskip("cadquery")` (`tests/gen/test_build.py`, `test_end_to_end.py`,
`test_export.py` — 27 tests collapse into 3 skip lines) plus 4 `needs_ocp` tests in
`tests/test_ap242_pmi.py`.

**A data-less clone must not be all-skips, and it is not.** `tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp`
(396,445 bytes) is committed precisely so the semantic-PMI read path has a positive control on a
fresh clone. Two tests exercise it:

- `test_the_committed_fixture_is_byte_identical_to_the_nist_original` — runs **always**, with or
  without `[gen]`, because it is a claim about the repo, not the CAD toolkit.
- `test_reads_nonzero_pmi_from_the_committed_fixture` — runs on a data-less clone **as long as
  `[gen]` is installed**, and asserts exact counts 21 dimensions / 6 geotols / 11 datums.

Without that fixture a `read_pmi_counts` stubbed to return zeros would pass the entire suite. See
`tests/fixtures/NIST-PROVENANCE.md`.

---

## 3. How to run everything

Runtimes are wall-clock on the development laptop; a workstation will be faster.

| Command | Time | Exit | Expected output |
|---|---|---|---|
| `pytest` | **78.6 s** | **0** | `428 passed` |
| `pytest -m "not slow"` | **67.2 s** | **0** | `426 passed, 2 deselected` |
| `python scripts/gate_a.py` | **2.7 s** | **1 — and that is correct** | 10-row table, `7 PASS (5 measured, 2 attested), 0 FAIL, 3 SKIP`, `Gate A: NOT CLEARED` |
| `python scripts/measure_ladder.py` | **0.3 s** | **0** | four `dN: f/t = p% fail` lines, the corpus digest, the recipe JSON |
| `python scripts/check_suite_integrity.py` | **15 min measured** (the workflow comment says ~25) | **1 — and that is correct today** | see §3.1 |

### 3.1 `check_suite_integrity.py`, reproduced

Run end-to-end at `30eb333` in an isolated clone (§4.2), 21:37 → 21:52, **15 min**:

```
Core branch coverage: 94.74 within 0.50 of 94.74
Mutation score: 100.00 is ABOVE the pin 95.89 by 4.11 -- the tree improved and the pin has
detached. Re-pin it and record why.
Suite integrity - tests that cannot fail (non-blocking for Gate A)

  Core branch coverage               PASS   94.74% (pin 94.74% +/- 0.50)
  Mutation score                     FAIL   100.00% (pin 95.89% +/- 0.50)

Suite integrity: FAILED (Mutation score)
```

Exit **1**. Both numbers reproduce the canonical values in the ledger reconciliation exactly. The
clone's `git status --short` was **empty** afterwards — on a normal exit cosmic-ray's restore is
byte-exact, as its docstring claims. The 15-minute figure is a fast laptop with the run isolated;
budget the workflow's ~25 min for a CI runner.

### 3.2 `pytest -m "not slow"` buys almost nothing

Only **two** tests carry `@pytest.mark.slow`, both in `tests/test_convergence.py`. The marker
saves ~11 s of a 79 s run. The suite is slow because `tests/test_declared_mutations.py` spawns a
fresh `pytest` subprocess per registry entry (15 entries × 2 runs each), not because of Monte
Carlo.

### 3.3 The two commands that legitimately exit non-zero

**Do not "fix" these.** Both are correct, current, recorded states.

- **`scripts/gate_a.py` exits 1.** Gate A returns 0 only when *every* criterion passes, and
  `main()` is explicit that "a skipped criterion is not a pass". Three rows SKIP: `NIST PMI
  conformance` and `TolAnalyst agreement` have no export CSV at `data/nist_pmi_expected.csv` /
  `data/tolanalyst_verdicts.csv` (Phase 3 work, not a defect), and `Fresh clone pipeline` is
  deliberately not self-certifiable from inside a configured checkout. Exit 1 here means
  *"NOT CLEARED"*, not *"broken"*.
- **`scripts/check_suite_integrity.py` exits 1** on the mutation pin. `MUTATION_MEASURED = 95.89`
  with a **two-sided** ±0.50 tolerance; the last measurement came in at 100.00%, which is
  *above* the pin, and the two-sided check fires on improvement as well as regression:
  `"the tree improved and the pin has detached. Re-pin it and record why."` The ledger
  reconciliation is explicit — **DO NOT RE-PIN**; resolution is scheduled work (P1.5). A
  one-sided floor would have stayed silently green, so the failure *is* the control working.

Exit codes for both scripts: `0` = cleared/OK, `1` = a criterion or pin failed, **`2` = refused to
run** (see §4.1). Three distinct meanings; do not collapse them.

### 3.4 Environment differences that change the numbers

`428 passed` assumes `[dev,gen]` **and** a fetched NIST suite. See the table in §2.5 for the other
two legitimate shapes.

---

## 4. The traps

This section is the reason this document exists.

### 4.1 The mutation lock, and exit 2

`pytest` **transiently rewrites tracked files under `src/` and `tests/`** and restores them.
`tests/mutation_registry.py` holds **15 declared mutations** whose targets are:

| Count | Target |
|---|---|
| 3 | `src/tolcad/gen/features.py` |
| 3 | `src/tolcad/gen/sampler.py` |
| 2 | `src/tolcad/iso286.py` |
| 2 | `src/tolcad/reliability.py` |
| 1 | `src/tolcad/gen/layout.py` |
| 1 | `src/tolcad/y14_5.py` |
| 1 | `tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp` (binary) |
| 1 | `tests/gen/test_features.py` |
| 1 | `tests/gen/test_layout.py` |

> **`CLAUDE.md`'s list is incomplete.** It names `src/tolcad/{iso286,reliability}.py`,
> `src/tolcad/gen/{sampler,layout,features}.py` and "one tracked fixture". It **omits
> `src/tolcad/y14_5.py` and the two files under `tests/gen/`**. The table above is generated from
> `tests.mutation_registry.REGISTRY` and is the truth.

`run_declared_mutation` opens `mutation_lock()` **before** the mutating write and closes it only
**after** the restore has been verified byte-identical, so there is no window where a file on
disk is mutated and the lock is not held. The lock is the file `.mutation-in-progress` at the
repo root (gitignored — a tracked lock would dirty the tree on every run and trip §4.4).

`scripts/gate_a.py` and `scripts/check_suite_integrity.py` each check for it first thing in
`main()` and **exit 2** rather than measure a mutated checker. Verified by execution; this is the
exact message (`gate_a.py`; the integrity script differs only in the third line):

```
REFUSING TO RUN: a declared mutation is in progress.
  lock:    <repo>\.mutation-in-progress
  held by: declared mutation in progress; pid=12345; started=2026-08-01T21:00:00
  This reader loads the checker core from disk in fresh interpreters and would measure a MUTATED
  checker, reporting a genuine number for the wrong instrument.
  If pytest is running in another window, wait for it to finish -- the lock clears itself.
  IF NOTHING IS RUNNING, THE LOCK IS STALE (a run was killed mid-mutation). Recover in this order:
    1. git status --short src/ tests/fixtures/
    2. anything modified there that you did not edit is a leftover mutant: git checkout -- src/ tests/fixtures/
    3. delete <repo>\.mutation-in-progress
    4. re-run.
```

`check_suite_integrity.py`'s third line instead reads: *"This reader loads the checker core from
disk in fresh interpreters **and mutates it itself**, so running now would both measure a MUTATED
checker and race another writer for the restore."*

**Stale-lock recovery, verbatim from the message, in order:**

1. `git status --short src/ tests/fixtures/`
2. Anything modified there that you did not edit is a leftover mutant:
   `git checkout -- src/ tests/fixtures/` (this discards *all* uncommitted work under those paths
   — check first if you have real edits to preserve)
3. Delete `.mutation-in-progress`
4. Re-run.

Crash-safety is deliberately **not** claimed: a SIGKILL between the write and the unlink leaves
the lock behind exactly as it leaves a mutated `src/` file behind. A killed run produces no
verdict, so this is not a silent false green — it is an expected state with a stated recovery.

The lock file's contents are diagnostic only (`pid=`, `started=`), so a lock you find can tell you
which process took it and when.

### 4.2 Never run `pytest` concurrently with anything that reads `src/tolcad/`

Stated in `CLAUDE.md` and enforced by §4.1, but the enforcement is one-directional: the *scripts*
refuse while `pytest` holds the lock. Nothing stops a second `pytest`, an editor's test runner, a
code-review pass, or another agent from **reading** a mutated file mid-run. Two writers are worse
still — `cosmic-ray` also mutates `src/tolcad/` in place, and `check_suite_integrity.py`'s
docstring records the accident that motivated the guard: an implementer started it alongside
`pytest`, killed it, and found `src/tolcad/y14_5.py` left mutated.

Directly observed while writing this document: with `check_suite_integrity.py` running in an
isolated clone, `git status --short` in that clone showed `M src/tolcad/iso286.py` — a live
cosmic-ray mutant sitting on disk mid-run. Nothing was broken; that is simply what the tree looks
like for the seconds each mutant's test command executes.

Practical rule: **one process at a time touches this repo.** If you must run something in
parallel, `git clone --no-local` to a scratch directory and run there — the lock, the mutations
and `tests/conftest.py`'s check are all repo-root-relative, so a clone is fully isolated. (Every
"fresh clone" number in §2.5, and the integrity measurement in §3, was produced that way while the
main tree sat untouched.)

### 4.3 CRLF — the corruption is a *commit*-time event

`core.autocrlf` on this machine is **`true`**, and it comes from Git for Windows' *system*
config (`C:/Program Files/Git/etc/gitconfig`), not from the repo or the user config. On Linux the
default is effectively `false`. Verified with `git config --show-origin --get-all core.autocrlf`.

The historically damaging event was a **`git add` / commit**: with `autocrlf=true` and no
`.gitattributes` protection, git's CRLF→LF *clean* filter stored a 391,739-byte blob in place of
the 396,445-byte NIST original (commit `d312ad6`, fixed in `7ba4e87`). The PMI reader returns
**identical** counts (21/6/11) from the mangled copy, so the positive control passed against the
exact corruption it existed to detect. Only size and hash notice.

**Counter-intuitively, `autocrlf=true` *hides* an already-corrupted blob.** Cloning a
CRLF-stripped commit under `autocrlf=false` or `input` reproduces the 391,739 corrupted bytes;
under `autocrlf=true`, checkout re-inserts a CR before every bare LF and silently reconstructs
396,445 bytes, byte- and hash-identical. That is a false-negative heal, not a detector — which is
why `.github/workflows/ci.yml` deliberately does **not** force `autocrlf=true` on the Windows leg,
and the long comment at the top of that file records the measurement. The actual detector is
`tests/test_gitattributes_clone.py`, which runs its own nested
`git -c core.autocrlf={true,input,false} clone --no-local` and checks size + SHA-256 in all three
cases, independent of the runner's ambient config.

**`core.ignorecase`** is `true` in `.git/config` here (Windows/macOS default). It makes
`.gitattributes` glob matching **case-insensitive**, so `*.STP binary` alone already covers
`nist_..._ap242-e1.stp`. Verified in an isolated throwaway repo whose only rule is `*.STP binary`:

```
$ git -c core.ignorecase=true  check-attr binary -- foo.stp
foo.stp: binary: set
$ git -c core.ignorecase=false check-attr binary -- foo.stp
foo.stp: binary: unspecified
```

Same rule, same filename, opposite answers. `core.ignorecase` decides it.

Consequence, and it bites: `.gitattributes`'s own comment — *"gitattributes patterns are
case-sensitive"* — is true only of git's matching engine on a case-sensitive config
(`core.ignorecase=false`, e.g. most Linux CI runners), **not universally**. Commenting out just
the lowercase `*.stp binary` line to demonstrate the failure mode does nothing on Windows;
`*.STP` still matches. All four lines must be disabled to reproduce it. Recorded in
`.superpowers/sdd/2026-08-01-closeout/task-7-report.md`.

`.gitattributes` is **last-match-wins**: appending `* text=auto` would silently re-arm the whole
bug.

### 4.4 `tests/conftest.py` fails the run if the tree is left dirty

A session-scoped autouse finalizer runs `git status --porcelain src/ tests/fixtures/` after the
last test and fails the run if anything is modified:

```
THE SUITE LEFT TRACKED FILES MODIFIED. A declared mutation did not restore.
Recover with `git checkout -- src/ tests/fixtures/` and check
mutation_registry.run_declared_mutation.
```

**What it means:** a declared mutation wrote a mutant and did not restore it. On Windows this has
a known cause — `_write_bytes_resiliently` in `tests/mutation_registry.py` documents an observed
`OSError: [Errno 22] Invalid argument` on the *restore* write, reproducing roughly once in a dozen
runs, most likely a virus scanner or write-back still holding the just-written file. The write is
now retried 5 times with backoff; a persistent failure raises a named `AssertionError` telling you
which file is left mutated.

**Recovery:** `git checkout -- src/ tests/fixtures/`, delete `.mutation-in-progress` if present,
re-run. Note the scope: it only watches `src/` and `tests/fixtures/`, so a mutant left in
`tests/gen/test_layout.py` or `tests/gen/test_features.py` (both are registry targets, §4.1) would
**not** be caught by this finalizer.

**The false positive, and it is easy to hit.** The finalizer cannot distinguish a leftover mutant
from *any other uncommitted change* under those two paths. It runs `git status --porcelain`, not a
comparison against the pre-run state. So:

> **Editing `tests/fixtures/NIST-PROVENANCE.md` — a plain Markdown provenance note — and then
> running `pytest` fails the entire run** with "A declared mutation did not restore", which is
> false. The same happens for any work-in-progress edit under `src/`.

Observed live while writing this document: parallel work left `tests/fixtures/NIST-PROVENANCE.md`
modified in the working tree. Commit or stash edits under `src/` and `tests/fixtures/` before
running the suite. The failure message names a cause that may not be your cause — check
`git status --short src/ tests/fixtures/` and ask whether *you* made the change before reaching
for `git checkout --`, which would destroy it.

**What it structurally cannot see:** corruption that existed only *during* the run. The tree is
clean afterwards. That blind spot is exactly why the mutation lock exists.

### 4.5 cosmic-ray takes tens of minutes and is off the push path

The workflow budgets ~25 min; measured here it was **15 min** (§3.1). Either way it is far too
slow for a push gate, and it is not one.

Confirmed against `.github/workflows/ci.yml`: the `integrity` job is gated
`if: github.event_name == 'workflow_dispatch' || github.event_name == 'schedule'`, and the only
schedule is `cron: "0 6 * * 1"` — weekly, Monday 06:00 UTC. It never runs on push or PR. The
file's own comment states the reason: *a gate people route around is worse than no gate*.

`scripts/check_suite_integrity.py` runs `cosmic-ray init` / `exec` / `cr-report` once per core
module across six modules (`types`, `y14_5`, `iso286`, `montecarlo`, `checker`, `reliability`),
scoring `killed / (total - incompetent)` aggregated across all six. INCOMPETENT mutants (e.g.
`RemoveDecorator` on a dataclass) cannot execute at all and are excluded from the denominator.

`cosmic-ray.toml`'s `test-command` is the **whole six-module core subset**, not the one matching
file. Scoping it per-file was spiked and measured 12 survivors of 66 on `types.py` (18.2%) against
5 of 66 (7.58%) for the full subset, because `checker.py` and `y14_5.py` tests exercise
`types.py` heavily. A per-file command measures nothing useful.

If `cosmic-ray` is missing, the layer **raises**, it does not skip:
`"cosmic-ray is not installed; install the [dev] extra. This layer does not skip."`

### 4.6 mutmut does not work here

`mutmut` 3.7.0 **refuses to run natively on Windows** — it exits with a message directing you to
WSL. That is why this project uses cosmic-ray, which installs, imports and exposes a working CLI
natively. Recorded in `docs/superpowers/specs/2026-08-01-suite-integrity-design.md:34` and
`docs/superpowers/plans/2026-08-01-suite-integrity.md:15`. Not re-verified in this session (mutmut is
not installed); confirm with `pip install mutmut==3.7.0 && mutmut run` on Windows.

### 4.7 Stale statements in tracked files

- `.github/workflows/ci.yml`'s header comment says the suite is *"currently 402 tests"*. It is
  **428**. Comment only; the job asserts nothing about the count.
- `docs/superpowers/specs/2026-08-01-ledger-reconciliation.md` §3 states
  `.superpowers/sdd/.gitignore` contains a single `*`, so every SDD ledger is untracked. That
  ignore file now contains **`*.diff`** plus a note reversing the blanket ignore, and the ledgers
  are being brought under tracking (§7 below). §2 of that same file previously called the registry
  size "14 entries, uncontested"; it now carries an amendment recording the correct value, **15**.
  Measure it, do not read it: `len(tests.mutation_registry.REGISTRY)`.

---

## 5. Hardware

### 5.1 Deployment targets — the two workstations

- **RHEL workstation** — Intel Xeon 56-core, **4× RTX A6000 Ada, 48 GB per card (192 GB total)**,
  compute capability **sm_89**. Primary training box (`torchrun`); fewer driver/NCCL problems than
  the Windows box.
- **Windows 11 + WSL2 workstation** — identical hardware, Docker under WSL2. Ablation farm: 4
  concurrent single-GPU configs.

These are **the baseline-model deployment targets**. Neither machine is reachable from this
laptop; the two are not networked beyond a shared LAN, and ablations are embarrassingly parallel,
so results are synced manually. `UNVERIFIED from this machine` — nothing in this session could
query them. Confirm with `nvidia-smi --query-gpu=name,compute_cap,memory.total --format=csv` on
each box.

### 5.2 Development laptop — this machine

Measured with `nvidia-smi --query-gpu=name,compute_cap,memory.total,driver_version --format=csv`:

```
NVIDIA GeForce RTX 5060 Laptop GPU, 12.0, 8151 MiB, 596.36
```

- **RTX 5060 Laptop (Blackwell), compute capability 12.0 → `sm_120`**, 8 GB VRAM, driver
  **596.36**.
- `nvidia-smi` reports **CUDA Version: 13.2** — that is the maximum CUDA *runtime* the driver can
  host, **not** an installed toolkit, and not a statement about what any wheel was built against.
  Notes elsewhere describing this laptop as "CUDA 12.x" are out of date on this point.
- **Docker Desktop is installed but the daemon is not running.** `docker info` returns
  `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`. CLI version
  29.2.1, context `desktop-linux`.
- `wsl -l -v` → `Ubuntu-22.04` (v2, **Stopped**) and `docker-desktop` (v2, **Stopped**).
- **PyTorch is not installed on this machine at all.**

### 5.3 The consequence, stated plainly

**Blackwell `sm_120` needs CUDA 12.8+ and PyTorch 2.7+ — strictly newer than Ada `sm_89` requires
(supported since CUDA 11.8). A GPU result obtained on this laptop is therefore not evidence about
the workstations.** Different SASS target, different toolkit, different kernel-selection paths,
and 8 GB against 48 GB. The laptop is a **CPU-only build-and-contract bench**: write the code,
run the suite, pin the container contract, ship the job to a workstation.

The specific version floors (CUDA 12.8, PyTorch 2.7) are `UNVERIFIED` here — no torch install
exists to interrogate. Confirm with `python -c "import torch; print(torch.version.cuda,
torch.cuda.get_arch_list())"` and check that `sm_120` appears in the arch list.

Container strategy, GPU base images and the workstation deployment contract are specified
separately in **`docs/superpowers/plans/2026-08-02-baseline-containerization.md`** — a `harness/`
package, one-directional like `validation/`, with the CUDA/PyTorch selection resolved per model
from a single build matrix. That is where the `sm_89` vs `sm_120` split must be pinned; it is
deliberately not pinned here.

---

## 6. CI

`.github/workflows/ci.yml` is the only workflow. Two jobs, deliberately on different paths.

**Triggers:** `push` to `main`, any `pull_request`, `workflow_dispatch`, and
`schedule: cron "0 6 * * 1"` (weekly, Monday 06:00 UTC).

| Job | Runs when | Matrix | Steps |
|---|---|---|---|
| `suite` | `push` or `pull_request` only | `ubuntu-latest`, `windows-latest`; `fail-fast: false`; Python 3.13 | `actions/checkout@v4` → `actions/setup-python@v5` → `pip install -e ".[dev,gen]"` → `python -m pytest -q` |
| `integrity` | `workflow_dispatch` or `schedule` only | `ubuntu-latest`, Python 3.13 | same install → `python scripts/check_suite_integrity.py` (~25 min) |

Because the jobs are mutually exclusive on `github.event_name`, **the weekly cron runs `integrity`
only — it does not re-run the suite**, and a manual dispatch likewise runs `integrity` only.

**What CI proves that a local run cannot:** the code path already passes from an ambient,
already-provisioned local interpreter. A local clone reuses that interpreter, so it cannot prove
the package installs from nothing. CI's real contribution is that `pip install -e ".[dev,gen]"`
succeeds on a bare Linux *and* a bare Windows runner with no leftover state.

**What CI deliberately does not run:**

- No `autocrlf` override on the Windows checkout — see §4.3; forcing it would *hide* the bug, and
  `tests/test_gitattributes_clone.py` already parametrizes all three settings internally.
- No mutation testing on push (§4.5).
- No lint, no type-check, no coverage gate as separate jobs.
- No `scripts/gate_a.py` step — Gate A exits 1 today by design (§3.3) and would red the build.
- Only Python 3.13, despite `requires-python = ">=3.11"`.
- No macOS runner.
- No fetch of either gitignored payload, so CI's suite result is the data-less shape:
  **426 passed, 2 skipped**.

---

## 7. Git hygiene

**Ignored, and why** (`.gitignore`, 15 rules — `.coverage` appears twice):

| Pattern | Reason |
|---|---|
| `__pycache__/`, `*.py[cod]`, `*.egg-info/`, `build/`, `dist/`, `.venv/` | Standard build/venv noise |
| `.pytest_cache/`, `.coverage`, `htmlcov/`, `*.sqlite`, `results/` | Regenerable measurement artifacts (`*.sqlite` = cosmic-ray sessions) |
| `papers/literature/*.pdf` | ~1.17 GB; reproducible via `scripts/fetch_literature.sh`. **The index and fetch log are tracked**, so the corpus stays auditable |
| `data/nist_pmi/` | ~14 MB archive / 68 MB extracted; reproducible via `scripts/fetch_nist_pmi.py` |
| `.mutation-in-progress` | Runtime lock (§4.1). Tracking it would dirty the tree on every mutation run and trip the §4.4 finalizer |

**Nested ignore:** `.superpowers/sdd/.gitignore` contains `*.diff` — review diffs are regenerable
from history (`git diff <a>..<b>`), ~720 KB of redundancy. Its comment records that **everything
else under `.superpowers/sdd/` IS tracked as of 2026-08-01, reversing an earlier blanket `*`.**
This is the reversal that `2026-08-01-ledger-reconciliation.md` §3 has not caught up with (§4.7).

**What a fresh clone gets** — measured by cloning `main` at `30eb333` into a scratch directory:

- Gets: `src/`, `tests/` (including the 396,445-byte AP242 fixture), `scripts/`, `validation/`,
  `docs/`, `papers/literature/{INDEX.md,_fetch_log.txt}`, `pyproject.toml`, `cosmic-ray.toml`,
  `CLAUDE.md`, `.gitattributes`, `.github/`, and the tracked parts of `.superpowers/`.
- **Does not get: any `data/` directory at all** (it exists only once you run the fetcher), and no
  PDFs.
- Total: ~2.0 MB.

**`validation/` is optional and one-directional.** It sits outside the installed package at the
repo root; `pytest`'s `pythonpath = ["src", "."]` makes it importable. Core may never import it,
and since `pythonpath` includes `.` the old runtime `ModuleNotFoundError` defence is gone — the
AST lint in `tests/test_architecture.py` is now the **sole** enforcement. That lint catches direct
imports, bare relative imports, dynamic imports (`importlib`, `__import__`) and obfuscated calls
(`exec`, `eval`). It must not be weakened.

**Note on the working tree as of this writing:** `git status --short` showed **101 staged
additions under `.superpowers/sdd/`** (`A ` entries), the SDD ledgers being brought under tracking
by parallel work, plus a modified `tests/fixtures/NIST-PROVENANCE.md` and several modified/new
files under `docs/`. None of them affect a test result — but the `tests/fixtures/` one **will fail
`pytest` at the finalizer** (§4.4), and none of them are in a fresh clone of `30eb333`. Verify the
tree state yourself before trusting any number in §3.

---

## 8. UNVERIFIED claims in this document

| Claim | What would confirm it |
|---|---|
| Suite passes on Python 3.11 / 3.12 | Add them to the CI matrix; expect 428 passed |
| Workstation specs (4× A6000 Ada, sm_89, 48 GB, RHEL / Windows+WSL2) | `nvidia-smi --query-gpu=name,compute_cap,memory.total --format=csv` on each box |
| `sm_120` requires CUDA ≥ 12.8 / PyTorch ≥ 2.7 | Install torch and check `sm_120 in torch.cuda.get_arch_list()` |
| mutmut 3.7.0 refuses to run on Windows | `pip install mutmut==3.7.0 && mutmut run` on Windows (recorded in two tracked specs; not re-run here) |
| `scripts/fetch_nist_pmi.py` exits 1 on an AP242-count mismatch | Read at `scripts/fetch_nist_pmi.py:56-63`; not triggered, since the current archive yields the expected 17 |
| CI is green on both runners at `30eb333` | `gh run list --limit 5` (the `gh` CLI is not installed on this laptop) |
