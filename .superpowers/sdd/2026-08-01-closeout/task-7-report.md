# Task 7 report: CI that exercises the corruption mode

Base: main @ 05d4dae. Result: main @ 2184485 (full SHA
218448575134d568fdfd4b88a70a8d260628279a), pushed.

## Files

- Created `tests/test_gitattributes_clone.py` (per brief step 1, unchanged from
  the brief's snippet -- it ran as written).
- Created `.github/workflows/ci.yml` (two jobs: `suite`, `integrity`; departs
  from the brief in one respect, explained below).

## Step 2: the mutation demonstration -- both results, and a correction

### Baseline (current `.gitattributes`, proves nothing by itself)

```
tests/test_gitattributes_clone.py::test_the_fixture_survives_a_clone_under_every_autocrlf_setting[true] PASSED
tests/test_gitattributes_clone.py::test_the_fixture_survives_a_clone_under_every_autocrlf_setting[input] PASSED
tests/test_gitattributes_clone.py::test_the_fixture_survives_a_clone_under_every_autocrlf_setting[false] PASSED
3 passed
```

### First mutation attempt found a real, separate bug in the brief's own method

The brief's Step 2 says: comment out `*.stp binary` and commit. I did exactly
that on a scratch branch (`scratch/gitattr-mutation-demo`) and re-ran the
test: **all three cases still passed, 396,445 bytes unchanged.** The reason
is not idempotent checkout behaviour -- it's simpler and more concrete:
`git check-attr` showed `binary: set` even with that line commented out,
because **`core.ignorecase=true` on this Windows checkout makes
`.gitattributes` glob matching case-insensitive**, so the still-active
`*.STP binary` line matched the lowercase `nist_..._ap242-e1.stp` filename
too. Commenting out only the lowercase line leaves the fixture protected.
Confirmed with:

```
$ git config --get core.ignorecase
true
$ git check-attr binary -- tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp
tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp: binary: set        # still set!
```

Fix for the demonstration: comment out all four lines (`*.stp`, `*.STP`,
`*.step`, `*.STEP`). After that, `check-attr` reported `binary: unspecified`
as expected.

### Second finding: the byte count the brief predicts appears, but on the
### wrong parametrize case -- the brief's causal story is backwards

With all four lines disabled, committing the `.gitattributes` change alone
still left the fixture untouched on clone (396,445 bytes, all three cases
green), because the object already stored in git history is the correct,
original CRLF blob, and checkout of an already-CRLF blob under
`autocrlf=true` is idempotent (git only inserts a CR before an LF that
doesn't already have one; every line here already ends CRLF, so nothing
changes). To actually manufacture the corrupted 391,739-byte object described
in the brief, I had to reproduce the *historical* event, not just remove the
attribute: set `core.autocrlf=true` locally and run
`git add --renormalize tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp`, which
invoked git's CRLF-stripping clean filter against the working-tree file and
staged a genuinely different, smaller blob. Verified before committing:

```
$ git show :tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp | wc -c
391739
```

Committed that on the scratch branch, then re-ran the test:

```
tests/test_gitattributes_clone.py::test_..._setting[true]  PASSED
tests/test_gitattributes_clone.py::test_..._setting[input] FAILED
tests/test_gitattributes_clone.py::test_..._setting[false] FAILED

FAILED [input]: AssertionError: autocrlf=input produced 391739 bytes, not 396445. ...
E       assert 391739 == 396445
FAILED [false]: AssertionError: autocrlf=false produced 391739 bytes, not 396445. ...
E       assert 391739 == 396445
2 failed, 1 passed
```

**This is the opposite of what the brief predicted.** The brief says "confirm
the `autocrlf=true` case FAILS reporting 391,739 bytes." Measured: `true`
PASSES (it self-heals the corrupted, LF-only blob back to byte-identical,
hash-identical 396,445-byte content on checkout, because it inserts a CR
before every bare LF). `input` and `false` are the cases that actually
surface a corrupted committed blob, because neither converts on checkout.

Mechanistic reason: the historical corruption event was a **commit-time**
event (a contributor's `git add`/`commit` with `autocrlf=true` and no
`.gitattributes` protection ran the CRLF->LF *clean* filter and the stripped
blob is what got stored, permanently, in the object database). CI never
commits -- it only checks out an already-decided blob -- so there is no
commit-time step for a CI checkout to reproduce. And on the checkout side,
`autocrlf=true` was measured to hide a stored corruption rather than expose
it.

Discarded completely afterward:

```
$ git checkout main
$ git branch -D scratch/gitattr-mutation-demo
$ git status --short
(only the new, still-untracked test file listed; .gitattributes and the
 fixture both back to their committed originals, hash 85a5752d...b821,
 396445 bytes -- confirmed by re-reading both after the branch delete)
```

## Step 3: the workflow -- one deliberate deviation from the brief

`.github/workflows/ci.yml`:

- **`suite`**: matrix `[ubuntu-latest, windows-latest]`, triggered on
  `push`/`pull_request` only (`if: github.event_name == 'push' ||
  github.event_name == 'pull_request'`). Steps: `actions/checkout@v4`,
  `actions/setup-python@v5` (3.13), `pip install -e ".[dev,gen]"`,
  `python -m pytest -q`.
- **`integrity`**: triggered on `workflow_dispatch` and a weekly `schedule`
  only (`if: github.event_name == 'workflow_dispatch' ||
  github.event_name == 'schedule'`, cron `0 6 * * 1`). Runs
  `python scripts/check_suite_integrity.py`. Never on push.

**Deviation, and why**: the brief instructs "the Windows leg runs
`git config --global core.autocrlf true` before checkout." I did not add
this step. Per the Step 2 finding above, that instruction rests on a
mistaken model of where the corruption happens (checkout) when it actually
happens at commit time, and empirically the opposite of what it claims:
forcing `autocrlf=true` on checkout would make a corrupted commit look
*healthy* on the Windows runner (self-heal to the correct byte count and
hash), which is a false-negative, not a detector. The actual detector,
`tests/test_gitattributes_clone.py`, already parametrizes `core.autocrlf`
across `true`/`input`/`false` via its own nested `git -c core.autocrlf=...
clone`, independent of whatever the outer runner's ambient config is -- so
it gets full coverage of the failure mode on either platform without any
outer override. The full rationale is recorded as a comment block at the
top of `ci.yml`.

I did keep the `windows-latest` leg in the matrix: its value is unrelated to
autocrlf -- it is the platform-portability check the brief's own comment
template asks for (`pip install -e ".[dev,gen]"` succeeding from nothing on
a bare Windows Python 3.13, not reusing an ambient interpreter).

## Step 4: full suite, Gate A, clean tree

```
$ python -m pytest -q
402 passed in 61.55s     (399 previously + 3 new clone-parametrize cases)

$ python scripts/gate_a.py; echo "GATE_A_EXIT=$?"
... 7 PASS (5 measured, 2 attested), 0 FAIL, 3 SKIP ...
Gate A: NOT CLEARED
GATE_A_EXIT=1
```

```
$ git status --short
(clean before staging; after `git add` + commit, clean again)
```

## Commit and push

```
$ git commit -m "feat: CI exercising the CRLF corruption mode, integrity layer off the push path" ...
[main 2184485] ...
 2 files changed, 121 insertions(+)
$ git push origin main
   05d4dae..2184485  main -> main
```

## Step 5: watching Actions

`gh` CLI is not installed in this environment (`which gh` /
`where.exe gh` both came back empty). Per the brief, that would normally mean
reporting "could not observe" rather than assuming success -- but a browser
tool was available and the repo is public, so I watched the run directly via
`github.com/harshD42/TolAEG-CAD/actions` and the public
`api.github.com/repos/.../actions/runs/<id>/jobs` endpoint (no auth needed
for a public repo's run/job status).

Run: `https://github.com/harshD42/TolAEG-CAD/actions/runs/30723976715`
(commit 2184485, event: push).

Confirmed immediately: **`integrity` job's conclusion is `skipped`**,
completed in the same second it started -- the `if:` gate worked, it did not
attempt to run cosmic-ray on push.

`suite (ubuntu-latest)` and `suite (windows-latest)` results, polled to
completion via the public jobs API (`run status: completed, conclusion:
success`):

```
suite (windows-latest) -> completed success
    all 7 steps success (checkout, setup-python, install, full suite, ...)
suite (ubuntu-latest) -> completed success
    all 7 steps success (checkout, setup-python, install, full suite, ...)
integrity -> completed skipped
```

Both `suite` legs went green on the first push, on both platforms, from a
completely bare runner. Run:
https://github.com/harshD42/TolAEG-CAD/actions/runs/30723976715

Final confirmation the tree is still clean after all of this:

```
$ git status --short
(nothing)
$ git log --oneline -1
2184485 feat: CI exercising the CRLF corruption mode, integrity layer off the push path
```

## Side finding worth flagging, out of scope to fix here

`core.ignorecase=true` (Windows/macOS default) makes `.gitattributes` glob
patterns match case-insensitively. The four-line belt-and-braces
`*.stp`/`*.STP`/`*.step`/`*.STEP` set is more redundant than its own comment
("Both extensions and both cases: gitattributes patterns are case-sensitive")
claims -- on a case-insensitive checkout, `*.STP` alone already covers `.stp`.
That comment is accurate for git's own attribute-matching engine only on a
case-sensitive filesystem/config (`core.ignorecase=false`, e.g. most Linux
CI runners) -- not universally, as its wording implies. Not touched (the
brief and CLAUDE.md both put `.gitattributes` changes out of scope beyond
what Task 7 needs), noted here for the record since it directly explains why
the naive one-line mutation in Step 2 didn't work.
