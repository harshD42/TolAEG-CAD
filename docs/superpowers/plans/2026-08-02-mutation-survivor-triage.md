# Mutation-Survivor Triage (P1.5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the tree-cleanliness finalizer that silently disabled Layers 2 and 3, prove the repair with a committed regression test, re-measure Layer 2 honestly, enumerate and triage every surviving mutant into a committed table, and only then re-pin — two-sided, with the enumeration in the same commit.

**Architecture:** Eight tasks in one serialised block. The diagnosis is already established (see below), so Task 1 is not an investigation: it is the regression test that stops the defect recurring, followed by the fix. Layer 3 is re-verified next because it is cheap and it has been vacuous for the same reason. Then Layer 2 is made *enumerable* — it currently deletes its own session databases, so no survivor list can exist — measured, enumerated, triaged, controlled, re-measured and re-pinned.

**Tech Stack:** Python 3.13, pytest 9.0.2, cosmic-ray 8.4.6, numpy 2.4.1 (pinned), git worktrees. No CadQuery in any task here.

**Canonical numbers:** `docs/superpowers/specs/2026-08-01-ledger-reconciliation.md`. Read it before starting. Cite it; do not restate its figures. The ledgers under `.superpowers/sdd/` are contemporaneous and full of superseded values — narrative only.

---

## What happened, stated plainly

**A control silently disabled two other controls, and looked perfectly healthy while doing it.**

`tests/conftest.py`'s session-scoped autouse finalizer — the O-B tree-cleanliness guard,
added by close-out Task 1 at `d7285f9` — fails any pytest session that ends with
`git status --porcelain src/ tests/fixtures/` non-empty. It never records the state at the
*start* of the session, so it cannot distinguish "the suite dirtied the tree" from "the tree
was already dirty."

Both of the repository's mutation layers dirty the tree *before* launching a pytest
subprocess:

- **Layer 2.** cosmic-ray writes the mutant into `src/tolcad/<module>.py` on disk, then runs
  the test command, then restores. `cosmic_ray/testing.py::run_tests` reads only the exit
  code: `0` → `SURVIVED`, anything else → `KILLED`. The finalizer makes every exit code
  non-zero, so **every mutant is recorded killed**. Layer 2 reported **100.00%** and has
  measured nothing since `d7285f9`.
- **Layer 3.** `run_declared_mutation` writes the declared mutation, then calls
  `_target_test_passes`, which returns `proc.returncode == 0`. The finalizer makes that
  `False` unconditionally, so every `expect="fail"` entry whose target lies under `src/` or
  `tests/fixtures/` **passes whether or not its guard can detect anything**. That is 13 of the
  15 registry entries.

The two symptoms have one cause and one fix, and the fix is not an exemption.

### The measurements this rests on

Three independent reproductions, all in throwaway clones — the real tree was never dirtied.

**1. The coordinator's reproduction.** Clone HEAD, append a semantically inert comment to
`src/tolcad/types.py` (a textbook surviving mutant), run cosmic-ray's test-command shape:

```
.......E                                                       [100%]
ERROR at teardown of test_negative_position_tol_rejected
THE SUITE LEFT TRACKED FILES MODIFIED. A declared mutation did not restore.
 M src/tolcad/types.py
7 passed, 1 error in 0.08s
EXIT=1
```

All seven tests passed. The run still exited 1.

**2. Layer 3 is vacuous — measured, not inferred.** In a clone at `30eb333`, a
`DeclaredMutation` with `expect="fail"` whose `replace` appends a **trailing comment** to a
dataclass field in `src/tolcad/types.py`, pointed at
`tests/test_types.py::test_verdict_is_immutable`. No test can detect a comment, so the
experiment must fail. It did not:

```
RESULT: run_declared_mutation PASSED an inert comment mutation.
        => Layer 3 is VACUOUS: expect='fail' entries pass unconditionally.
```

**3. The snapshot fix restores both, and the registry survives it.** With `tests/conftest.py`
replaced by the snapshot form specified in Task 1, the same probe is correctly rejected:

```
RESULT: run_declared_mutation correctly REJECTED it:
        inert-comment-probe: tests/test_types.py::test_verdict_is_immutable still PASSED
        with src/tolcad/types.py corrupted. That guard cannot detect what it exists to
        detect.
```

and the real registry, honestly executed for the first time since `d7285f9`, passes in full:

```
15 passed, 14 deselected in 27.73s
```

**So the Layer 3 damage is to provenance, not to the guards.** Every one of the fifteen
declared mutations does detect its corruption. What was lost is the *evidence* that it does —
and for four entries, the evidence never existed at all. `ladder-d2-row-shifted`
(`4094bd5`), `tapped-hole-upper-dev-nonzero` and `case-sensitive-guard-uppercased`
(`928ca1f`), and `y14-5-worked-example-boundary-shifted` (`05d4dae`) were all added after
`d7285f9` and have therefore **never once been honestly executed**. Task 2 executes them and
records the result. A guard that has never been watched failing is exactly what the registry
exists to prevent; four of them were sitting inside it.

**Timeline, verified.** `d7285f9` (2026-08-01 18:28:20) created the finalizer. It is an
ancestor of both `062316e` (18:35:00, where `MUTATION_MEASURED = 95.89` was pinned) and
`05d4dae` (19:18:53, where 100.00% was observed). The 95.89 *measurement* was taken by the
architect on the feature branch before the finalizer existed — the closeout plan document
itself is `0e046ac` at 18:12:57 and already quotes the figure — so **95.89 is very likely the
last real Layer 2 number**, and this plan treats it as the last honest reading rather than as
a pin to defend.

### What this episode is

It is the project's signature defect — the check that cannot fail — in its sharpest form yet:
**a control silently disabled another control.** The O-B tree-cleanliness guard destroyed the
Layer 2 mutation score and hollowed out the Layer 3 registry, and every dashboard read green.
Layer 2 read 100.00%; Layer 3 read 15 passing experiments; the suite read 428 passed.

**No new ordinal is minted for it.** The reconciliation's *instance count* section fixes the
canonical count at twelve, refers to instances **by name rather than by number**, and
explicitly supersedes the ordinals "thirteenth" and "fifteenth" as a numbering scheme —
"inventing them would be the same defect in a new coat". This instance is therefore named:
**the O-B finalizer capture**. Refer to it by that name everywhere.

### The vindication, which belongs in the record

**The two-sided pin caught it.** A one-sided floor would have read `100.00 >= 93.35` and
stayed green forever, through pre-registration and through corpus generation, with both
mutation layers dead. The close-out Task 2 decision to make both pins two-sided is the single
reason this was found at all — and it was found on the pin's *first real encounter* with a
detached measurement. That is the strongest available evidence for the two-sided-pin rule and
it should be cited whenever the rule is questioned.

The corollary is the constraint below.

### Re-pinning before the triage is FORBIDDEN

Not discouraged — forbidden. Re-pinning `MUTATION_MEASURED` to an observed value before the
survivor set is enumerated would discard the only signal Layer 2 has ever produced for free,
and it would do so at the exact moment the signal proved its worth. Task 8 is the only task
permitted to touch `MUTATION_MEASURED`, and only with the enumeration in the same commit.

### What the artefact does not excuse

The **triage is still owed.** The reconciliation's *untriaged survivors* section records the
last genuine enumeration: run 3, 40 survivors, of which 19 were corrected documented
equivalents, leaving 21 untriaged. Every figure after that — ~17, ~12, ~27, and 0 — is
arithmetic over a score, and the 0 was never evidence of anything. Plan for a survivor set on
the order of run 3's, not for the ~27 the 95.89 score implies against a 650 denominator.

---

## Global Constraints

- **`docs/superpowers/specs/2026-08-01-ledger-reconciliation.md` is the canonical source for
  every contested figure.** Cite it by section name. Never quote a figure from a ledger under
  `.superpowers/sdd/`.
- **Do NOT re-pin `MUTATION_MEASURED` before Task 8.**
- **Pre-registered Gate A/B/C/D thresholds in design spec §7 are frozen** (`CLAUDE.md`).
  `scripts/gate_a.py` must still exit **1** with **7 PASS (5 measured, 2 attested) / 0 FAIL /
  3 SKIP** at the end of every task.
- **Do NOT change any value** in `_IT_MICRONS`, `_DEVIATION_MICRONS`, `_SIZE_BANDS`,
  `_CLEARANCE_HOLE_MM`, `TAPPING_DRILL_MM`, `_TOL_FRACTION_RANGE`, `_MIN_WALL_MM`,
  `_EDGE_MARGIN_MM`. **Do not modify any of the six core modules** — the mutated code must not
  move underneath the measurement.
- **Do NOT delete or weaken any of the 15 registry entries.** All fifteen have now been
  observed passing under a repaired finalizer.
- **The Tier 1 ladder must stay at d1 31/159, d2 99/301, d3 239/452, d4 421/609** over seeds
  0–199 on numpy 2.4.1, corpus digest unchanged (`tests/gen/test_ladder_pin.py`). Re-confirm
  at the end of Tasks 1, 5 and 8.
- **Layer 2's scope is exactly six modules** under `src/tolcad`: `types`, `y14_5`, `iso286`,
  `montecarlo`, `checker`, `reliability`. `gen/` is excluded by design spec §2's non-goals
  ("Not applied to `gen/`"). **A scope change silently moves the score** — Layer 1's
  48.0-vs-94.74 confusion in the reconciliation doc is exactly this error, caused by
  `--cov=src/tolcad` sweeping in `gen/`. No task may change `CORE_MODULES`, the `test-command`
  in `cosmic-ray.toml`, or `[tool.coverage.run] omit` in `pyproject.toml`. If a scope change is
  ever genuinely wanted it is a separate plan with its own baseline.
- **A full cosmic-ray run is ~25 minutes** (`.github/workflows/ci.yml`; the closeout plan).
  Record whatever you actually measure in the run manifest. Note without chasing: the
  suite-integrity plan predicted ~5 minutes from the `types.py` spike.
- **Layer 2 stays off the push path.** `.github/workflows/ci.yml` runs the `integrity` job
  under `if: github.event_name == 'workflow_dispatch' || github.event_name == 'schedule'`
  only, with a weekly `cron: "0 6 * * 1"`. Verified. Do not move it onto `push`.
- **Nothing may edit `src/` OR `tests/` while a cosmic-ray run is in flight.** `src/` is what
  is mutated; `tests/` *is* the test command. Enforced mechanically by the **run manifest**
  (Task 3): `git rev-parse HEAD` plus a digest of `git status --porcelain src/ tests/`,
  recorded before and after every `exec`, with the score refused if they differ. This is also
  what makes an interrupted-and-resumed run safe.
- **All of P1.5 runs in a dedicated git worktree** on branch `p1.5/mutation-survivor-triage`,
  so a concurrent session on `main` cannot invalidate a run in progress.
- **The mutation lock is live.** `tests/mutation_registry.mutation_lock()` writes
  `.mutation-in-progress`; `scripts/gate_a.py` and `scripts/check_suite_integrity.py` exit
  **2** (`_LOCK_HELD_EXIT`) while it exists. Exit 2 is a refusal, never a failed pin. If you
  see it and nothing is running, the lock is stale — follow the recovery procedure the script
  prints. It did not cause the 100.00% (`bdd632c` postdates `05d4dae`), and the cosmic-ray
  test command never takes it (none of the six core test files imports `tests/mutation_registry`).
- **Never run `pytest` concurrently with `scripts/check_suite_integrity.py` or
  `scripts/gate_a.py`** (`CLAUDE.md`). During Tasks 3 and 8 the machine runs one thing.

## Re-costed estimate

**≈ 17.5 h of engineering, i.e. 2 – 2.5 serialised days.** The brief's 1.5 days was costed
before the diagnosis and before the Layer 3 finding. It has gone **up**, not down:

| Change | Effect |
|---|---|
| Diagnosis now known | **−1.5 h** — no hypothesis-discrimination task |
| Layer 3 re-verification is new work (Task 2) | **+1.5 h** |
| Realistic survivor scale is run 3's 40, not the ~27 implied by 95.89 | **+1.5 h** on Tasks 4–6 |
| The triage control re-executes every verdict at ~2 min/mutant | **+1 h** |
| Two full Layer 2 runs (Task 3 and Task 8) are mandatory, not optional | ~50 min unattended |

Contingency not in the 17.5 h: **a third full run**, if Task 8's re-measure surfaces a
survivor that Task 5 never triaged. That is +30 min plus however long the new rows take. Do
not compress the schedule by skipping Task 8's set-difference check — pinning over an
untriaged survivor is the state this plan started in.

---

## Path exclusion vs. snapshot: the decision, and why

The coordinator asked that this be evaluated rather than assumed.

| Option | Verdict |
|---|---|
| **Exclude `src/` while a mutation tool runs**, keyed on an env var or on `.mutation-in-progress` | **Rejected.** It is an opt-out on the control that catches a corrupted working tree, and design spec §6 rules the shape out ("It does not silently skip, because a skipped integrity layer is the failure mode being fixed"). It also cannot distinguish cosmic-ray's live mutant from a leftover one, which is the case O-B exists for. And it would require the finalizer to know which tools exist — a list that goes stale. |
| **Narrow the watched paths** (e.g. watch only `tests/fixtures/*.stp`, not the directory) | **Rejected as the primary fix, adopted as a message improvement.** It would fix the `NIST-PROVENANCE.md` symptom and nothing else; Layer 2 and Layer 3 would stay dead. |
| **Snapshot at session start, compare at session end** | **Adopted.** It asks O-B's actual question — *did this run leave the tree dirty?* — rather than the different question it currently asks. It fixes all three symptoms with no opt-out and no tool-specific knowledge, and it loses nothing: a declared mutation that fails to restore is clean at the start and dirty at the end, which is precisely the case the control exists for. **Measured**: with the snapshot in place, the inert-comment probe is correctly rejected and all 15 registry entries still pass. |

Cost of the snapshot: one extra `git status` per pytest session, ~50 ms. Across a full Layer 2
run that is roughly a minute added to ~25. Accepted; recorded in the code comment.

**Separately, the recovery message is destructive and must be fixed in the same task.** It
currently advises `git checkout -- src/ tests/fixtures/` unconditionally. `tests/fixtures/`
holds exactly two files: the `.stp` mutation target and `NIST-PROVENANCE.md`. An operator who
edits the documentation file and runs the suite is told to run a command that destroys their
work. The repaired message names **only the newly-dirty paths** and offers a checkout scoped
to those paths.

---

## Spikes

Cross-reference `docs/SPIKES.md` **by title**, never by ID — IDs there are assigned by that
register, not by this plan.

**Two spikes already in the register are answered by this plan and must be closed by it,
not left open:**

- **"Why does the mutation score read 100.00%?"** — answered by the diagnosis at the top of
  this document. Mark it RESOLVED in Task 2 Step 7, with the resolution pointing at
  `docs/superpowers/specs/2026-08-02-ob-finalizer-capture.md`. Do not leave an open spike
  whose answer is committed elsewhere; that is how the survivor count went missing.
- **"How much of the mutation kill count is behavioural?"** — this is the survivor-triage
  question, and Tasks 5 and 6 answer it. Mark it RESOLVED in Task 8 Step 6, pointing at the
  triage table's verdict distribution. Note the answer is now *known to have been unmeasurable*
  for the whole capture window, which is worth recording in the register rather than just in
  the plan.

The three spikes below are new and are owned by this plan.

### Spike — "What the 468 non-viable Layer 2 jobs actually are"

**Time box: 45 minutes. Runs inside Task 3, before the first honest re-measure.**

`_mutate_one_module` computes `incompetent = report.count("TestOutcome.INCOMPETENT")` from
cr-report's text and the denominator as `total - incompetent`. But `cr-report` prints
`test outcome: None` for jobs whose `worker_outcome` is `WorkerOutcome.NO_TEST` (no mutation
was possible at that occurrence), that string is invisible to the count, and
`WorkResult.is_killed` — which is `test_outcome != TestOutcome.SURVIVED` — treats them as
killed. The reconciliation's *mutation score* section records 468 excluded jobs against 1,118.
If any of those are NO_TEST rather than INCOMPETENT, the denominator every pin has ever been
computed over is wrong, in the same shape as the Layer 1 scope error.

**Resolve it by** opening a session database and tabulating `(worker_outcome, test_outcome)`
pairs. **Fallback:** stop parsing cr-report text and compute all counts from
`cosmic_ray.work_db.WorkDB` (Task 3 does this regardless); record the denominator change as a
**correction stating both the old and the new denominator** in Task 8's reconciliation
amendment. Never swap a denominator silently.

### Spike — "A decidable test for 'equivalent mutant'"

**Time box: 1 hour. Runs at the start of Task 6.**

SI-4's fix round found **nine mislabelled mutants** — four called "equivalent" that were live,
five called "killed" that did not kill (reconciliation, *untriaged survivors*). A prose
argument produced that error and prose is still the process. The proposed control is to apply
the mutant and require a fixed observable set to be **identical**; the unknown is which
observables make an equivalence claim decidable rather than merely plausible.

**Proposed observable set:** (a) the full suite's pass/fail and test count; (b)
`python scripts/measure_ladder.py` — all four counts plus the corpus digest; (c) Gate A's
report, if and only if it can be captured outside the mutation lock (see Task 6).

**Fallback:** any row the set cannot decide is **downgraded to `ACCEPTED-GAP`**, not argued
harder in prose. An undecidable equivalence claim is a gap with a nicer name.

### Spike — "Does `cosmic-ray baseline` write the module to disk?"

**Time box: 30 minutes. Runs in Task 8, before choosing the permanent Layer 2 guard.**

`cosmic-ray baseline CONFIG_FILE [--session-file FILE]` exists in 8.4.6 and "Exits with 0 if
the job has exited normally, otherwise 1". If it runs the test command against a clean,
unmutated tree then it would **not** have caught the O-B finalizer capture — a clean tree makes
the finalizer pass — which is worth knowing before anyone proposes it as the guard.

**Fallback:** do not use `baseline`. Use the survivor sentinel in Task 8, which discriminates
in the direction that matters: it requires a known mutant to **survive**, so an instrument that
kills everything fails it.

---

## Residual questions the diagnosis does not answer

The cause of the 100.00% is settled. Two questions about the *denominator* are not, and they
matter for the re-pin regardless of what caused the score:

1. **Was the mutant set ever re-scoped?** No tracked file records per-module job counts for any
   previous run, so the only comparison available is against the reconciliation's aggregate
   (1,118 jobs, 650 viable). Task 3's manifest makes per-module totals a tracked, diffable
   fact for the first time. **UNVERIFIED until Task 3 Step 6 runs.**
2. **Are the 468 excluded jobs INCOMPETENT or NO_TEST?** See the spike.

Record both in the diagnosis document with their verdicts; a question closed silently is a
question nobody answered.

---

## File structure

| File | Change | Responsibility |
|---|---|---|
| `tests/conftest.py` | Modify | O-B finalizer: snapshot at start, compare at end, non-destructive recovery advice |
| `tests/test_tree_cleanliness.py` | Modify | **The regression test for the O-B finalizer capture**, both directions |
| `tests/test_declared_mutations.py` | Modify | The inert-mutation guard: Layer 3's own anti-vacuity, extended to cover this |
| `docs/superpowers/specs/2026-08-02-ob-finalizer-capture.md` | Create | The episode: mechanism, three reproductions, timeline, what it cost, what caught it |
| `tests/test_ob_finalizer_capture_record.py` | Create | Guards that document: mechanism, both reproductions, and the two-sided-pin vindication |
| `scripts/check_suite_integrity.py` | Modify | Durable sessions, DB-derived counts, completeness + tree-fingerprint guards, `--layer`, sentinel, the Task 8 re-pin |
| `tests/test_suite_integrity_script.py` | Modify | Tests for each of the above |
| `scripts/triage_survivors.py` | Create | Reads session DBs → the survivor table's rows |
| `docs/superpowers/specs/2026-08-02-mutation-survivor-triage.md` | Create | **The committed survivor table.** The headline deliverable |
| `tests/test_survivor_triage_table.py` | Create | The table is complete, closed-vocabulary, and matches the manifest |
| `tests/test_survivor_triage_control.py` | Create | The control **on the triage**: mechanically re-executes every verdict |
| `pyproject.toml` | Modify | One new marker, `triage_control` |
| `.gitignore` | Modify | `.cosmic-ray-sessions/` |
| `docs/superpowers/specs/2026-08-01-ledger-reconciliation.md` | Modify | Two CANONICAL bullets replaced **in place** (Task 8) |

**Not touched by any task:** `cosmic-ray.toml`, `CORE_MODULES`, `[tool.coverage.run] omit`,
`scripts/gate_a.py`, any of the six core modules, `.github/workflows/ci.yml`'s job triggers,
any of the 15 registry entries.

---

### Task 1: Reproduce the capture as a committed regression test, then repair the finalizer

**Estimate: 2.5 h.** No cosmic-ray `exec` in this task.

**Files:**
- Modify: `tests/test_tree_cleanliness.py`
- Modify: `tests/conftest.py`

**Interfaces:**
- Consumes: nothing
- Produces: `tests.conftest.dirty_tracked_paths() -> list[str]`;
  `tests.conftest.newly_dirty(before: list[str], after: list[str]) -> list[str]`; a
  `_fail_if_the_suite_left_the_tree_dirty` fixture that fires only on dirt the session created

**Fixing the instance is not the deliverable; the guard is.** Without a test that fails on the
current `conftest.py`, this repair is one refactor away from coming back — and it came back
inside a control whose entire job was to prevent things coming back.

- [ ] **Step 1: Create the isolated worktree and verify it measures its own `src/`**

REQUIRED SUB-SKILL: `superpowers:using-git-worktrees`.

```bash
cd /c/Users/harsh/Downloads/Projects/Paper1
git rev-parse HEAD                      # record; expect 30eb333... unless main moved
git status --porcelain                  # must be empty before you start
git worktree add -b p1.5/mutation-survivor-triage ../Paper1-p15 HEAD
cd ../Paper1-p15
python -c "import sys; sys.path.insert(0,'src'); import tolcad, pathlib; print(pathlib.Path(tolcad.__file__).resolve())"
```

Expected: a path under `Paper1-p15/src/tolcad/`, **not** `Paper1/src/tolcad/`. The `tolcad`
editable install is a plain `.pth` path entry pointing at the main repo's `src` (verified:
`site-packages/__editable__.tolcad-0.1.0.pth` contains one path, not a finder module), and
`pyproject.toml`'s `pythonpath = ["src", "."]` puts the worktree's `src` ahead of it. If the
printed path is the main repo, STOP — every measurement in this plan would be against the
wrong tree. Fall back to `git clone --no-local` plus `pip install -e ".[dev,gen]"` in a fresh
venv, and record which you used.

All remaining steps and tasks run in `../Paper1-p15`.

- [ ] **Step 2: Write the failing test**

Append to `tests/test_tree_cleanliness.py`:

```python
def test_newly_dirty_ignores_dirt_that_predates_the_session():
    """THE REGRESSION TEST FOR THE O-B FINALIZER CAPTURE.

    O-B asks what THIS RUN left behind. The original finalizer asked whether the
    tree was dirty, which is a different question, and both mutation layers
    dirty the tree BEFORE launching their pytest subprocess:

      * cosmic-ray writes the mutant to src/ then runs the test command, and
        reads a non-zero exit as "mutant killed" -- so every mutant died and
        Layer 2 reported 100.00%;
      * run_declared_mutation writes the declared mutation then calls
        _target_test_passes, so every expect="fail" entry passed whether or not
        its guard could detect anything.

    A control silently disabled two other controls. See
    docs/superpowers/specs/2026-08-02-ob-finalizer-capture.md.
    """
    from tests.conftest import newly_dirty

    assert newly_dirty([" M src/tolcad/types.py"], [" M src/tolcad/types.py"]) == []


def test_newly_dirty_still_reports_dirt_the_session_created():
    """The case the finalizer exists for: a declared mutation that did not restore."""
    from tests.conftest import newly_dirty

    assert newly_dirty([], [" M src/tolcad/reliability.py"]) == [
        " M src/tolcad/reliability.py"
    ]


def test_pre_existing_dirt_does_not_amnesty_everything_else():
    from tests.conftest import newly_dirty

    before = [" M src/tolcad/types.py"]
    after = [" M src/tolcad/types.py", " M src/tolcad/iso286.py"]
    assert newly_dirty(before, after) == [" M src/tolcad/iso286.py"]


def test_a_session_that_starts_dirty_and_ends_dirty_exits_zero():
    """End to end, in a real subprocess, against a genuinely dirty tree.

    Uses an UNTRACKED file under src/ rather than editing a tracked one: git
    status reports it as '??', the finalizer sees it, and nothing tracked is
    ever modified. Do not "improve" this by editing a core module.
    """
    probe = REPO / "src" / "tolcad" / "_p15_probe.py"
    probe.write_text("# transient probe; see test_tree_cleanliness.py\n", encoding="utf-8")
    try:
        assert _dirty_tracked_paths(), "the probe did not dirty the tree"
        proc = subprocess.run(
            [
                sys.executable, "-m", "pytest", "tests/test_types.py",
                "-q", "--no-header", "-p", "no:cacheprovider",
            ],
            cwd=REPO, capture_output=True, text=True,
        )
        assert proc.returncode == 0, (
            "a session whose tree was ALREADY dirty when it started must not "
            "fail. This exact failure is what made every cosmic-ray mutant "
            "'die' and every declared mutation 'succeed'.\n" + proc.stdout[-3000:]
        )
    finally:
        probe.unlink(missing_ok=True)
    assert not _dirty_tracked_paths()


def test_an_inert_declared_mutation_is_rejected():
    """Layer 3's own anti-vacuity, extended to cover the capture.

    A comment cannot change behaviour, so an expect="fail" entry that only adds
    a comment MUST fail. Under the captured finalizer it passed -- measured, in
    a clone, on 2026-08-02. This is the guard that keeps Layer 3 honest: it
    proves the runner can still tell a detected mutation from an undetectable
    one.

    Lives here rather than in test_declared_mutations.py only if that module is
    unavailable; prefer test_declared_mutations.py, which owns the runner. See
    Task 1 Step 5.
    """
```

Then put the real body of that last test in `tests/test_declared_mutations.py`, where the
runner's other anti-vacuity guards live, and delete the stub above:

```python
def test_a_semantically_inert_mutation_is_rejected():
    """A comment cannot change behaviour, so this experiment MUST fail.

    THE O-B FINALIZER CAPTURE, guarded. From d7285f9 until 2026-08-02 the
    session-scoped tree-cleanliness finalizer failed every pytest run whose tree
    was dirty -- and run_declared_mutation dirties the tree by design before
    calling _target_test_passes. So _target_test_passes returned False for every
    mutation, and all thirteen expect="fail" entries targeting src/ or
    tests/fixtures/ passed WITHOUT their guards being exercised at all.
    Measured in a clone: this exact probe passed. It must not.
    """
    inert = DeclaredMutation(
        name="inert-comment-probe",
        target="src/tolcad/types.py",
        find="    detail: dict = field(default_factory=dict)",
        replace=(
            "    detail: dict = field(default_factory=dict)"
            "  # INERT PROBE, no test can see this"
        ),
        test="tests/test_types.py::test_verdict_is_immutable",
        expect="fail",
        why="fixture for the runner's own guard; see the O-B finalizer capture",
    )
    with pytest.raises(AssertionError, match="still PASSED"):
        run_declared_mutation(inert)
```

The anchor `    detail: dict = field(default_factory=dict)` and the test node ID
`tests/test_types.py::test_verdict_is_immutable` were both verified to exist and to be unique
at `30eb333`. If the anchor count changes, find another unique inert site rather than deleting
the guard.

- [ ] **Step 3: Run the tests and watch them fail**

```bash
python -m pytest tests/test_tree_cleanliness.py -v
python -m pytest tests/test_declared_mutations.py -v -k inert
```

Expected, and this is the point of the step:
- the three `newly_dirty` tests fail with `ImportError: cannot import name 'newly_dirty'`;
- `test_a_session_that_starts_dirty_and_ends_dirty_exits_zero` fails on `proc.returncode == 0`;
- `test_a_semantically_inert_mutation_is_rejected` fails with `DID NOT RAISE <class 'AssertionError'>`
  — **that failure is the captured Layer 3, reproduced in the repository's own suite.**

Paste all three failures into the Task 1 report. They are the evidence that the fix fixes
something.

- [ ] **Step 4: Repair the finalizer**

Replace `tests/conftest.py` entirely:

```python
"""Session-scoped tree-cleanliness finalizer (O-B). See tests/test_tree_cleanliness.py.

WHAT CHANGED ON 2026-08-02, AND WHY -- "the O-B finalizer capture".

This finalizer used to fail the session if `git status --porcelain src/
tests/fixtures/` was non-empty at teardown. That asks "is the tree dirty?", but
O-B's question is "did THIS RUN leave the tree dirty?" -- a different question,
answered wrongly whenever the tree was already dirty when the session began.

Both mutation layers dirty the tree before launching a pytest subprocess, so
both were silently disabled from d7285f9 until this commit:

  * cosmic-ray writes the mutant to src/tolcad/<module>.py, runs the test
    command, and reads a non-zero exit code as "mutant killed". Every mutant
    therefore died and Layer 2 reported 100.00% while measuring nothing.
  * run_declared_mutation writes the declared mutation, then calls
    _target_test_passes, which returns `returncode == 0`. Every expect="fail"
    entry targeting src/ or tests/fixtures/ -- thirteen of the fifteen -- passed
    without its guard being exercised.

A control silently disabled two other controls, and read green throughout. The
two-sided mutation pin is what caught it; a one-sided floor would have read
100.00 >= 93.35 and stayed green forever. Full record:
docs/superpowers/specs/2026-08-02-ob-finalizer-capture.md.

THE FIX IS A SNAPSHOT, NOT AN EXEMPTION. An env-var or lock-file exemption for
"a mutation tool is running" would be an opt-out on the control that catches a
corrupted working tree, which design spec section 6 rules out, and it could not
tell a live mutant from a leftover one. The snapshot loses nothing: a declared
mutation that fails to restore is clean at the start and dirty at the end, which
is exactly the case this control exists for. Cost: one extra `git status` per
session, about 50 ms.
"""

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent

# src/ is what the mutation layers corrupt; tests/fixtures/ holds the .stp
# mutation target. Watching the fixtures DIRECTORY also covers
# NIST-PROVENANCE.md, which is not a mutation target -- that is deliberate (a
# fixture directory left modified is worth knowing about either way) and is why
# the recovery advice below is scoped to the offending paths rather than to the
# whole directory.
_WATCHED = ("src/", "tests/fixtures/")


def dirty_tracked_paths() -> list[str]:
    """Porcelain lines for the watched paths. Empty means clean."""
    proc = subprocess.run(
        ["git", "status", "--porcelain", *_WATCHED],
        cwd=REPO, capture_output=True, text=True,
    )
    return [line for line in proc.stdout.splitlines() if line.strip()]


def newly_dirty(before: list[str], after: list[str]) -> list[str]:
    """Porcelain lines present at teardown that were not present at setup.

    Order-preserving on `after`, so the message reads in git's own order. A line
    whose status CHANGED (e.g. '?? x' becoming ' M x') counts as new: O-B would
    rather over-report than miss a corrupted working tree.
    """
    seen = set(before)
    return [line for line in after if line not in seen]


def _recovery_advice(dirty: list[str]) -> str:
    """Name only the offending paths.

    The previous message said `git checkout -- src/ tests/fixtures/`
    unconditionally. tests/fixtures/ holds exactly two files: the .stp mutation
    target and NIST-PROVENANCE.md. An operator who edited the documentation file
    and ran the suite was told to run a command that destroys their work.
    """
    paths = [line[3:].strip() for line in dirty]
    return "git checkout -- " + " ".join(f'"{p}"' for p in paths)


@pytest.fixture(scope="session", autouse=True)
def _fail_if_the_suite_left_the_tree_dirty():
    before = dirty_tracked_paths()
    yield
    dirty = newly_dirty(before, dirty_tracked_paths())
    if dirty:
        pytest.fail(
            "THE SUITE LEFT TRACKED FILES MODIFIED. A declared mutation did not "
            "restore. Check mutation_registry.run_declared_mutation, then "
            "restore ONLY these paths with:\n"
            f"  {_recovery_advice(dirty)}\n" + "\n".join(dirty),
            pytrace=False,
        )
```

The leading sentence `THE SUITE LEFT TRACKED FILES MODIFIED.` is unchanged on purpose: it is
quoted in the reproduction transcripts and in `tests/test_ob_finalizer_capture_record.py`.

- [ ] **Step 5: Run the tests to verify they pass**

```bash
python -m pytest tests/test_tree_cleanliness.py -v
python -m pytest tests/test_declared_mutations.py -v
python -m pytest -q
python -m pytest tests/gen/test_ladder_pin.py -q
python scripts/gate_a.py > /dev/null 2>&1; echo "gate_a exit: $?"
git status --porcelain
```

Expected: all green; full suite passes (baseline **428 passed** plus the tests added here —
report the actual number and the added wall-clock time); ladder unchanged; Gate A exits **1**;
tree clean. Capture the exit code without a pipe.

`test_the_tree_is_clean_right_now` still asserts *absolute* cleanliness and must still pass —
the snapshot changed the finalizer, not that test. Confirm it was not weakened.

**Measured reference, from the clone probe on 2026-08-02:** with this `conftest.py`,
`tests/test_declared_mutations.py` runs `15 passed, 14 deselected in 27.73 s` for the
parametrised registry entries. If your run reports a registry FAILURE, that is a **finding**,
not a plan bug — a guard that does not guard. Stop and report it before continuing.

- [ ] **Step 6: Commit**

```bash
git add tests/conftest.py tests/test_tree_cleanliness.py tests/test_declared_mutations.py
git commit -m "fix: O-B reports only the dirt the session created, unblocking Layers 2 and 3"
```

---

### Task 2: Re-verify Layer 3 honestly and record the episode

**Estimate: 1.5 h.**

**Files:**
- Create: `docs/superpowers/specs/2026-08-02-ob-finalizer-capture.md`
- Create: `tests/test_ob_finalizer_capture_record.py`

**Interfaces:**
- Consumes: the repaired finalizer from Task 1
- Produces: the episode record, cited by `tests/conftest.py`,
  `scripts/check_suite_integrity.py` and both triage documents

Layer 3 was vacuous for thirteen of fifteen entries. Task 1 restored the mechanism; this task
produces the **evidence** — which is what was actually lost — and writes down what happened so
the next person does not have to rediscover it from a git log.

- [ ] **Step 1: Execute all fifteen entries honestly and record the result**

```bash
python -m pytest tests/test_declared_mutations.py -v -k "behaves_as_declared" \
  > /tmp/p15-layer3.txt 2>&1
echo "exit: $?"
cat /tmp/p15-layer3.txt
```

Expected: 15 passed. Record the full list with per-entry PASSED/FAILED. Then classify each of
the fifteen by whether the finalizer had captured it:

- **Captured** (target under `src/` or `tests/fixtures/`, `expect="fail"`) — 13 entries:
  `it7-row-transposed`, `zeroed-wall-margin`, `it-grade-set-widened`, `flat-difficulty-ladder`,
  `ladder-d2-row-shifted`, `crlf-corrupted-nist-fixture`, `m12-clearance-diameter`,
  `fastener-upper-dev-nonzero`, `reliability-perturbation-neutered`,
  `reliability-perturbation-tripled`, `tapped-hole-upper-dev-nonzero`,
  `y14-5-worked-example-boundary-shifted`, `case-sensitive-guard-uppercased`.
- **Never captured** — 2 entries: `stale-literal-wall-floor` (targets
  `tests/gen/test_layout.py`, outside the watched paths) and `mc-seed-base-shifted` (targets
  `tests/gen/test_features.py`, outside the watched paths, and is the sole `expect="pass"`
  entry, which the capture would have made *fail* rather than pass — a useful cross-check that
  the mechanism is understood correctly).

Verify that classification against the current `_WATCHED` tuple rather than trusting the list.

- [ ] **Step 2: Identify the four entries that had never been executed honestly**

```bash
git diff d7285f9..HEAD -- tests/mutation_registry.py | grep -E "^\+\s+name="
```

Expected output names exactly four entries: `ladder-d2-row-shifted`,
`tapped-hole-upper-dev-nonzero`, `y14-5-worked-example-boundary-shifted`,
`case-sensitive-guard-uppercased`. Every one was added after the finalizer existed, so none
was ever watched failing until Step 1. The other nine captured entries were watched failing on
the `feat/suite-integrity` branch before `d7285f9`, so they have historical evidence as well
as Step 1's.

- [ ] **Step 3: Write the failing test**

Create `tests/test_ob_finalizer_capture_record.py`:

```python
"""The O-B finalizer capture must be recorded where a clone can read it.

Ten of the project's historical instances were found by an adversarial reader
over a diff, and none by the three-layer machinery. This one was found by a
two-sided pin -- the first time a layer caught anything -- and the reasoning
that produced the fix is worth more than the fix. A record that lives in a
transcript is the *Unencoded* shape from the design spec's own taxonomy.
"""

import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DOC = (
    REPO_ROOT / "docs" / "superpowers" / "specs"
    / "2026-08-02-ob-finalizer-capture.md"
)


def _text() -> str:
    assert DOC.is_file(), (
        f"{DOC} does not exist. The record of the capture exists only in a "
        f"transcript, which is the Unencoded defect shape this repository has "
        f"already shipped twice."
    )
    return DOC.read_text(encoding="utf-8")


def test_the_record_is_committed():
    assert DOC.is_file()


def test_it_names_both_captured_layers():
    text = _text()
    assert "Layer 2" in text and "Layer 3" in text, (
        "one control disabled TWO others; a record naming only the mutation "
        "score understates it"
    )


def test_it_records_the_reproduction_not_just_the_conclusion():
    text = _text()
    assert "THE SUITE LEFT TRACKED FILES MODIFIED" in text, (
        "quote the failure message, so a reader can tell the test command "
        "failed for the tree's state rather than for the mutant"
    )
    assert "inert" in text.lower(), (
        "the Layer 3 reproduction is the inert-comment probe; name it"
    )


def test_it_records_the_two_sided_pin_vindication():
    """The strongest evidence the project has for the two-sided-pin rule."""
    text = _text()
    assert "two-sided" in text.lower()
    assert re.search(r"one-sided", text, re.IGNORECASE), (
        "state what a one-sided floor would have done: read 100.00 >= 93.35 and "
        "stayed green"
    )


def test_it_does_not_mint_a_new_instance_ordinal():
    """The reconciliation fixes the count at twelve, BY NAME, and supersedes the
    ordinals 'thirteenth' and 'fifteenth' as a numbering scheme. Inventing a new
    one would be, in its own words, the same defect in a new coat."""
    text = _text().lower()
    for ordinal in ("thirteenth instance", "instance 13", "instance thirteen"):
        assert ordinal not in text, (
            f"{ordinal!r} mints a new ordinal; refer to this by name -- 'the "
            f"O-B finalizer capture' -- per the ledger reconciliation's "
            f"'instance count' section"
        )


@pytest.mark.parametrize(
    "entry",
    [
        "ladder-d2-row-shifted",
        "tapped-hole-upper-dev-nonzero",
        "y14-5-worked-example-boundary-shifted",
        "case-sensitive-guard-uppercased",
    ],
)
def test_it_names_every_entry_that_was_never_executed_honestly(entry):
    """These four were added after d7285f9, so no honest run of them existed
    until 2026-08-02. A guard that has never been watched failing is exactly
    what the registry exists to prevent."""
    assert entry in _text()
```

- [ ] **Step 4: Run the test to verify it fails**

Run: `python -m pytest tests/test_ob_finalizer_capture_record.py -v`
Expected: FAIL — the document does not exist; every test reports the "Unencoded defect shape"
message.

- [ ] **Step 5: Write the record**

Create `docs/superpowers/specs/2026-08-02-ob-finalizer-capture.md`. Required contents:

- **The name and the shape.** "The O-B finalizer capture: a control silently disabled two
  other controls." A paragraph stating explicitly that **no new ordinal is minted**, citing the
  reconciliation's *instance count* section for the rule and the canonical count of twelve.
- **The mechanism**, in one paragraph per layer, as summarised at the top of this plan.
- **The three reproductions**, verbatim: the coordinator's cosmic-ray-shape transcript
  (including `THE SUITE LEFT TRACKED FILES MODIFIED` and `EXIT=1`), the inert-comment probe
  before the fix, and the same probe plus the `15 passed` registry run after the fix.
- **The timeline**: `d7285f9` created the finalizer and is an ancestor of both `062316e` and
  `05d4dae`; the 95.89 measurement predates it (`0e046ac` at 18:12:57 already quotes it);
  therefore 95.89 is very likely the last real Layer 2 number. Cite the reconciliation's
  *mutation score* section rather than restating figures.
- **What it cost**: Layer 2 measured nothing from `d7285f9`; Layer 3's thirteen captured
  entries passed without exercising their guards; four entries — named — had never been
  executed honestly at all. **And what it did not cost**: all fifteen entries pass under the
  repaired finalizer, so the guards themselves are sound and no registry entry needs changing.
  Say both, in that order.
- **The vindication**: the two-sided pin caught it on its first real encounter; a one-sided
  floor would have read `100.00 >= 93.35` and stayed green through pre-registration.
- **The second symptom**: editing `tests/fixtures/NIST-PROVENANCE.md` also tripped the
  finalizer, and the recovery advice would have destroyed the edit. Record it as the symptom
  that showed the defect was about *before-versus-after*, not about mutation tools.
- **The fix and the rejected alternatives**, reproducing this plan's decision table.
- **The residual questions** (mis-scoping, and the 468), each with its owning task or spike,
  cross-referenced to `docs/SPIKES.md` by spike title.

- [ ] **Step 6: Run the tests to verify they pass**

```bash
python -m pytest tests/test_ob_finalizer_capture_record.py -v
python -m pytest -q
git status --porcelain
```

- [ ] **Step 7: Commit**

```bash
git add docs/superpowers/specs/2026-08-02-ob-finalizer-capture.md \
        tests/test_ob_finalizer_capture_record.py
git commit -m "docs: record the O-B finalizer capture and re-verify all fifteen declared mutations"
```

---

### Task 3: Make Layer 2 enumerable, and take the first honest measurement

**Estimate: 2.5 h, of which ~25 min is an unattended run. Contains a spike.**

**Files:**
- Modify: `scripts/check_suite_integrity.py`
- Modify: `tests/test_suite_integrity_script.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: nothing from Tasks 1–2 beyond a working finalizer
- Produces:
  - `SESSIONS_DIR: Path` = `REPO_ROOT / ".cosmic-ray-sessions"`
  - `count_outcomes(session_path: Path) -> dict[str, int]` with keys exactly
    `{"total", "complete", "survived", "killed", "incompetent", "no_test"}`
  - `assert_complete(counts: dict[str, int], module: str) -> None`
  - `tree_fingerprint() -> str` — `f"{sha}:{digest16}"`
  - `write_manifest(path: Path, per_module: dict[str, dict[str, int]], before: str, after: str) -> None`
  - `main` gains `--layer {coverage,mutation,both}` (default `both`) and `--sessions-dir PATH`

**Three defects, all of which must be fixed before any number is trusted.**

1. **Sessions are destroyed.** `run_mutation_score` builds them in a
   `tempfile.TemporaryDirectory()`. No survivor can be enumerated from a run that deletes its
   own evidence — mechanically, this is why every survivor figure since run 3 is arithmetic
   over a score.
2. **Completeness is never checked.** `total` comes from `db.num_work_items` (every job) while
   `surviving mutants` is computed over `db.num_results` (completed only). A partial run puts
   uncounted jobs in the killed bucket and inflates the score — toward 100%, the direction that
   already burned this project once.
3. **The denominator is parsed out of prose.** `report.count("TestOutcome.INCOMPETENT")` cannot
   see `test outcome: None` (`WorkerOutcome.NO_TEST`). See the spike.

- [ ] **Step 1: Run the spike — "What the 468 non-viable Layer 2 jobs actually are"**

**Time box 45 minutes.** `types.py` is 80 lines and took 28 s for 66 mutants in the original
spike, so this is minutes.

```bash
mkdir -p .cosmic-ray-sessions
python - <<'PY'
import pathlib, tomllib
cfg = tomllib.loads(pathlib.Path("cosmic-ray.toml").read_text(encoding="utf-8"))
pathlib.Path(".cosmic-ray-sessions/spike-types.toml").write_text(
    "[cosmic-ray]\n"
    'module-path = "src/tolcad/types.py"\n'
    f"timeout = {cfg['cosmic-ray']['timeout']}\n"
    "excluded-modules = []\n"
    f"test-command = \"{cfg['cosmic-ray']['test-command']}\"\n"
    '\n[cosmic-ray.distributor]\nname = "local"\n',
    encoding="utf-8",
)
PY
cosmic-ray init .cosmic-ray-sessions/spike-types.toml .cosmic-ray-sessions/spike-types.sqlite
cosmic-ray exec .cosmic-ray-sessions/spike-types.toml .cosmic-ray-sessions/spike-types.sqlite
python - <<'PY'
import collections
from cosmic_ray.work_db import WorkDB, use_db
with use_db(".cosmic-ray-sessions/spike-types.sqlite", WorkDB.Mode.open) as db:
    tally = collections.Counter(
        (str(r.worker_outcome), str(r.test_outcome)) for _, r in db.results
    )
    print("num_work_items:", db.num_work_items, "num_results:", db.num_results)
    for pair, n in sorted(tally.items()):
        print(f"{n:5d}  worker={pair[0]:<26} test={pair[1]}")
PY
```

**Sanity check while you are here:** on the repaired tree this session should report a
*non-zero* number of `test=TestOutcome.SURVIVED` rows. If it reports zero survivors on
`types.py`, the finalizer repair did not take — the original spike measured **5 survivors of
66** on this module. Stop and re-check Task 1.

**What the tally decides:** if any row shows `test=None`, the prose-parsing denominator
under-counts. **Fallback:** Step 4's `count_outcomes` reads the DB anyway — adopt it, and state
both the old and new denominator in Task 8's reconciliation amendment.

Append the tally to the capture record as a dated section; do not rewrite Task 2's text.

- [ ] **Step 2: Write the failing test**

Append to `tests/test_suite_integrity_script.py` (add `import pytest` if absent):

```python
def test_sessions_are_durable_not_thrown_away():
    """A run that deletes its own evidence cannot produce a survivor list.

    Every survivor figure recorded since run 3 is arithmetic over a score
    rather than an enumeration, and this is the mechanical reason: sessions
    lived in a TemporaryDirectory. See the 'untriaged survivors' section of
    docs/superpowers/specs/2026-08-01-ledger-reconciliation.md.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    assert mod.SESSIONS_DIR == REPO / ".cosmic-ray-sessions"
    src = (REPO / "scripts" / "check_suite_integrity.py").read_text(encoding="utf-8")
    assert "TemporaryDirectory" not in src, (
        "session databases must outlive the run; they ARE the enumeration"
    )


def test_counts_come_from_the_session_database_not_from_report_prose():
    """cr-report prints 'test outcome: None' for NO_TEST jobs, invisible to a
    text search for 'TestOutcome.INCOMPETENT', while WorkResult.is_killed
    (test_outcome != SURVIVED) counts them as killed. Parsing prose put an
    unknown number of jobs in the wrong bucket of the denominator every pin has
    been computed over."""
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    assert callable(mod.count_outcomes)
    src = (REPO / "scripts" / "check_suite_integrity.py").read_text(encoding="utf-8")
    assert 'report.count("TestOutcome.INCOMPETENT")' not in src


def test_an_incomplete_run_is_refused_rather_than_scored():
    """Uncounted jobs land in the killed bucket, so a partial run inflates the
    score toward 100% -- the direction that already produced a fake perfect."""
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    with pytest.raises(RuntimeError, match="complete"):
        mod.assert_complete(
            {"total": 650, "complete": 649, "survived": 0,
             "killed": 649, "incompetent": 0, "no_test": 0},
            "types",
        )
    mod.assert_complete(
        {"total": 650, "complete": 650, "survived": 27,
         "killed": 623, "incompetent": 0, "no_test": 0},
        "types",
    )


def test_the_tree_fingerprint_is_stable_and_names_a_commit():
    """A run whose tree moved underneath it is not a measurement of either tree."""
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    first = mod.tree_fingerprint()
    assert ":" in first and len(first.split(":")[0]) >= 7
    assert mod.tree_fingerprint() == first
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python -m pytest tests/test_suite_integrity_script.py -v -k "durable or database or incomplete or fingerprint"`
Expected: FAIL — `AttributeError: module 'check_suite_integrity' has no attribute 'SESSIONS_DIR'`
and friends.

- [ ] **Step 4: Implement**

In `scripts/check_suite_integrity.py`, drop the now-unused `tempfile` import and add:

```python
import hashlib
import json

from cosmic_ray.work_db import WorkDB, use_db

# Sessions OUTLIVE the run. They ARE the enumeration: a survivor list cannot be
# produced from a run that deletes its own evidence, which is mechanically why
# every survivor figure since run 3 has been arithmetic over a score.
# Gitignored -- regenerable, ~25 min.
SESSIONS_DIR = REPO_ROOT / ".cosmic-ray-sessions"

_OUTCOME_KEYS = ("total", "complete", "survived", "killed", "incompetent", "no_test")


def count_outcomes(session_path: Path) -> dict[str, int]:
    """Tally one session directly from its database, not from cr-report's text.

    cr-report prints `test outcome: None` for jobs whose worker outcome is
    NO_TEST (no mutation was possible at that occurrence), so a text search for
    "TestOutcome.INCOMPETENT" cannot see them -- while WorkResult.is_killed,
    which is `test_outcome != SURVIVED`, counts them as killed. Parsing prose
    put an unknown number of jobs in the wrong bucket of the denominator every
    pin has been computed over.
    """
    from cosmic_ray.work_item import TestOutcome, WorkerOutcome

    counts = dict.fromkeys(_OUTCOME_KEYS, 0)
    with use_db(str(session_path), WorkDB.Mode.open) as db:
        counts["total"] = db.num_work_items
        counts["complete"] = db.num_results
        for _job_id, result in db.results:
            if result.worker_outcome == WorkerOutcome.NO_TEST:
                counts["no_test"] += 1
            elif result.test_outcome == TestOutcome.SURVIVED:
                counts["survived"] += 1
            elif result.test_outcome == TestOutcome.INCOMPETENT:
                counts["incompetent"] += 1
            else:
                counts["killed"] += 1
    return counts


def assert_complete(counts: dict[str, int], module: str) -> None:
    """Refuse to score a run that did not finish.

    `total` is every job; `complete` is every job with a result. The old
    arithmetic subtracted survivors from `total`, so any unfinished job was
    silently counted as killed and the score was inflated -- toward 100%.
    """
    if counts["complete"] != counts["total"]:
        raise RuntimeError(
            f"{module}: {counts['complete']} of {counts['total']} jobs complete. "
            f"Refusing to report a score over an unfinished run -- the missing "
            f"jobs would be counted as killed. Re-run `cosmic-ray exec` on the "
            f"SAME session file to finish the remaining work, and check the "
            f"tree fingerprint has not moved in the meantime."
        )


def tree_fingerprint() -> str:
    """`<HEAD sha>:<16 hex of sha256 over git status --porcelain src/ tests/>`.

    Editing src/ invalidates a run because src/ is what is mutated; editing
    tests/ invalidates it because tests/ IS the test command. Comparing this
    before and after an exec is what makes an interrupted-and-resumed run safe:
    a resumed run whose fingerprint moved is two half-measurements of two
    different trees.
    """
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    porcelain = subprocess.run(
        ["git", "status", "--porcelain", "src/", "tests/"], cwd=REPO_ROOT,
        capture_output=True, text=True, check=True,
    ).stdout
    return f"{sha}:{hashlib.sha256(porcelain.encode('utf-8')).hexdigest()[:16]}"


def write_manifest(
    path: Path,
    per_module: dict[str, dict[str, int]],
    before: str,
    after: str,
) -> None:
    """Record what was measured, over which tree, with which per-module counts.

    The per-module `total` figures are the fingerprint that detects a SCOPE
    change. Layer 1 made this mistake once already: 48.0 vs 94.74 was a scope
    difference read as drift (ledger reconciliation, 'branch coverage'). With
    per-module totals recorded, the same mistake in Layer 2 shows up in a diff
    instead of hiding in an aggregate.
    """
    path.write_text(
        json.dumps(
            {
                "tree_fingerprint_before": before,
                "tree_fingerprint_after": after,
                "core_modules": list(CORE_MODULES),
                "per_module": per_module,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
```

Rewrite `_mutate_one_module` to write its generated config and its session into `SESSIONS_DIR`
(`SESSIONS_DIR.mkdir(parents=True, exist_ok=True)`), keep the `cosmic-ray init` and
`cosmic-ray exec` subprocess calls exactly as they are, and return `count_outcomes(session)`
instead of the three-tuple. Delete the `cr-report` subprocess call and the `_count` helper.

Rewrite `run_mutation_score` to:
1. keep the `shutil.which("cosmic-ray")` guard verbatim — unavailable is a failure, never a
   skip;
2. `before = tree_fingerprint()`;
3. loop `CORE_MODULES`, calling `_mutate_one_module` then `assert_complete`;
4. `after = tree_fingerprint()`; raise `RuntimeError` naming both values if they differ;
5. aggregate `denominator = total - incompetent - no_test`, `killed = denominator - survived`,
   `score = 100.0 * killed / denominator`, keeping the `denominator <= 0` guard;
6. `write_manifest(SESSIONS_DIR / "run-manifest.json", ...)`;
7. return `check_two_sided(score, MUTATION_MEASURED, MUTATION_TOLERANCE)` unchanged.

Add `--layer {coverage,mutation,both}` and `--sessions-dir PATH` to `main`, keeping
`_refuse_if_a_mutation_is_in_flight()` as the **first** statement and `--self-test-failure`
unchanged. `--layer` exists so later tasks can re-read a session or re-check coverage without
paying 25 minutes; it must default to `both` so the CI invocation
(`python scripts/check_suite_integrity.py`, no arguments) is unaffected.

Add to `.gitignore` under the existing suite-integrity block:

```
.cosmic-ray-sessions/
```

- [ ] **Step 5: Run the unit tests**

```bash
python -m pytest tests/test_suite_integrity_script.py -v
python -m pytest -q
```
Expected: all pass. **Do not run the full script yet.**

- [ ] **Step 6: Take the first honest measurement since `d7285f9`**

Nothing else may run on this machine for the next half hour.

```bash
ls .mutation-in-progress 2>/dev/null && echo "LOCK PRESENT -- follow the printed recovery procedure"
git status --porcelain            # must be empty
git rev-parse HEAD                # record this SHA
python scripts/check_suite_integrity.py > .cosmic-ray-sessions/run-1.log 2>&1
echo "integrity exit: $?"
tail -20 .cosmic-ray-sessions/run-1.log
cat .cosmic-ray-sessions/run-manifest.json
```

Exit **2** = the lock is held; a refusal, not a measurement. Exit **1** is the expected
outcome: the honest score will not be 100.00 and, if it is not within 0.50 of 95.89, the
two-sided pin will say so. Exit **0** would mean the tree landed back within tolerance of
95.89, which is plausible given that neither the six core modules nor their six test files
changed between `062316e` and `HEAD` — verify that claim yourself with:

```bash
git diff --name-only 062316e..HEAD -- \
  src/tolcad/types.py src/tolcad/y14_5.py src/tolcad/iso286.py \
  src/tolcad/montecarlo.py src/tolcad/checker.py src/tolcad/reliability.py \
  tests/test_types.py tests/test_y14_5.py tests/test_iso286.py \
  tests/test_montecarlo.py tests/test_checker.py tests/test_reliability.py
```

Expected: empty. If run 1's score is close to 95.89 that is corroboration; if it is far from
it, that is a **second finding** and needs its own explanation before Task 8 pins anything.

Append to the capture record, as a dated section: the score, the aggregate counts, the six
per-module `total` figures, the wall-clock time, and both tree fingerprints. Then **close
residual question 1**: compare the aggregate total against the reconciliation's 1,118 jobs /
650 viable and record whether the mutant set was ever re-scoped.

- [ ] **Step 7: Commit**

```bash
git add scripts/check_suite_integrity.py tests/test_suite_integrity_script.py .gitignore \
        docs/superpowers/specs/2026-08-02-ob-finalizer-capture.md
git commit -m "feat: durable Layer 2 sessions, DB-derived counts, completeness and tree-fingerprint guards"
```

---

### Task 4: Enumerate every survivor into a committed table

**Estimate: 2 h.**

**Files:**
- Create: `scripts/triage_survivors.py`
- Create: `docs/superpowers/specs/2026-08-02-mutation-survivor-triage.md`
- Create: `tests/test_survivor_triage_table.py`

**Interfaces:**
- Consumes: `SESSIONS_DIR` from Task 3
- Produces:
  - `enumerate_survivors(sessions_dir: Path) -> list[dict]` with keys
    `{"module", "operator", "occurrence", "start_pos", "job_id"}`
  - `render_rows(survivors: list[dict]) -> str` — markdown body rows, verdict pre-filled
    `PENDING`
  - the committed table

**This task produces a list, not a judgement.** Task 5 judges. They are split because an
enumeration can be checked against the manifest and a judgement cannot, so they need different
guards and different review gates.

**The output is a committed table, not a shell run.** A triage performed in a terminal and
reported in prose is the *Unencoded* shape, which this repository has already shipped twice —
and it is why the survivor count has been unknown since run 3.

- [ ] **Step 1: Write the failing test**

Create `tests/test_survivor_triage_table.py`:

```python
"""The survivor triage must be a committed table that matches the run it came from.

Two failures this guards, both of which have already happened here:

1. An UNCOMMITTED triage -- performed in a shell, reported in prose, gone with
   the session. That is the *Unencoded* shape, and it is why the untriaged
   survivor count has been unknown since run 3 (ledger reconciliation,
   'untriaged survivors').
2. A triage that does not match its run. Fewer rows than measured survivors
   means some survivor was never looked at, and "every survivor was triaged"
   becomes a claim rather than a fact.
"""

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DOC = (
    REPO_ROOT / "docs" / "superpowers" / "specs"
    / "2026-08-02-mutation-survivor-triage.md"
)
MANIFEST_FIELD = "Survivors measured:"

# Closed vocabulary. Task 5 removes PENDING; until then a row may be un-judged,
# but it may not be missing.
ALLOWED_VERDICTS = {"KILLED-BY-NEW-TEST", "EQUIVALENT", "ACCEPTED-GAP", "PENDING"}

CORE_MODULE_PATHS = {
    f"src/tolcad/{m}.py"
    for m in ("types", "y14_5", "iso286", "montecarlo", "checker", "reliability")
}


def _text() -> str:
    assert DOC.is_file(), (
        f"{DOC} does not exist. A survivor triage that is not committed is the "
        f"Unencoded defect shape, and it is why the survivor count has been "
        f"unknown since run 3."
    )
    return DOC.read_text(encoding="utf-8")


def _rows() -> list[list[str]]:
    """Body rows of the survivor table: exactly six pipe-separated cells."""
    rows = []
    for line in _text().splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 6:
            continue
        if not cells[0] or set(cells[0]) <= set("-: "):
            continue
        if cells[0].lower() == "module":
            continue
        rows.append(cells)
    return rows


def test_the_table_is_committed():
    assert DOC.is_file()


def test_the_table_records_the_tree_it_was_measured_over():
    text = _text()
    assert re.search(r"^Base commit:\s*[0-9a-f]{7,40}\s*$", text, re.MULTILINE), (
        "a survivor list is only meaningful against a stated tree"
    )
    assert re.search(rf"^{re.escape(MANIFEST_FIELD)}\s*\d+\s*$", text, re.MULTILINE), (
        f"the document must carry `{MANIFEST_FIELD} <n>`, copied from the run "
        f"manifest"
    )


def test_every_survivor_in_the_run_has_a_row():
    """Arithmetic over a score is not an enumeration. Count the rows."""
    text = _text()
    declared = int(
        re.search(rf"^{re.escape(MANIFEST_FIELD)}\s*(\d+)\s*$", text, re.MULTILINE).group(1)
    )
    rows = _rows()
    assert len(rows) == declared, (
        f"the table has {len(rows)} rows for {declared} measured survivors. A "
        f"missing row is a survivor nobody looked at."
    )
    assert declared > 0 or "ZERO SURVIVORS" in text, (
        "a survivor count of zero is exactly the shape this project's history "
        "says to scrutinise -- it is what the O-B finalizer capture produced. "
        "If it is real, say so explicitly and show the evidence."
    )


def test_every_row_carries_a_verdict_from_the_closed_set():
    for cells in _rows():
        module, operator, occurrence, verdict, _evidence, _why = cells
        assert verdict in ALLOWED_VERDICTS, (
            f"{module}/{operator}/{occurrence}: verdict {verdict!r} is not one "
            f"of {sorted(ALLOWED_VERDICTS)}. Free-text verdicts are how nine "
            f"mutants got mislabelled in SI-4."
        )


def test_every_row_identifies_a_mutant_precisely_enough_to_reapply():
    """module + operator + occurrence is exactly what `cosmic-ray apply` takes."""
    for cells in _rows():
        module, operator, occurrence, _verdict, _evidence, _why = cells
        assert module in CORE_MODULE_PATHS, (
            f"{module} is outside Layer 2's six-module scope; a scope change "
            f"moves the score without moving the tree"
        )
        assert operator.startswith("core/"), operator
        assert occurrence.isdigit(), occurrence


def test_rows_are_unique():
    seen = [(c[0], c[1], c[2]) for c in _rows()]
    assert len(seen) == len(set(seen)), "duplicate mutant rows inflate the count"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_survivor_triage_table.py -v`
Expected: FAIL — the document does not exist.

- [ ] **Step 3: Write the enumerator**

Create `scripts/triage_survivors.py`:

```python
#!/usr/bin/env python
"""Enumerate surviving mutants from the durable Layer 2 sessions.

WHY THIS EXISTS. The last time anyone ENUMERATED a survivor set was run 3.
Every figure since -- ~17, ~12, ~27 and 0 -- is arithmetic over a score. See the
'untriaged survivors' section of
docs/superpowers/specs/2026-08-01-ledger-reconciliation.md. A score cannot say
WHICH mutant survived, so it cannot say whether a survivor is an equivalent
mutant or a hole in the suite. The 0 was worse than useless: it was an artefact
of the O-B finalizer capture
(docs/superpowers/specs/2026-08-02-ob-finalizer-capture.md).

Usage:
    python scripts/triage_survivors.py            # markdown rows on stdout
    python scripts/triage_survivors.py --json     # machine-readable
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cosmic_ray.work_db import WorkDB, use_db
from cosmic_ray.work_item import TestOutcome

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SESSIONS_DIR = REPO_ROOT / ".cosmic-ray-sessions"


def enumerate_survivors(sessions_dir: Path) -> list[dict]:
    """Every SURVIVED work item across every session, sorted for a stable diff.

    Sorted by (module, operator, occurrence) so re-running after a triage
    produces a diff a reviewer can read rather than a reshuffle.
    """
    survivors: list[dict] = []
    for session in sorted(sessions_dir.glob("*.sqlite")):
        with use_db(str(session), WorkDB.Mode.open) as db:
            for work_item, result in db.completed_work_items:
                if result.test_outcome != TestOutcome.SURVIVED:
                    continue
                for mutation in work_item.mutations:
                    survivors.append(
                        {
                            "module": str(mutation.module_path).replace("\\", "/"),
                            "operator": mutation.operator_name,
                            "occurrence": mutation.occurrence,
                            "start_pos": list(mutation.start_pos),
                            "job_id": work_item.job_id,
                        }
                    )
    survivors.sort(key=lambda s: (s["module"], s["operator"], s["occurrence"]))
    return survivors


def render_rows(survivors: list[dict]) -> str:
    """Markdown body rows, six cells, verdict pre-filled PENDING."""
    lines = []
    for s in survivors:
        line, _col = s["start_pos"]
        lines.append(
            f"| {s['module']} | {s['operator']} | {s['occurrence']} | PENDING "
            f"| line {line} | |"
        )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions-dir", type=Path, default=DEFAULT_SESSIONS_DIR)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not args.sessions_dir.is_dir():
        print(
            f"no sessions at {args.sessions_dir}. Run "
            f"`python scripts/check_suite_integrity.py` first -- it takes about "
            f"25 minutes and must not run concurrently with pytest.",
            file=sys.stderr,
        )
        return 2

    survivors = enumerate_survivors(args.sessions_dir)
    print(json.dumps(survivors, indent=2, sort_keys=True) if args.json
          else render_rows(survivors))
    print(f"\n{len(survivors)} survivors", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

**UNVERIFIED:** `MutationSpec.start_pos` is declared as `tuple[int, int]` in
`cosmic_ray/work_item.py`, but its 1- vs 0-basedness has not been checked against a real
session here. Confirm against one survivor by opening the module at the reported line; if it
is 0-based, say so in the table's legend rather than silently adjusting the numbers.

- [ ] **Step 4: Generate the table**

```bash
python scripts/triage_survivors.py --json > .cosmic-ray-sessions/survivors.json
python scripts/triage_survivors.py > .cosmic-ray-sessions/survivors.md
```

Create `docs/superpowers/specs/2026-08-02-mutation-survivor-triage.md` containing:

- A header saying what this is: the enumerated Layer 2 survivor set and its triage — the
  artifact the reconciliation's *untriaged survivors* section assigns to P1.5 — and that the
  previous "0 survivors" was an artefact of the O-B finalizer capture, cross-referenced to the
  capture record.
- `Base commit: <sha>` and `Survivors measured: <n>`, copied from the Task 3 run manifest and
  `survivors.json`. If they disagree, stop: the table and the run describe different things.
- A **scope statement**: six modules, `gen/` excluded per design spec §2 non-goals, plus the
  six per-module `total` job counts from the manifest, so a future scope change is a diff.
- The verdict legend:
  - `KILLED-BY-NEW-TEST` — a test added in this plan fails on this mutant. Evidence cell names
    the test node ID.
  - `EQUIVALENT` — the mutation provably cannot change any observable. Why cell holds the
    argument; Task 6 re-executes it.
  - `ACCEPTED-GAP` — a real hole, accepted and recorded rather than closed. Why cell says what
    the missing test would assert and why closing it is out of scope.
  - `PENDING` — not yet judged. Legal in this task only.
- A **comparison against run 3** — 40 survivors, 19 corrected documented equivalents, 21
  untriaged (cite the reconciliation, do not restate its derivation). Say how many of run 3's
  survivors reappear here.
- The table, header row exactly
  `| Module | Operator | Occurrence | Verdict | Evidence | Why |`, then the generated rows.

- [ ] **Step 5: Run the tests to verify they pass**

```bash
python -m pytest tests/test_survivor_triage_table.py -v
python -m pytest -q
git status --porcelain src/
```

- [ ] **Step 6: Commit**

```bash
git add scripts/triage_survivors.py tests/test_survivor_triage_table.py \
        docs/superpowers/specs/2026-08-02-mutation-survivor-triage.md
git commit -m "feat: enumerate the Layer 2 survivor set into a committed table"
```

---

### Task 5: Drive every PENDING row to a verdict

**Estimate: 4 h. The largest task, and the one the plan exists for.**

**Files:**
- Modify: `docs/superpowers/specs/2026-08-02-mutation-survivor-triage.md`
- Modify: `tests/test_survivor_triage_table.py`
- Modify: whichever of `tests/test_types.py`, `tests/test_y14_5.py`, `tests/test_iso286.py`,
  `tests/test_montecarlo.py`, `tests/test_checker.py`, `tests/test_reliability.py` gain killing
  tests

**Interfaces:**
- Consumes: the table from Task 4
- Produces: a table with no `PENDING` rows; new tests in the core test subset

**Editing `tests/` invalidates Task 3's measurement.** Expected and planned for — Task 8
re-measures. What must not happen is editing `src/`: the mutated code has to be the same code,
or the survivor list stops describing the tree.

**Do not maximise the score.** Design spec §2: coverage and mutation score are "instruments for
one specific defect class, not targets to maximise". A genuinely equivalent mutant is a correct
result, and an honestly recorded `ACCEPTED-GAP` is a better outcome than a contrived test that
kills a mutant while protecting nothing.

- [ ] **Step 1: Tighten the guard (the failing test)**

In `tests/test_survivor_triage_table.py`, remove `"PENDING"` from `ALLOWED_VERDICTS` and append:

```python
def test_no_row_is_still_pending():
    pending = [c for c in _rows() if c[3] == "PENDING"]
    assert not pending, (
        f"{len(pending)} survivors are still un-judged: "
        f"{[(c[0], c[1], c[2]) for c in pending[:10]]}. An unexamined survivor "
        f"is not acceptable (design spec section 4, Layer 2 threshold policy); "
        f"an equivalent mutant is."
    )


def test_every_killed_row_names_a_test_node_id():
    for cells in _rows():
        if cells[3] != "KILLED-BY-NEW-TEST":
            continue
        assert "::" in cells[4], (
            f"{cells[0]}/{cells[1]}/{cells[2]}: the evidence cell must name the "
            f"specific test node ID that kills this mutant. A whole-file "
            f"selector can be satisfied by an unrelated failure -- and five "
            f"mutants labelled 'killed' in SI-4 did not kill."
        )


def test_every_equivalent_row_states_an_argument():
    for cells in _rows():
        if cells[3] != "EQUIVALENT":
            continue
        assert len(cells[5]) >= 40, (
            f"{cells[0]}/{cells[1]}/{cells[2]}: an equivalence claim needs a "
            f"written argument, not a shrug. Four mutants labelled 'equivalent' "
            f"in SI-4 were live."
        )


def test_every_accepted_gap_states_what_the_missing_test_would_assert():
    for cells in _rows():
        if cells[3] != "ACCEPTED-GAP":
            continue
        assert len(cells[5]) >= 40, (
            f"{cells[0]}/{cells[1]}/{cells[2]}: an accepted gap must say what "
            f"the missing test would assert and why it is out of scope. "
            f"'Hard' and silence are not reasons."
        )


def test_the_verdict_distribution_is_stated_in_the_prose():
    """A reader must see the shape without counting forty rows."""
    text = _text()
    for verdict in ("KILLED-BY-NEW-TEST", "EQUIVALENT", "ACCEPTED-GAP"):
        assert f"{verdict}:" in text, (
            f"the document must state how many rows are {verdict}"
        )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_survivor_triage_table.py -v`
Expected: FAIL — `test_no_row_is_still_pending` lists every row, and
`test_every_row_carries_a_verdict_from_the_closed_set` now rejects `PENDING`.

- [ ] **Step 3: Triage, one mutant at a time, in table order**

```bash
git status --porcelain src/                       # must be empty
cosmic-ray apply <module> <operator> <occurrence>
git --no-pager diff src/                          # READ the mutation
```

`cosmic-ray apply MODULE_PATH OPERATOR OCCURRENCE` writes the mutation and does **not** restore
it. Read the diff, then choose one of three paths.

**Kill it.** Write a test in the matching core test file, then verify **both directions** —
this is the check that catches the SI-4 failure mode where five "killed" labels did not kill:

```bash
python -m pytest "<new test node id>" -q -p no:cacheprovider; echo "mutated exit: $?"
git checkout -- src/
python -m pytest "<new test node id>" -q -p no:cacheprovider; echo "clean exit: $?"
```

Required: `mutated exit: 1` **and** `clean exit: 0`. A test that fails both ways is broken; one
that passes both ways does not kill the mutant. Set `KILLED-BY-NEW-TEST` and put the node ID in
the Evidence cell.

**Call it equivalent.** Restore first (`git checkout -- src/`), then write the argument in the
Why cell: what the mutation changes, and why no observable can differ. Set `EQUIVALENT`. Do not
try to prove it here — Task 6 executes the proof, and a claim that fails there comes back to
this task.

**Accept it as a gap.** Restore, set `ACCEPTED-GAP`, and say in the Why cell what the missing
test would have to assert and why it is out of scope. Acceptable reasons: the mutant sits in a
path whose behaviour is not a published number and testing it needs new fixtures; closing it
would require editing a core module. Not acceptable: "hard", "low value", or silence.

**After every single mutant, without exception:**

```bash
git checkout -- src/
git status --porcelain src/     # must be empty before the next apply
```

Leaving a mutant on disk while applying the next produces a higher-order mutant and a triage of
something that is not in the table.

- [ ] **Step 4: State the distribution and verify**

Add a paragraph giving the counts in exactly the form `KILLED-BY-NEW-TEST: <n>`,
`EQUIVALENT: <n>`, `ACCEPTED-GAP: <n>`, and compare against run 3's figures from the
reconciliation's *untriaged survivors* section. Say plainly how much the new equivalent set
overlaps the old 19, and name any of the 19 that is no longer a survivor at all.

```bash
python -m pytest tests/test_survivor_triage_table.py -v
python -m pytest -q
python -m pytest tests/gen/test_ladder_pin.py -q
python scripts/gate_a.py > /dev/null 2>&1; echo "gate_a exit: $?"
git status --porcelain
```

Expected: all pass; ladder counts unchanged; Gate A exits **1**; tree clean.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-08-02-mutation-survivor-triage.md \
        tests/test_survivor_triage_table.py tests/test_*.py
git commit -m "test: triage every Layer 2 survivor, with a verdict and evidence per mutant"
```

---

### Task 6: The control on the triage

**Estimate: 2.5 h. Contains a spike.**

**Files:**
- Create: `tests/test_survivor_triage_control.py`
- Modify: `pyproject.toml`
- Modify: `docs/superpowers/specs/2026-08-02-mutation-survivor-triage.md`

**Interfaces:**
- Consumes: the table from Task 5
- Produces: `tests/test_survivor_triage_control.py`, parametrised over the table's rows, marked
  `triage_control`

**Why a control on the triage rather than just a triage.** SI-4's fix round found **nine
mislabelled mutants** — four "equivalent" that were live, five "killed" that did not kill.
Whatever process produced that error is still the process: a human reads a diff and writes a
word in a cell. Task 5 improves the process; it does not control it. This task controls it by
**re-executing every verdict** instead of re-reading it.

This is not a new layer under R5 — it is design spec §7's own Layer 2 validation ("confirm the
reported score changes when a known-weak test is removed"), which was specified and, on the
evidence, never performed.

- [ ] **Step 1: Run the spike — "A decidable test for 'equivalent mutant'"**

**Time box 1 hour.** Take the two rows you are least confident about:

```bash
python -m pytest -q > /tmp/p15-clean-suite.txt 2>&1; echo "clean suite exit: $?"
python scripts/measure_ladder.py > /tmp/p15-clean-ladder.txt 2>&1
cosmic-ray apply <module> <operator> <occurrence>
python -m pytest -q > /tmp/p15-mut-suite.txt 2>&1; echo "mutated suite exit: $?"
python scripts/measure_ladder.py > /tmp/p15-mut-ladder.txt 2>&1
git checkout -- src/
diff /tmp/p15-clean-ladder.txt /tmp/p15-mut-ladder.txt && echo "ladder identical"
```

Decide whether the set discriminates, and record the cost — the full suite plus the ladder is
roughly two minutes per mutant, so if the `EQUIVALENT` set is large the control must be marked
`slow`. **Fallback:** any row the set cannot decide is downgraded from `EQUIVALENT` to
`ACCEPTED-GAP` in Task 5's table. Record the ruling under the spike's title in `docs/SPIKES.md`
and in the triage document.

**On Gate A as an observable:** `scripts/gate_a.py` exits 2 while the mutation lock is held, by
design from `bdd632c`, and the control below holds that lock. If the spike concludes Gate A's
output is needed to decide a row, capture it in a separate, explicitly serialised step outside
the lock — **do not weaken the lock**, which is the one control the stopping criterion demanded
of itself.

- [ ] **Step 2: Write the failing test**

Create `tests/test_survivor_triage_control.py`:

```python
"""Re-execute every triage verdict. The triage's own control.

SI-4's fix round found NINE mislabelled mutants -- four called "equivalent"
that were live, five called "killed" that did not kill (ledger reconciliation,
'untriaged survivors'). The process that produced that error was a human
reading a diff and writing a word in a cell, and that is still the process. So
the verdicts are re-run, not re-read.

Each test mutates src/ and restores it, and therefore takes the same mutation
lock the declared-mutation layer takes: scripts/gate_a.py and
scripts/check_suite_integrity.py refuse to start while it runs.
"""

import subprocess
import sys

import pytest

from tests.mutation_registry import REPO_ROOT, mutation_lock
from tests.test_survivor_triage_table import _rows

pytestmark = pytest.mark.triage_control


def _apply(module: str, operator: str, occurrence: str) -> None:
    proc = subprocess.run(
        ["cosmic-ray", "apply", module, operator, occurrence],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, (
        f"cosmic-ray apply {module} {operator} {occurrence} failed:\n"
        f"{proc.stdout}\n{proc.stderr}"
    )


def _restore() -> None:
    subprocess.run(["git", "checkout", "--", "src/"], cwd=REPO_ROOT, check=True)
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "src/"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    assert not dirty.strip(), f"src/ was not restored: {dirty}"


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args], cwd=REPO_ROOT, capture_output=True, text=True
    )


def _rows_with(verdict: str) -> list[list[str]]:
    return [c for c in _rows() if c[3] == verdict]


def _ids(rows: list[list[str]]) -> list[str]:
    return [f"{c[0].rsplit('/', 1)[-1]}:{c[1].split('/')[-1]}:{c[2]}" for c in rows]


_KILLED = _rows_with("KILLED-BY-NEW-TEST")
_EQUIVALENT = _rows_with("EQUIVALENT")


def test_the_parametrisation_is_not_empty():
    """A parametrisation over an empty list is a test that cannot fail -- which
    is the defect class this whole repository exists to eliminate."""
    assert _rows(), "the triage table has no rows; this control would be vacuous"


@pytest.mark.skipif(not _KILLED, reason="no KILLED-BY-NEW-TEST rows in the table")
@pytest.mark.parametrize("row", _KILLED, ids=_ids(_KILLED))
def test_every_killed_verdict_actually_kills(row):
    """Both directions. Five SI-4 'killed' labels did not kill."""
    module, operator, occurrence, _verdict, node_id, _why = row

    baseline = _run(["-m", "pytest", node_id, "-q", "-p", "no:cacheprovider"])
    assert baseline.returncode == 0, (
        f"{node_id} FAILS on the unmutated tree. Demonstrating an outcome "
        f"change from a broken baseline proves nothing.\n{baseline.stdout[-2000:]}"
    )

    with mutation_lock():
        try:
            _apply(module, operator, occurrence)
            mutated = _run(["-m", "pytest", node_id, "-q", "-p", "no:cacheprovider"])
        finally:
            _restore()

    assert mutated.returncode != 0, (
        f"{node_id} still PASSED with {module} {operator} occurrence "
        f"{occurrence} applied. This row is mislabelled KILLED-BY-NEW-TEST -- "
        f"the mutant is live. Change the verdict or write a test that kills "
        f"it.\n{mutated.stdout[-2000:]}"
    )


@pytest.mark.slow
@pytest.mark.skipif(not _EQUIVALENT, reason="no EQUIVALENT rows in the table")
@pytest.mark.parametrize("row", _EQUIVALENT, ids=_ids(_EQUIVALENT))
def test_every_equivalent_verdict_leaves_every_observable_unchanged(row):
    """Four SI-4 'equivalent' labels were live mutants.

    The observable set is the one fixed by the spike 'A decidable test for
    "equivalent mutant"': the full suite's outcome, and the exact ladder counts
    plus corpus digest. If ANY of them moves, the mutation is not equivalent --
    whatever the argument in the table says.
    """
    module, operator, occurrence, _verdict, _evidence, _why = row

    clean_ladder = _run(["scripts/measure_ladder.py"])
    assert clean_ladder.returncode == 0

    with mutation_lock():
        try:
            _apply(module, operator, occurrence)
            mutated_suite = _run([
                "-m", "pytest", "-q", "-p", "no:cacheprovider",
                "--ignore=tests/test_survivor_triage_control.py",
            ])
            mutated_ladder = _run(["scripts/measure_ladder.py"])
        finally:
            _restore()

    assert mutated_suite.returncode == 0, (
        f"{module} {operator} occurrence {occurrence} is labelled EQUIVALENT "
        f"but the suite FAILS under it -- so a test CAN see it, and Layer 2 "
        f"recorded a detectable mutant as surviving. That is a Layer 2 "
        f"finding, not a triage error: check the run's tree fingerprint "
        f"against the current one.\n{mutated_suite.stdout[-2000:]}"
    )
    assert mutated_ladder.stdout == clean_ladder.stdout, (
        f"{module} {operator} occurrence {occurrence} is labelled EQUIVALENT "
        f"but changes the pre-registered ladder or the corpus digest. It is "
        f"not equivalent.\n--- clean ---\n{clean_ladder.stdout}\n"
        f"--- mutated ---\n{mutated_ladder.stdout}"
    )
```

Add the marker to `pyproject.toml`, alongside `slow` and `mutation`:

```toml
    "triage_control: re-executes each survivor-triage verdict; mutates src/ via cosmic-ray apply",
```

`--ignore=tests/test_survivor_triage_control.py` on the inner run stops this module recursing
into itself. It is used in preference to `-m "not triage_control"` because deselection by
marker still *collects* the module, and collection imports `_rows()` at module scope.

- [ ] **Step 3: Run the tests and expect some to fail**

Run: `python -m pytest tests/test_survivor_triage_control.py -v`

Expect **some rows to fail** — that is the task. If every row passes on the first run, check
that `test_the_parametrisation_is_not_empty` also ran and passed; a green control over an empty
list is the defect wearing this task's uniform.

- [ ] **Step 4: Correct the mislabelled rows and re-run**

Every failure is a **finding**. For each:

- a `KILLED-BY-NEW-TEST` row whose test does not kill → fix the test or change the verdict to
  `ACCEPTED-GAP`, and record that the control caught it;
- an `EQUIVALENT` row whose observables move → change the verdict, and record that the mutation
  is live. If the *suite* fails under a mutant Layer 2 recorded as surviving, that is a Layer 2
  inconsistency rather than a triage error — say so and check the run's tree fingerprint.

Add a section to the triage document: *"Corrections the control found"*, with a count and one
line per correction. If the count is zero, say **zero** and say what would have shown up — a
control that has never caught anything needs its own justification, and SI-4's nine is the
prior that says zero is unlikely.

```bash
python -m pytest tests/test_survivor_triage_control.py -v
python -m pytest -q
git status --porcelain
```

Report the added wall-clock time.

- [ ] **Step 5: Commit**

```bash
git add tests/test_survivor_triage_control.py pyproject.toml \
        docs/superpowers/specs/2026-08-02-mutation-survivor-triage.md \
        tests/test_survivor_triage_table.py tests/test_*.py
git commit -m "test: re-execute every triage verdict, and record the corrections it found"
```

---

### Task 7: The survivor sentinel — a guard that fails when the instrument is captured

**Estimate: 1 h. Contains a spike.**

**Files:**
- Modify: `scripts/check_suite_integrity.py`
- Modify: `tests/test_suite_integrity_script.py`

**Interfaces:**
- Consumes: the triage table from Task 6
- Produces: `SURVIVOR_SENTINEL: tuple[str, str, int]`;
  `check_sentinel(survivor_job_keys: set[tuple[str, str, int]]) -> tuple[bool, str]`

**A two-sided pin catches drift. It cannot catch a captured instrument.** It caught this one
only because the capture happened to move the number by 4.11 pp; a capture that landed inside
±0.50 would have gone straight through. What discriminates in the right direction is requiring
a **known mutant to survive** — the `expect="pass"` direction Layer 3 already relies on,
applied to Layer 2. If a future run reports the sentinel killed, the instrument changed, not
the suite.

- [ ] **Step 1: Run the spike — "Does `cosmic-ray baseline` write the module to disk?"**

**Time box 30 minutes.**

```bash
cosmic-ray baseline cosmic-ray.toml --session-file .cosmic-ray-sessions/baseline.sqlite
echo "baseline exit: $?"
python - <<'PY'
from cosmic_ray.work_db import WorkDB, use_db
with use_db(".cosmic-ray-sessions/baseline.sqlite", WorkDB.Mode.open) as db:
    for item, result in db.completed_work_items:
        print(item.job_id, item.mutations, result.worker_outcome, result.test_outcome)
PY
```

Record whether the baseline job carries a mutation (and so dirties the tree) or not. Either
way the decision stands — **use the sentinel** — but the rejection of `baseline` as the guard
must be evidenced rather than assumed, because on a clean tree it would not have caught the
capture at all.

- [ ] **Step 2: Write the failing test**

Append to `tests/test_suite_integrity_script.py`:

```python
def test_a_pinned_survivor_sentinel_names_a_real_triaged_mutant():
    """A two-sided pin catches drift; it cannot catch a captured instrument.

    From d7285f9 to 2026-08-02 the O-B tree-cleanliness finalizer made every
    cosmic-ray test command exit non-zero, so every mutant was recorded KILLED
    and the layer read 100.00%. The pin caught it only because the capture
    moved the number by more than the tolerance; a capture landing inside
    +/-0.50 would have passed. The sentinel discriminates in the right
    direction: it requires a mutant the triage proved cannot be killed to still
    be reported SURVIVED. See
    docs/superpowers/specs/2026-08-02-ob-finalizer-capture.md.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    module, operator, occurrence = mod.SURVIVOR_SENTINEL
    assert module in {f"src/tolcad/{m}.py" for m in mod.CORE_MODULES}
    assert operator.startswith("core/")
    assert isinstance(occurrence, int)

    triage = (
        REPO / "docs" / "superpowers" / "specs"
        / "2026-08-02-mutation-survivor-triage.md"
    ).read_text(encoding="utf-8")
    matches = [
        ln for ln in triage.splitlines()
        if f"| {module} | {operator} | {occurrence} |" in ln
    ]
    assert len(matches) == 1, (
        f"the sentinel {mod.SURVIVOR_SENTINEL} matches {len(matches)} rows of "
        f"the triage table; it must name exactly one triaged mutant"
    )
    assert "EQUIVALENT" in matches[0] or "ACCEPTED-GAP" in matches[0], (
        "the sentinel must be a mutant the triage established CANNOT be killed; "
        "pinning a killable one turns the guard into a flake"
    )


def test_the_sentinel_check_fails_when_the_sentinel_is_reported_killed():
    """Exercise the guard's failing branch without a 25-minute run."""
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    ok, msg = mod.check_sentinel(set())
    assert not ok
    assert "sentinel" in msg.lower() and "instrument" in msg.lower()

    ok2, _ = mod.check_sentinel({mod.SURVIVOR_SENTINEL})
    assert ok2
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python -m pytest tests/test_suite_integrity_script.py -v -k sentinel`
Expected: FAIL — `SURVIVOR_SENTINEL` and `check_sentinel` do not exist.

- [ ] **Step 4: Implement**

In `scripts/check_suite_integrity.py`:

```python
# THE SURVIVOR SENTINEL. A two-sided pin catches DRIFT. It cannot catch an
# instrument that reports a plausible number for the wrong reason -- and on
# 2026-08-01 exactly that happened. The O-B tree-cleanliness finalizer made
# every cosmic-ray test command exit non-zero, every mutant was recorded
# KILLED, and this layer reported 100.00% while measuring nothing. The pin
# caught it only because 100.00 is 4.11 pp from 95.89; a capture landing inside
# the 0.50 tolerance would have sailed through.
#
# So: name one mutant the triage proved cannot be killed, and require the run to
# still report it SURVIVED. This is the `expect="pass"` direction Layer 3
# already relies on, applied to Layer 2 -- an instrument that kills everything
# fails here even when the score looks reasonable.
#
# Sourced from docs/superpowers/specs/2026-08-02-mutation-survivor-triage.md;
# tests/test_suite_integrity_script.py asserts the row still exists and is still
# EQUIVALENT or ACCEPTED-GAP. Occurrence indices are POSITIONAL and move when the
# module's AST changes, so re-derive this whenever MUTATION_MEASURED is re-pinned.
SURVIVOR_SENTINEL: tuple[str, str, int] = ("src/tolcad/...", "core/...", 0)


def check_sentinel(survivor_job_keys: set[tuple[str, str, int]]) -> tuple[bool, str]:
    """True iff the pinned sentinel is among this run's survivors."""
    if SURVIVOR_SENTINEL in survivor_job_keys:
        return True, f"sentinel {SURVIVOR_SENTINEL} survived, as pinned"
    return False, (
        f"SENTINEL KILLED: {SURVIVOR_SENTINEL} is pinned as a mutant no test can "
        f"detect, and this run reports it killed. The instrument changed, not "
        f"the suite. Do not re-pin the score -- diagnose first. See "
        f"docs/superpowers/specs/2026-08-02-ob-finalizer-capture.md."
    )
```

Pick the sentinel from the Task 6 table: an `EQUIVALENT` row that the control verified, in the
module least likely to change. Have `run_mutation_score` collect `survivor_job_keys` while it
walks the sessions — import `enumerate_survivors` from `scripts/triage_survivors.py`, or
duplicate the eight-line loop and say which you did and why — and add the sentinel as its own
row in `_print_report` so a reader sees it beside the score. A failed sentinel must make `main`
return 1.

- [ ] **Step 5: Run and commit**

```bash
python -m pytest tests/test_suite_integrity_script.py -v
python -m pytest -q
```

```bash
git add scripts/check_suite_integrity.py tests/test_suite_integrity_script.py
git commit -m "feat: a survivor sentinel that fails the gate when the instrument is captured"
```

---

### Task 8: Re-measure, re-pin two-sided, and close the reconciliation

**Estimate: 2 h, of which ~25 min is an unattended run.**

**Files:**
- Modify: `scripts/check_suite_integrity.py`
- Modify: `docs/superpowers/specs/2026-08-01-ledger-reconciliation.md`
- Modify: `docs/superpowers/specs/2026-08-02-mutation-survivor-triage.md`

**Interfaces:**
- Consumes: everything above
- Produces: an updated `MUTATION_MEASURED` and `SURVIVOR_SENTINEL`; the reconciliation's two
  amended CANONICAL bullets

Task 5 added tests, so Task 3's score is stale by construction. This task measures the tree as
it now stands and pins that.

- [ ] **Step 1: Re-measure**

Nothing else runs on this machine.

```bash
git status --porcelain             # must be empty
git rev-parse HEAD                 # record: this is the SHA the pin describes
rm -f .cosmic-ray-sessions/*.sqlite
python scripts/check_suite_integrity.py > .cosmic-ray-sessions/run-2.log 2>&1
echo "integrity exit: $?"
tail -30 .cosmic-ray-sessions/run-2.log
cat .cosmic-ray-sessions/run-manifest.json
python scripts/triage_survivors.py --json > .cosmic-ray-sessions/survivors-2.json
```

- [ ] **Step 2: Reconcile the two survivor sets before pinning anything**

```bash
python - <<'PY'
import json, pathlib
load = lambda p: {(s["module"], s["operator"], s["occurrence"])
                  for s in json.loads(pathlib.Path(p).read_text())}
a = load(".cosmic-ray-sessions/survivors.json")
b = load(".cosmic-ray-sessions/survivors-2.json")
print("run 1 only (should be exactly the KILLED-BY-NEW-TEST rows):")
for k in sorted(a - b): print("  ", k)
print("run 2 only (NEW survivors -- never triaged):")
for k in sorted(b - a): print("  ", k)
PY
```

`a - b` must equal the table's `KILLED-BY-NEW-TEST` rows exactly. **`b - a` must be empty.** A
new survivor means Task 5's tests changed the mutant set: go back to Task 5, triage the new
rows, re-run Task 6's control, and re-measure. Do not pin over an untriaged survivor — that is
the state this plan started in. This is the contingency the re-cost calls out.

- [ ] **Step 3: Re-pin**

Set `MUTATION_MEASURED` to run 2's score to two decimals, with a dated comment naming the SHA
and the survivor count. **Leave `MUTATION_TOLERANCE = 0.50` alone** — the existing comment
justifies it against display rounding and cosmic-ray's timeout variance, and widening a
tolerance requires a recorded reason. Set `SURVIVOR_SENTINEL` to the chosen row.

`test_the_mutation_pin_is_measured_not_aspirational` rejects `MUTATION_MEASURED` in
`(0, 50, 60, 70, 75, 80, 85, 90, 95, 100)`. **If the honest measurement is exactly 100.0 that
test fails, and it is right to** — a real 100.00% means zero survivors, which means the
sentinel cannot exist and the triage table needs its `ZERO SURVIVORS` statement. Stop and
escalate; do not edit the exclusion list.

- [ ] **Step 4: Amend the reconciliation — in place, exactly two bullets**

`tests/test_observation_assignment.py` constrains how this is done. Read it first:

- `test_each_contested_quantity_has_exactly_one_canonical_value` requires **exactly one** line
  starting `- **CANONICAL` inside each `### <quantity>` section;
- `test_every_canonical_value_cites_its_provenance` requires the file to contain **exactly
  seven** `- **CANONICAL` bullets in total, each containing `provenance:`.

So **replace the text of the two existing CANONICAL bullets in place. Do not add an eighth.**

- ***untriaged survivors*** — replace with the enumerated result at the new SHA, citing
  `docs/superpowers/specs/2026-08-02-mutation-survivor-triage.md` and the run manifest as
  provenance. Add SUPERSEDED entries for the run-3-derived 21 and for the 0 implied by
  100.00%, the latter with the reason: an artefact of the O-B finalizer capture, cited.
- ***mutation score*** — replace with the new two-sided pin and its measurement, citing
  `scripts/check_suite_integrity.py::MUTATION_MEASURED` at the new commit. Add SUPERSEDED
  entries for `95.89` (reason: the last pre-capture measurement, taken on a tree without
  `tests/conftest.py`) and for the `100.00%` observation (reason: a captured instrument, not a
  measurement; cite the capture record). Replace the **DO NOT RE-PIN** sentence with a one-line
  record of when and why the re-pin happened, so a grep for the old instruction lands on its
  resolution rather than on a contradiction.

If the Task 3 spike changed the denominator, state the old and the new denominator in the same
bullet. A denominator change is a scope change wearing different clothes.

- [ ] **Step 5: Verify everything**

```bash
python -m pytest -q
python -m pytest tests/test_observation_assignment.py -v
python -m pytest tests/gen/test_ladder_pin.py -q
python scripts/gate_a.py > /dev/null 2>&1; echo "gate_a exit: $?"
python scripts/check_suite_integrity.py --layer coverage > /dev/null 2>&1; echo "coverage exit: $?"
git status --porcelain
```

Expected: full suite passes; the reconciliation guards pass — this is the check that the
in-place amendment did not add an eighth CANONICAL bullet; ladder unchanged; Gate A exits **1**
with 7 PASS (5 measured, 2 attested) / 3 SKIP; the coverage-only layer exits **0** at 94.74;
tree clean.

- [ ] **Step 6: Commit**

```bash
git add scripts/check_suite_integrity.py \
        docs/superpowers/specs/2026-08-01-ledger-reconciliation.md \
        docs/superpowers/specs/2026-08-02-mutation-survivor-triage.md
git commit -m "fix: re-pin Layer 2 against an enumerated survivor set, with a survivor sentinel"
```

- [ ] **Step 7: Land the branch and clean up the worktree**

REQUIRED SUB-SKILL: `superpowers:finishing-a-development-branch`.

```bash
cd /c/Users/harsh/Downloads/Projects/Paper1
git merge --ff-only p1.5/mutation-survivor-triage
python -m pytest -q
git worktree remove ../Paper1-p15
git worktree prune
```

If the merge is not a fast-forward, `main` moved during P1.5 — meaning something edited `src/`
or `tests/` while a measurement was in flight. Do not merge. Re-run Task 8's measurement at the
merged SHA first.

---

## Plan completion state

At the end of Task 8:

- The O-B finalizer answers O-B's actual question, and a **committed regression test** fails
  against the old behaviour in both directions
- Layer 3 is honest again: all fifteen declared mutations have been executed against a working
  finalizer, the four that had never been executed are named, and an inert-mutation probe
  guards the runner against the same capture
- The episode is recorded by name — **the O-B finalizer capture** — with three reproductions,
  the timeline, what it cost, what it did not cost, and the two-sided-pin vindication; no new
  ordinal was minted
- Layer 2 sessions are durable, counts come from the database rather than from prose, an
  unfinished run is refused rather than scored, and a run whose tree moved is refused too
- **Every survivor is enumerated in a committed table** with a closed-vocabulary verdict,
  evidence, and a written argument for every equivalence claim
- Every verdict has been **re-executed** by a control, with the corrections it found recorded
  and counted
- A survivor sentinel fails the gate when the instrument is captured — the failure mode a
  two-sided pin can only catch by luck
- The score is re-pinned two-sided at a stated SHA with the enumeration in the same commit, and
  the reconciliation's two open quantities are closed in place
- Gate A, the ladder pin, the coverage pin, `cosmic-ray.toml`, `CORE_MODULES`, the CI triggers
  and all fifteen registry entries are unchanged

## Deliberately NOT done here

- **Raising the mutation score.** Design spec §2: the score is an instrument, not a target.
  `ACCEPTED-GAP` rows stay accepted.
- **Extending Layer 2 to `gen/`.** Excluded by spec §2 non-goals; a scope change is a separate
  plan with its own baseline.
- **Auditing every other control for the same shape.** The O-B finalizer capture is one control
  disabling others; nothing here checks whether any *other* control does the same. That audit
  is worth scheduling and is bigger than this plan.
- **Executably pinning the declared-mutation registry size.** The reconciliation's §2 amendment
  asks whether it should be, having found a stale count inside the one document whose purpose
  is holding non-stale numbers. One line of test; its own review.
- **The baseline runnability audit** and **P2.3, the fresh-clone receipt**, both still open from
  the closeout plan.

## Open questions for the human

**1. The sentinel's maintenance burden.** It pins one mutant by
`(module, operator, occurrence)`, and occurrence indices are positional: they shift whenever
the module's AST changes. The six core modules are frozen today only because pre-registration
has not happened. After Phase 4 the sentinel becomes a maintenance cost that, on this
repository's history, will be silenced rather than re-derived. Deriving it from the triage
table at run time removes the burden but also removes the pin, and an unpinned sentinel can be
quietly emptied. This plan chooses the pin and the burden; re-examine at the first re-pin after
the corpus exists.

**2. What else did the capture hide?** Layer 2 measured nothing between `d7285f9` and this
plan, and Layer 3's thirteen captured entries proved nothing over the same window. Every commit
in that range — `062316e` through `30eb333` — landed with both mutation layers dead. The suite
and Gate A were live throughout, and the registry has now been shown sound, so the exposure is
bounded; but "bounded" is not "zero", and the honest statement for the pre-registration is that
the mutation-based evidence for that range dates from after 2026-08-02, not from when the
commits landed.
