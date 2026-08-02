# Task 9 brief — mutual exclusion between the mutation layer and readers of `src/`

Source: `docs/superpowers/plans/2026-08-01-closeout.md` §"Task 9" (lines 957–1063).
Base: `main` @ `db93822`. Baseline: **425 passed**, Gate A exit **1**, tree clean, pushed.

## Why this control exists

`scripts/gate_a.py` shells out to a fresh interpreter that reads `tests/test_reliability.py`
and the checker core **from disk**. While `run_declared_mutation` has, say,
`reliability-perturbation-tripled` applied, `src/tolcad/reliability.py` on disk is mutated.
An overlapping run therefore reports a Gate A number measured against a mutated checker —
a silent false green.

**O-B structurally cannot reveal it:** the tree is clean *after* the run; the corruption
exists only *during* it. O-A and O-C also miss it. Only O-D found it. Per the
observation-assignment spec committed in Task 8 (R2 + "O-D discovers, it does not guard"),
a control is required, and a `CLAUDE.md` warning is not one (R5).

This is not hypothetical: during Task 7 an implementer accidentally launched
`check_suite_integrity.py`, killed it, and found `y14_5.py` left mutated.

## Scope

- Modify `tests/mutation_registry.py` — add `MUTATION_LOCK` + `mutation_lock()`; wrap the
  mutate/run/restore section of `run_declared_mutation`.
- Modify `scripts/gate_a.py` and `scripts/check_suite_integrity.py` — refuse to start.
- Modify `tests/test_declared_mutations.py` — the two new tests.
- Modify `.gitignore`.

Do NOT touch anything under `src/`. Do NOT change any table constant or threshold, and do
NOT re-pin the mutation score (it currently reads 100.00 against a 95.89 pin;
`check_suite_integrity.py` fails today and that is P1.5's business, not yours).

## Draft code — verify before use

The plan's snippets are a draft. Four consecutive tasks found plan code that did not run as
written (wrong threshold direction, nonexistent symbols, wrong arity, a backwards rationale).
Read the real files first.

### Test (append to `tests/test_declared_mutations.py`)

```python
def test_a_reader_refuses_to_run_while_a_mutation_is_in_flight():
    from tests.mutation_registry import MUTATION_LOCK, mutation_lock

    assert not MUTATION_LOCK.exists()
    with mutation_lock():
        assert MUTATION_LOCK.exists()
        proc = subprocess.run(
            [sys.executable, "scripts/gate_a.py"],
            cwd=REPO, capture_output=True, text=True,
        )
        assert proc.returncode != 0
        assert "mutation" in (proc.stdout + proc.stderr).lower()
    assert not MUTATION_LOCK.exists(), "the lock must clear even on the happy path"


def test_the_lock_clears_when_the_body_raises():
    from tests.mutation_registry import MUTATION_LOCK, mutation_lock

    with pytest.raises(RuntimeError):
        with mutation_lock():
            raise RuntimeError("boom")
    assert not MUTATION_LOCK.exists(), "a stale lock would block every later run"
```

Check the module's existing imports and whether a `REPO`-like constant already exists under
some other name before adding one.

### `tests/mutation_registry.py`

```python
MUTATION_LOCK = REPO_ROOT / ".mutation-in-progress"


@contextlib.contextmanager
def mutation_lock():
    MUTATION_LOCK.write_text("declared mutation in progress\n", encoding="utf-8")
    try:
        yield
    finally:
        MUTATION_LOCK.unlink(missing_ok=True)
```

Verify the real name of the repo-root constant in that file — `REPO_ROOT` is the plan's
guess.

### Both scripts

```python
_MUTATION_LOCK = Path(__file__).resolve().parent.parent / ".mutation-in-progress"
if _MUTATION_LOCK.exists():
    print(
        "REFUSING TO RUN: a declared mutation is in progress "
        f"({_MUTATION_LOCK}). This reader loads the checker from disk and would "
        "measure a mutated one. Wait for the suite to finish.",
        file=sys.stderr,
    )
    raise SystemExit(2)
```

Two things the plan does not say and you must decide and justify:

1. **Where the guard goes.** At module top level it fires on import — which also fires if
   anything merely imports the script. Inside `main()` it fires only on execution. Pick one
   and say why. Whichever you pick, the check must fire before any measurement work.
2. **Exit code 2 collides with nothing?** `gate_a.py` uses 0/1 meaningfully; confirm 2 is
   free in both scripts and that no caller (CI, tests) treats non-zero uniformly in a way
   that would hide the refusal. Check `.github/workflows/ci.yml`.

## Two failure modes to test for beyond the plan's two

- **The guard must not be defeated by a cleanup that never runs.** Verify by inspection that
  `run_declared_mutation` restores the file inside the same `try/finally` region, so a
  mutation cannot outlive the lock.
- **A stale lock must be diagnosable.** If a process is killed mid-mutation the lock file
  survives and every later Gate A run refuses. The message must tell a human what to do.
  Confirm the wording does — "wait for the suite to finish" is wrong advice for a stale lock.
  Improving it is in scope.

## Method

TDD. Write the tests, run them, **watch them fail, record the output verbatim**, then
implement, then green.

## Verification before commit

- `python -m pytest -q` — full suite, report the count (baseline 425).
- `python scripts/gate_a.py; echo $?` — **no pipe**, expect exit 1 (lock absent).
- Prove the refusal by hand: create `.mutation-in-progress`, run each script, show both
  refuse; delete it; show both run again.
- `git status --short` clean.
- Commit and push to `origin` (https://github.com/harshD42/TolAEG-CAD).

## Report

Write the full report to `.superpowers/sdd/2026-08-01-closeout/task-9-report.md` and append
a T9 entry to `.superpowers/sdd/2026-08-01-closeout/progress.md`.
