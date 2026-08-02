# Task 9 report — mutual exclusion between the mutation layer and readers of `src/`

**Status:** COMPLETE. Commit `bdd632c`, base `main` @ `db93822`. Full suite **428 passed** (baseline 425 + 3).
Gate A exit **1** (7 PASS / 3 SKIP), unchanged. Tree clean, pushed to `origin`.

---

## 1. What was built

| File | Change |
|---|---|
| `tests/mutation_registry.py` | `MUTATION_LOCK` + `mutation_lock()` contextmanager; `run_declared_mutation` wraps mutate/run/restore/verify in it |
| `scripts/gate_a.py` | `_MUTATION_LOCK`, `_LOCK_HELD_EXIT = 2`, `_refuse_if_a_mutation_is_in_flight()`, called as the first statement of `main()` |
| `scripts/check_suite_integrity.py` | the same guard, called before the `--self-test-failure` argv branch |
| `tests/test_declared_mutations.py` | three new tests (the plan's two, plus one the plan does not have) |
| `.gitignore` | `.mutation-in-progress` |

Nothing under `src/` was touched. No table constant or threshold was changed. The
mutation score was not re-pinned and cosmic-ray was not run.

## 2. TDD — the failures, verbatim

### Stage A: the tests, no implementation

```
tests\test_declared_mutations.py:15: in <module>
    from tests.mutation_registry import (
E   ImportError: cannot import name 'MUTATION_LOCK' from 'tests.mutation_registry'
=========================== short test summary info ===========================
ERROR tests/test_declared_mutations.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

### Stage B: `mutation_lock` implemented, the scripts NOT yet guarded

This is the defect itself, reproduced live. With the lock held, `gate_a.py` ran to
completion and printed a full green report:

```
E           AssertionError: scripts/gate_a.py exited 1 with the lock held; expected 2.
E           A reader that merely fails for its usual reason is indistinguishable from
E           one that refused.
E
E             Gate A - checker correctness (blocking)
E
E               Y14.5 published worked examples  PASS(measured)  ...
E               Y14.5 self-consistency           PASS(measured)  ...
E               Monte Carlo convergence          PASS(measured)  ...
E               Checker reliability              PASS(measured)  mean 0.9975 over 200 ...
E               Validation isolation             PASS(measured)  no core imports
E               ...
E               7 PASS (5 measured, 2 attested), 0 FAIL, 3 SKIP.
E
E             Gate A: NOT CLEARED
E
E           assert 1 == 2
=========================== short test summary info ===========================
FAILED tests/test_declared_mutations.py::test_a_reader_refuses_to_run_while_a_mutation_is_in_flight
================= 1 failed, 2 passed, 26 deselected in 2.51s ==================
```

Note what stage B proves about the plan's own assertion. The plan's snippet checks
`proc.returncode != 0`. Gate A exits **1 on a clean tree by design** (three SKIPs
remain), so `!= 0` is satisfied whether the guard exists or not. The plan's test was
one substring (`"mutation" in output`) away from being a sixteenth instance of this
project's dominant failure mode. Both new tests pin the exit code **exactly**.

### Stage C: guards added — green

```
tests/test_declared_mutations.py::test_a_reader_refuses_to_run_while_a_mutation_is_in_flight PASSED
tests/test_declared_mutations.py::test_the_lock_clears_when_the_body_raises PASSED
tests/test_declared_mutations.py::test_the_runner_holds_the_lock_across_mutate_run_and_restore PASSED
```

## 3. Each test watched failing against a plausible broken implementation

Six mutants applied to the real files, run, reverted. Every one is killed.

| Mutant | Killed by | Observed |
|---|---|---|
| **M1** `mutation_lock` never writes the file | all three | `mutation_lock() did not create the lock file, so the refusals below would prove nothing`; `the lock was never taken, so its absence afterwards proves nothing`; `[False, False] == [True, True]` |
| **M2** `mutation_lock` has no `try/finally` | `lock_clears` | `a stale lock would block every later run` — `assert not True` |
| **M3a** lock taken and dropped, then the tree mutated unprotected | `holds_the_lock` | `the lock was not held at both writes (mutate, restore): [False, False]` |
| **M3b** lock covers mutate+test but is released before the restore | `holds_the_lock` | `... [True, False]` |
| **M4** the plan's original refusal wording | `reader_refuses` | `scripts/gate_a.py's refusal does not mention the stale-lock case. 'Wait for the suite to finish' is wrong advice when nothing is running` |
| **M5** only `gate_a` guarded, `check_suite_integrity` not | `reader_refuses` | `scripts/check_suite_integrity.py exited 1 with the lock held; expected 2` |

M1 is the exact mutant the brief warned about: the plan's
`test_the_lock_clears_when_the_body_raises` passes against a `mutation_lock` that
never creates the file. The shipped version records `MUTATION_LOCK.exists()` from
inside the body into `seen["held"]` and asserts it afterwards, so the absence of the
lock at the end only counts if it was present in the middle.

**A test of mine was itself vacuous and had to be rewritten.** The first draft of
`test_the_runner_holds_the_lock_across_mutate_run_and_restore` compared character
offsets of `with mutation_lock():` and the mutating write in the module source. It
**passed against M3a** — offsets cannot see block structure, so
`with mutation_lock(): pass` followed by an unprotected mutate/run/restore satisfied
`lock_at < mutate_at`. Recorded here because it is the project's dominant failure mode
reappearing inside the control added to close one, on the first attempt, in a task
whose brief warned about exactly it. The shipped version is behavioural: it
monkeypatches `_write_bytes_resiliently` and `_target_test_passes` into recorders that
sample `MUTATION_LOCK.exists()` and write nothing, then drives the real runner and
requires `[True, True]` at the mutate and restore writes. It touches no file on disk.

## 4. The two decisions the plan left open

### 4.1 Where the guard goes: **inside `main()`**, not at module level

This is not a style preference; module level is **actively wrong here** and would have
manufactured two guards that cannot fail.

`tests/test_gate_a.py` imports `scripts.gate_a` at module scope (line 10). Two registry
entries — `reliability-perturbation-tripled` and
`y14-5-worked-example-boundary-shifted` — target tests in that file, so
`run_declared_mutation` spawns a pytest subprocess that **imports `gate_a` while the
lock is held, by construction, on every suite run**. A module-level
`raise SystemExit(2)` would make those subprocesses exit non-zero at import.
`_target_test_passes` reads that as `passed_under_mutation = False`, and both entries
are `expect="fail"` — so both experiments would report **success for an entirely
spurious reason**, having never observed the mutation they exist to test. The guard
would have blinded two of the fifteen critical guards inside the layer built to catch
blind guards.

`tests/test_suite_integrity_script.py` imports `check_suite_integrity` the same way, to
read its pins; a module-level exit there turns a held lock into a collection error in
unrelated tests.

The distinction the placement encodes: **importing these modules is always safe; running
a measurement with them is what must not overlap.** In both scripts the check is reached
before any measurement work — in `check_suite_integrity.py` deliberately ahead of the
`--self-test-failure` branch, so the self-test path exercises the same guard.

### 4.2 Exit code 2 collides with nothing — checked, not assumed

- `gate_a.py`: `main()` returns 0 (cleared) / 1 (not cleared). 2 is free.
- `check_suite_integrity.py`: `main()` returns 0 (OK) / 1 (a pin failed). 2 is free.
- `.github/workflows/ci.yml`: the `suite` job runs `python -m pytest -q` and never
  invokes `gate_a.py`. The `integrity` job runs `python scripts/check_suite_integrity.py`
  as a bare `run:` step, so any non-zero fails the job — a refusal fails loudly rather
  than being swallowed. No CI step maps exit codes or uses `|| true`.
- The one place in the tree that treats non-zero uniformly is `tests/test_gate_a.py`,
  which asserts `returncode != 0` in four tests. Those run with no lock present and get
  1. That uniformity is precisely why the new test pins `== 2` instead of `!= 0`.
- `tests/test_suite_integrity_script.py::test_the_script_reports_and_exits_nonzero_when_a_layer_fails`
  already pins `returncode == 1` exactly, so a spurious refusal in that path would be
  caught by an existing test rather than absorbed.

**This matters concretely today:** `check_suite_integrity.py` currently exits 1 on the
mutation pin (100.00 vs 95.89 ± 0.50, P1.5's business). Without a distinct code,
"refused because of the lock" and "failed the pin" would be the same signal.

## 5. The stale-lock message

The plan's draft ends "Wait for the suite to finish." That is wrong advice in the case
that actually strands a human: a run killed mid-mutation leaves the lock behind and
**every later invocation refuses forever**, with nothing running to wait for. The
shipped message covers both states and is a procedure, not a report:

```
REFUSING TO RUN: a declared mutation is in progress.
  lock:    C:\Users\harsh\Downloads\Projects\Paper1\.mutation-in-progress
  held by: declared mutation in progress; pid=99999; started=2026-08-01T20:20:00
  This reader loads the checker core from disk in fresh interpreters and would measure
  a MUTATED checker, reporting a genuine number for the wrong instrument.
  If pytest is running in another window, wait for it to finish -- the lock clears itself.
  IF NOTHING IS RUNNING, THE LOCK IS STALE (a run was killed mid-mutation). Recover in
  this order:
    1. git status --short src/ tests/fixtures/
    2. anything modified there that you did not edit is a leftover mutant:
       git checkout -- src/ tests/fixtures/
    3. delete C:\Users\harsh\Downloads\Projects\Paper1\.mutation-in-progress
    4. re-run.
```

`check_suite_integrity.py`'s copy differs in one sentence — it says the script *also
mutates* those files itself, so an overlap races two writers for the restore. That is
the Task 7 accident, and the recovery is unchanged.

The lock file therefore carries `pid=` and `started=`, which is what lets the message
print `held by:` at all. A lock with no provenance leaves only "delete this and hope".

Two things this message deliberately does **not** claim:

- **Crash safety.** A SIGKILL between the write and the unlink leaves the lock behind,
  exactly as it leaves a mutated `src/` file behind. That is B10, and the table already
  rules it not-a-silent-false-green (a killed run produces no verdict). Rather than
  pretend the case cannot occur, the message treats it as expected and states the
  recovery. Step 1 of the recovery is O-B run by hand.
- **Mutual exclusion between two concurrent `pytest` runs.** The lock is advisory and
  last-writer-wins; two suites in parallel still collide on `src/`. Nothing in this task
  changes that, and `CLAUDE.md` still says so.

## 6. Verification, by hand

```
$ python -m pytest -q
428 passed in 59.45s

$ python scripts/gate_a.py ; echo $?        # unpiped, lock absent
  ... 7 PASS (5 measured, 2 attested), 0 FAIL, 3 SKIP.
  Gate A: NOT CLEARED
1

$ printf '...' > .mutation-in-progress      # lock present
$ python scripts/gate_a.py ; echo $?
REFUSING TO RUN: a declared mutation is in progress. ...
2
$ python scripts/check_suite_integrity.py ; echo $?     # REAL invocation, not --self-test
REFUSING TO RUN: a declared mutation is in progress. ...
2

$ rm .mutation-in-progress                  # lock gone
$ python scripts/gate_a.py >/dev/null 2>&1 ; echo $?
1
$ python scripts/check_suite_integrity.py --self-test-failure ; echo $?
Suite integrity: FAILED (Self-test (synthetic failure))
1

$ git status --short
(clean)
$ git check-ignore -v .mutation-in-progress
.gitignore:28:.mutation-in-progress	.mutation-in-progress
```

The refusing `check_suite_integrity.py` run above is the **real** invocation with no
flags, and it returned immediately instead of after ~25 minutes — direct evidence the
guard fires before `run_coverage()`. The lock-absent proof uses `--self-test-failure`
because running the real path means running cosmic-ray, which the brief puts out of
scope; the guard sits ahead of the argv branch, so it is the same code path.

## 7. The Task 8 table, checked against what was built

Row 9 of `docs/superpowers/specs/2026-08-01-observation-assignment.md` §3 predicts:
failure mode "a published Gate A number measured against a mutated checker, silent
false green"; revealed by **none** (O-B structurally blind — clean after, corrupt
during); verdict **Yes, a control is required**.

**The implementation matches the row.** Stage B above is that row's failure-mode cell
executed rather than asserted: with a mutation in flight, Gate A printed
`7 PASS (5 measured, 2 attested), 0 FAIL` and `git status` was clean afterwards. No
amendment to the spec is needed and none was made; §3.2's "add a row" does not apply,
because the control is already the table's own ninth row.

**The regress terminates, and it is worth saying where.** R2 applied to `mutation_lock`
itself asks: if the lock silently stops being taken, what reveals it? Before this task,
nothing. After it, **O-A** — `test_a_reader_refuses_to_run_while_a_mutation_is_in_flight`
runs unattended on every suite invocation and fails loudly, and it observes the two real
scripts as subprocesses rather than inspecting the lock's implementation. That is R4
("prefer observing an artifact over guarding a guard") satisfied literally, and it is
why no fourth-level control is required.

## 8. Findings — what did not hold

**T9 FINDING 1 (plan, sixth consecutive task).** The plan's
`assert proc.returncode != 0` cannot fail: `gate_a.py` exits 1 on a clean tree by
design. Only the `"mutation" in output` substring kept the snippet honest. Both shipped
tests pin the exit code exactly.

**T9 FINDING 2 (plan).** `REPO_ROOT` was the plan's guess for the repo-root constant in
`tests/mutation_registry.py` — it is correct there, but `scripts/gate_a.py` calls its
own constant `REPO` and `tests/test_declared_mutations.py` had no such constant at all.
Imported `REPO_ROOT` from `mutation_registry` rather than minting a second one.

**T9 FINDING 3 (plan, load-bearing).** The plan gives no guidance on guard placement and
its snippet is written at module scope. Module scope would have silently neutered the
two `tests/test_gate_a.py`-targeted registry entries — see §4.1. Had the snippet been
pasted as written, the layer's own reports would have kept saying PASS.

**T9 FINDING 4 (my own first draft).** The source-offset version of
`test_the_runner_holds_the_lock_across_mutate_run_and_restore` passed against M3a. See
§3. It is recorded rather than quietly fixed, because "the reviewer wrote a test that
cannot fail while adding the control for tests that cannot fail" is the most useful
single data point this task produced about R5.

**T9 FINDING 5 (brief, minor and not acted on).** The brief scopes the change to five
files, none of which is `CLAUDE.md`. `CLAUDE.md`'s concurrency paragraph is now
*enforced* rather than merely stated, and a reader would benefit from one sentence
pointing at `.mutation-in-progress`. Not done: `CLAUDE.md` is out of scope and is not a
file an agent should edit on another agent's instruction. **Recommended follow-up for
the human**, one sentence, no behaviour change:

> Both scripts now refuse to start (exit 2) while `.mutation-in-progress` exists;
> `tests/mutation_registry.mutation_lock()` holds it for the mutate/run/restore window.
> The warning above is still the reason, but it is no longer the only thing standing
> between you and a false green.

**T9 FINDING 6 (out of scope, confirmed as stated).** `check_suite_integrity.py` exits 1
on `MUTATION SCORE 100.00 vs pin 95.89 -> FAIL, pin detached upward`, exactly as the
brief says. Not re-pinned, not investigated. It is now distinguishable from a refusal by
exit code.

## 9. Duplication, declared

`_refuse_if_a_mutation_is_in_flight` is duplicated in the two scripts rather than
shared. `scripts/` is not an installed package;
`python scripts/check_suite_integrity.py` puts `scripts/` on `sys.path[0]` while
`tests/test_gate_a.py` imports `scripts.gate_a` with the repo root on the path, and no
single import form resolves in both entry points. Twelve duplicated lines were preferred
to an import that works in one place and not the other.
`test_a_reader_refuses_to_run_while_a_mutation_is_in_flight` drives **both** copies as
subprocesses, so they cannot drift apart silently — M5 above is that claim watched
failing.
