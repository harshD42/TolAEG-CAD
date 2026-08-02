# Observation Assignment: the stopping criterion, worked

**Status:** approved 2026-08-01. Additive. Freezes no threshold and changes no constant.
**Guard:** `tests/test_observation_assignment.py` — this document is parsed, not merely read.
**Companion:** `docs/superpowers/specs/2026-08-01-ledger-reconciliation.md`.

## 0. Why this file exists at all

Until it was written, the table in §3 lived only in an agent transcript. That is the
**Unencoded** shape from the suite-integrity design spec's own taxonomy — *"the verification
happened but left no guard"* — and it is the identical defect as the 39-cell IT table check
that was run once in a shell and never committed. The artifact that makes this project's
stopping criterion *checkable* rather than merely *stated* was one session expiry from gone.

The irony is worth keeping on the page rather than in a commit message, because it is the
strongest available argument for R4: **prefer observing an artifact over guarding a guard.**
An unwritten rule is not a control at any depth.

## 1. The four observations

The regress "who checks the checker?" terminates because this list is **closed**. Extending it
is a human decision recorded here; no agent may add a fifth observation.

- **O-A** — full suite pass/fail on a clean checkout.
- **O-B** — working-tree cleanliness after every suite run. Implemented as a session-scoped
  finalizer over `git status --porcelain src/ tests/fixtures/` (`tests/conftest.py`).
- **O-C** — **two-sided exact pins** on
  (a) every published number,
  (b) every **instrument-composition quantity** a published number is computed over —
  denominators, `tested`/`excluded`, seed-set sizes, and
  (c) every constant a layer or a gate compares a measurement against.
- **O-D** — adversarial review at named checkpoints, by a reader who did not write the thing.

**O-C is two-sided by construction.** A one-sided floor is how `MUTATION_MEASURED` drifted
2.04 pp — four times its own tolerance — *inside the layer built to catch drift*. A floor
never flags an improvement, so the pin detaches silently the moment the next test lands.

## 2. The rules

- **R1 — Coverage.** Every published number has a named guard **watched failing**, with
  recorded output, via a registry entry.
- **R2 — Termination.** A control needs its own control **only if** its failure mode is a
  **silent false green** *and* **none of O-A…O-D reveals it**. *To add a control you must name
  the observation that fails to reveal the defect.*
- **R3 — Loud beats guarded.** A failure that stops the run needs no second control.
- **R4 — Prefer artifact observation over guarding the guard.**
- **R5 — Layers ratchet, review discovers.** Zero of the historical instances were found by the
  three-layer machinery; ten were found by an adversarial reader over a diff. A new layer is
  justified only when a defect review already caught **comes back**. Awareness — a note in
  `CLAUDE.md`, a line in a prompt — is explicitly **not** a control: the pattern was in project
  memory and in nearly every review prompt of the 2026-08-01 session and three new instances
  still landed.
- **R6 — Disclose with a measured bound**, and with a CI where the quantity is stochastic.

### 2.1 What "reveals" means in R2 — the one reading that matters

R2 asks whether an observation reveals the defect **on every run, without a human deciding to
look**. O-A, O-B and O-C are standing observations: they run unattended and they fail loudly.

**O-D is not.** It is scheduled at named checkpoints, it is a discovery mechanism (R5), and it
has a duty cycle measured in review-days. So O-D having *found* a defect once does **not**
discharge R2 for that defect's recurrence. This distinction is load-bearing and is exactly
where the plan's prose is ambiguous: Task 9's control is required *even though O-D found the
defect*, because O-D cannot be relied on to find it again next Tuesday.

The rule, stated so it cannot be misapplied:

> **O-D discovers; it does not guard.** For R2's purposes, count O-D as revealing a defect only
> when a *scheduled, budgeted* checkpoint is specifically charged with looking for it — and even
> then, prefer converting it into O-A/O-B/O-C.

## 3. The worked assignment table

One row per control in the tree. A reader deciding whether a *proposed* control is justified
works this table mechanically: find the failure mode, read the "revealed by" cell, and apply
R2. A row whose verdict names no observation is decoration; the guard rejects it.

| Control | Failure mode if it goes wrong | Revealed by | Needs its own control? |
|---|---|---|---|
| `run_declared_mutation` — the declared-mutation runner (Layer 3's engine) | A botched restore leaves a `src/` file mutated on disk. OBSERVED, not hypothetical: `OSError: Errno 22` on the restore write left `src/tolcad/reliability.py` mutated, once in roughly a dozen Windows runs. | O-B directly, on the same run; O-A on the next run, since a mutated checker fails the suite. Steps 1, 2 and 5 of the runner make its own vacuity loud (R3). | No — O-B. The runner is the one control the project has actually *watched* fail, and O-B was built in the same commit as the merge that introduced the hazard. |
| `test_the_registry_still_covers_every_critical_guard` | One commit deletes a registry entry **and** its name from `_CRITICAL_GUARDS` together. Silent false green: the guard simply stops existing and nothing reports it. | O-D only. `_CRITICAL_GUARDS` lives in the same file and the same review as `REGISTRY`, so the deletion is visible in the diff and nowhere else. | No — O-D, and no mechanical control can do better. This is B4, an accepted limit stated in the test's own docstring rather than left for a reader to rediscover. R6: the bound is disclosed, not closed. |
| B2 — the OSError-to-AssertionError restore conversion inside Layer 3's runner | The conversion is wrong and the operator is not told the tree is mutated. An untested error branch inside the module built to catch untested branches. | O-B. The branch can only fire when the tree is *already* corrupt, and O-B fires on the same run against the same condition. | No — O-B. Not a silent false green: the branch's whole job is to be loud, and the observation that would replace it is already running (R3, R4). |
| B3 — no post-triage verification that the survivor set actually shrank | A triage records kills it did not make, and the reported score is carried forward from a stale run. Silent false green — and it happened: nine mutants were mislabelled, four "equivalent" that were live and five "killed" that did not kill. | O-C, since Task 2 made the mutation pin **two-sided**. It fired on its first real encounter: `MUTATION SCORE 100.00 vs pin 95.89 -> FAIL, pin detached upward`. A one-sided floor would have stayed green. | No — O-C. **The verdict changed because O-C changed.** Before the pin was two-sided this row read Yes; that is what an assignment table is for. |
| re-run-and-compare survivor control, proposed by the SI-4 fix agent, not built | It would catch a false kill claim by requiring the survivor set to shrink by the claimed amount. | O-C already reveals the defect it targets, in both directions, on every run of the integrity script. | No — O-C. **R2 forbids building it.** This is the refusal case: what the open item actually needs is a re-*measurement* (P1.5), not a new layer. R5 agrees — no caught defect has come back. |
| B10 — restoration is exception-safe but not crash-safe (SIGKILL mid-write) | A killed run leaves a `src/` file mutated with no `finally` reached. | O-B on the next run's finalizer; O-A immediately, since a mutated checker fails the suite. | No — not a silent false green at all: a SIGKILLed run produces no green verdict to be false. O-B catches the residue regardless. |
| B9 — `_count_and_apply` normalises CRLF to LF across the **whole file** for text targets | A line-ending-sensitive text target's experiment fails for the wrong reason, or appears to succeed because of the normalisation rather than the anchor. | O-A: the experiment fails loudly. The shipped three-line `test_text_targets_have_a_known_safe_suffix` bounds the blast radius to `.py/.md/.toml/.yml/.yaml/.cfg`. | No — O-A, and R3: the failure is loud. Stated honestly: the suffix guard **bounds blast radius, it does not fix B9**. The real fix is 15–25 lines and is deliberately not scheduled (R6: disclosed with its cost). |
| the ladder pin (`tests/gen/test_ladder_pin.py`) | The pre-registration freezes four numbers that nothing executable holds. Measured silent false green: with only the endpoints banded over 80 seeds, d2 and d3 could move **19.3 percentage points** with every guard green, and `flat-difficulty-ladder` targets d4 only. | O-C — all four exact counts (31/159, 99/301, 239/452, 421/609) plus the corpus digest, two-sided, on a pinned numpy 2.4.1. | No — O-C. No new control was needed; O-C applied *honestly* was, which is R1's unused teeth. The `ladder-d2-row-shifted` registry entry is the executed guard R1 requires, and it proves the pin notices a middle-row change. |
| `mate[8]`'s partial degeneracy in the reliability instrument | `tested` silently fell 12 to 11 while `tested > 0` stayed green and the published mean stayed plausible. Silent false green that survived four ledgers, and a second mate had the same defect latent. | O-C — but **only** its clause (b), instrument composition. No pin on the published number would have caught it: 0.9982 looked fine. Discovery credit is O-D's, and the July ledger shows the symptom was seen and reasoned benign without asking which mate left. | No — O-C(b). **This instance is why O-C names instrument-composition quantities explicitly** rather than only published numbers. Now pinned by `test_reliability_tested_and_excluded_are_pinned_exactly` and the construction rule in `test_every_sensitive_mate_has_exactly_one_binding_part`. |
| mutual exclusion between the mutation layer and readers of `src/` (Task 9's `mutation_lock`) | `gate_a.py` shells out to a fresh interpreter that reads the checker core **from disk** while `reliability-perturbation-tripled` has `src/tolcad/reliability.py` mutated. A published Gate A number measured against a mutated checker. Silent false green. | **None.** O-A: the suite passes, both processes agree. O-B: **structurally blind** — the tree is clean *after* the run; the corruption exists only *during* it. O-C: the pins compare a number to a constant, and the number is real — the *instrument* was wrong. O-D found it once and cannot be scheduled per-run (§2.1). | Yes — none of O-A…O-D reveals it, and the failure is a silent false green. R2 therefore requires a control and R5 explicitly rules out a `CLAUDE.md` warning as one. This is the criterion having teeth against its own author. |

### 3.1 The table tested on the case it was written for

Take Task 9's proposed mutual-exclusion control cold and run the procedure:

1. **Is the failure a silent false green?** Yes — a Gate A row prints PASS with a number
   measured against a mutated checker, and nothing anywhere says otherwise.
2. **Does O-A reveal it?** No. Both processes complete; the suite is green.
3. **Does O-B reveal it?** No, and *not for a contingent reason* — O-B observes the tree
   **after** the run. The corruption exists only during it. This is the cell that decides the
   row, and it is the sentence the table has to be able to produce.
4. **Does O-C reveal it?** No. O-C pins numbers against constants. The measured number is a
   genuine measurement — of the wrong instrument.
5. **Does O-D reveal it?** It *found* it. Under §2.1 that does not discharge R2.
6. **Verdict:** Yes, a control is justified. Named observation that fails: **O-B**.

The table produced the answer without appeal to judgement. That is the test of whether it is
an instrument or decoration.

### 3.2 How to use this table for a control that is not in it

Add a row. If you cannot fill the "revealed by" cell with an observation or the word `none`,
you do not yet understand the failure mode well enough to justify the control. If you write
`none`, you are claiming a gap in a closed list of four — say which one you expected to catch
it and why it structurally cannot, in the row.

## 4. The instance count, and the instance the map dropped

The suite-integrity design spec's §1 table enumerates **twelve** shape-instances while the
prose and §8 both say eleven. The discrepancy is not a miscount in the table — it is a
**dropped row in §8's distribution**:

| §1 shape | §8's distribution names it? |
|---|---|
| Insensitive x4 (anti-degeneracy guard; NIST CRLF fixture; case-sensitive text guard; seed-fished positive control) | yes, all four |
| Tautological x2 (self-referential layout margin constants; `nominal + 0.0 == nominal`) | yes, both |
| Unreachable x2 (module-level `pytestmark` skip; fetcher's mismatch `exit 1` branch) | yes, both |
| Drifted x2 (literal wall floor; Gate A measurement with 1000x headroom) | yes, both |
| Structurally impossible x1 (reliability metric incapable of returning below 1.0) | yes |
| **Unencoded x1 (39-cell IT table check run once in a shell, never committed)** | **no — omitted entirely** |

Eleven named, twelve enumerated. The single instance §8's coverage map silently drops is the
**Unencoded** one — the same shape as this document's own §0, and the only one of the twelve
that no layer can catch, because no layer can observe a verification that left no artifact.
Only O-D can, and only by comparing a document against the tree.

That instance is now closed twice over: the IT table is committed as the 52-cell IT5–IT8 pin
with an executed `it7-row-transposed` registry entry, and this file closes the observation
table. §8's success criterion still needs its C1 amendment; that is scheduled, not done here.

**Consequence for numbering.** Because the base count is wrong by one, every ordinal minted
later is unreliable. Only instances 2, 3, 4, 5, 6 and 10 are attested in code or spec text.
The canonical resolution is in the ledger-reconciliation companion: **refer to instances by
name, not by number.**
