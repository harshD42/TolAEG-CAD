# Architect close-out plan (Round 0) — 2026-08-01

Author: senior architect agent. Verified against the repo by execution, not from summaries.

## Repo state verified
- feat/suite-integrity is **10 commits ahead**, not 8; main is a strict ancestor, so a clean fast-forward.
- 374 passed + 2 skipped (NIST suite not fetched). Reproduced in a worktree AND a real `git clone --no-local`.
- Gate A exit 1, 6 PASS / 3 SKIP. Reliability mean 0.9982 over 200 seeds, CI [0.9964, 0.9995].
- Ladder confirmed exactly: 31/159, 99/301, 239/452, 421/609 on numpy 2.4.1.

## TWELVE NEW FINDINGS (F1–F12), none of which were in the 17-item inventory

**F1** — `MUTATION_MEASURED = 93.85` is 2.04 pp BELOW the current tree (re-ran: coverage 94.74%, mutation 95.89%). Four times its own 0.50 tolerance. A later commit raised the real score and nobody re-measured. It passes silently because a floor is a lower bound. The drift class, live, inside the layer built to catch the drift class. Thirteenth instance. Consequence: B1's "~12 untriaged survivors" is a stale carried-forward number.

**F2** — *** THE FOUR PRE-REGISTRATION LADDER NUMBERS ARE PINNED BY NOTHING. *** They appear in BLOCKERS.md and five ledgers and would go straight into the pre-registration. The only committed guard is a monotonicity assertion plus bands over 80 SEEDS, NOT 200. No script produces the 200-seed figures. The corpus digest is unreproducible — the recipe was never recorded. CONTROLLER-VERIFIED: `ls scripts/` shows no such script.

**F3** — The frozen ladder is numpy-version-dependent and numpy is UNPINNED (`numpy>=1.26`, installed 2.4.1). NEP 19 guarantees stream stability only for legacy RandomState, not Generator. Reproduces today; nothing makes it reproduce for a reviewer in 2027.

**F4** — `.gitattributes` IS testable without CI — the architect proved it in 20 s with `git -c core.autocrlf=true clone --no-local`. Also: ubuntu-latest defaults to autocrlf=false, so a Linux-only CI exercises the SAFE direction and proves nothing. Needs a windows-latest leg with autocrlf=true.

**F5** — *** ADDING CI DOES NOT CLOSE A3. *** `gate_a.py:353` hardcodes the row and `tests/test_gate_a.py:112` ASSERTS `"SKIP"` in that row. CONTROLLER-VERIFIED both. Closing A3 requires editing `gate_a.py` and that test. The architect argues CLAUDE.md freezes §7 THRESHOLDS, not the file, and correction 2026-08-01e already amended `gate_a.py` pre-data under a logged amendment.

**F6** — Gate A cannot clear without SolidWorks, contradicting §4.3 ("every headline number reproduces with no SolidWorks license") and §7's own prose. The §7 TABLE still lists TolAnalyst ≥95% as a criterion and `gate_a.py` counts every SKIP as not-a-pass.

**F7** — *** HIGHEST UNCERTAINTY, POTENTIALLY CRITICAL. *** The NIST oracle's ground-truth `assembles` column has no published source. The suite is 17 SINGLE-PART AP242 files — no assemblies — and NIST publishes annotation content, not assemblability verdicts. The architect did NOT read NIST's documentation this session and flags this as needing verification FIRST, before pre-registration.

**F8** — Phase 4 has essentially no infrastructure. `metrics/`, `harness/`, `analysis/` do not exist. A5 is one line hiding three unbuilt subsystems plus ≥8 baseline integrations.

**F9** — `.superpowers/` is UNTRACKED AND NOT IGNORED. Five ledgers, all fix reports, BLOCKERS.md — the project's entire defect history, which Gate D's traceability requirement depends on — is one `rm -rf` from gone and absent from the remote. CONTROLLER-VERIFIED.

**F10** — No LICENSE, no README. Contribution 1 claims "the first such OPEN tool". A repo with no licence is not open source. CONTROLLER-VERIFIED both absent.

**F11** — SI-5's planned instance-map test forces a FALSE claim: `assert "not caught" not in doc` pressures wording around instance 4, which is measured as improved-not-closed. Its sibling `assert f"| {n} |" in doc` passes against eleven rows of "TODO".

**F12** — Layer 2 takes ~25 MINUTES, not "a few minutes". SI-5's plan puts it on per-push CI. A gate people route around is worse than no gate.

Hygiene: BLOCKERS.md says 17 items but lists 18. `fetch_nist_pmi.py` has no archive checksum.

## MERGE DECISION

Fast-forward merge `feat/suite-integrity` into `main` NOW, before anything else. Do not rebase, squash, or gate on any B-item.

Rationale: the diff touches ZERO files under `src/` — 1,949 lines of tests and tooling with no behaviour change, so it cannot regress a headline number. `main` is a strict ancestor. Both floors pass on re-measurement (stale UPWARD, the safe direction). Everything downstream must sit on top of it. "Twelve open items" is an argument FOR merging: on `main` they are visible with a running gate; on a branch they rot.

## SEQUENCE

**Phase 0** (hours): merge+push; commit `.superpowers` (F9); LICENSE (F10); README (F10).

**Phase 1** (1–2 days) — the ONLY technical work on the critical path:
- **P1.1 [CP]** `scripts/measure_ladder.py` + a test pinning exact counts and a corpus digest over a WRITTEN-DOWN recipe. Failure message prints `numpy.__version__`. Closes F2.
- **P1.2 [CP]** Pin `numpy==2.4.1` in a `repro` extra + lockfile. Closes F3. P1.1 without P1.2 is a test that cries wolf for the wrong reason.
- **P1.3 [CP]** Resolve the NIST oracle definition (F7). Human + literature. Blocks A4.
- **P1.4 [CP]** Resolve the Gate A licence contradiction (F6) via a §7 correction-log entry.
- **P1.5 [par]** Re-measure + re-triage Layer 2 (B1+B3+F1). One run, alone. Then RE-RUN and require the survivor set to have actually shrunk. Re-pin both constants.
- **P1.6 [par]** The `.gitattributes` clone test (F4). ~10 lines, no CI dependency.
- **P1.7 [par]** Post-suite tree-cleanliness assertion. ONE depth-0 control that subsumes B2, B10 and the cosmic-ray leftover hazard.
- **P1.8 [par]** Two one-liners: B9 (suffix check) and B11 (`::` in selector).
- **P1.9 [par]** SHA-256 pin on the NIST archive.

**Phase 2** (1–2 days): CI with TWO jobs — `suite` (ubuntu + windows matrix, windows sets autocrlf=true) and `integrity` (workflow_dispatch + weekly ONLY, per F12).
- **P2.3 [CP]** Close A3 honestly: `gate_a.py` reads `data/fresh_clone_receipt.json` `{commit_sha, workflow_run_url, pytest_exit, integrity_exit}`; the row PASSes only if `commit_sha == HEAD`. Replace the SKIP-pinning test. Log as a §7 correction, pre-data.
- **P2.4 [par]** SI-5 instance map with an AMENDED contract (see C1).

**Phase 3 [CP]**: pre-registration. Tag the repo; put the tag in the registration.

**Phase 4 [CP]**: corpus + `metrics/` + `harness/` + `analysis/` + ≥8 baselines (F8).

CRITICAL PATH is short and mostly DECISIONS: NIST oracle definition + TolAnalyst ruling + ladder/environment pin + fresh-clone receipt → pre-registration → corpus. Roughly three days of engineering and one decision session.

## DISPOSITIONS (8 FIX NOW / 3 FIX LATER / 5 ACCEPT / 3 REJECT, plus the A1 split)

- **A1 SPLIT**: definition FIX NOW (blocks A4); verdict CSV FIX LATER.
- **A2 FIX LATER**; but resolve its STATUS now (P1.4).
- **A3 FIX NOW**, re-scoped: P1.6 + P2.1 + P2.3.
- **A4 FIX NOW** — the critical path.
- **A5 FIX LATER**, and re-scope (F8).
- **B1 FIX NOW** (P1.5). **B3 FIX NOW** (P1.5). **B9 FIX NOW**. **B11 FIX NOW**.
- **B2 ACCEPT**: failure mode is a LOUD OSError either way; identical harmful outcome; depth-3 under the stopping rule; covered at depth 0 by P1.7 instead.
- **B4 ACCEPT**: no in-repo mechanism can stop a deliberate two-line commit by a solo author.
- **B5 FIX LATER WITH A TRIGGER**: on adding a SECOND `expect="pass"` entry, require a `witness_test` field. Write the trigger into the docstring, not into memory.
- **B6 ACCEPT**: the tripwire is correctly scoped; the seed-fishing CLASS is closed instead by the pre-registration committing every statistic to a pre-declared seed set.
- **B7 REJECT THE FIX**: "fixing" means retuning `_RELIABILITY_MATES` AFTER seeing the k-sweep — post-hoc instrument tuning, strictly worse than the residual. Disclose the k-sweep (0.9982 / 0.9518 / 0.9068) verbatim instead. Instance 4 = improved, bounded, NOT closed.
- **B8 REJECT AS NOT-A-DEFECT**: each `_uninterned` copy asserts its own postcondition, so drift fails loudly at point of use. What remains is DRY aesthetics.
- **B10 ACCEPT**: no in-process mechanism survives SIGKILL; detection at depth 0 (P1.7) is right.
- **B12 REJECT, CONDITIONAL ON A RULING**: the mutation score is NEVER a published number — README and CI only, never the paper. With no published number the imbalance cannot distort anything. If the author later cites it, this flips to FIX.
- **C1 FIX NOW**, split, plan AMENDED: each of the eleven rows carries a verdict from a closed vocabulary CAUGHT / PARTIAL / ACCEPTED with a non-empty evidence cell. Instance 3 is PARTIAL, instance 4 is PARTIAL with the k-sweep. Eleven CAUGHTs would be the fourteenth instance.

## THE STOPPING CRITERION (applied by counting, not taste)

**Definition.** A PUBLISHED NUMBER appears in the paper, the pre-registration, the headline table, or a gate verdict. Everything else is engineering telemetry.

- **R1 Coverage** — every published number has exactly one named guard, WATCHED FAILING at least once by an executed mutation with recorded output. Not argued. Executed.
- **R2 Depth cap** — number ← guard (d1) ← meta-guard (d2). DEPTH 3 IS PROHIBITED. d2 is allowed only for the runner's three anti-vacuity checks, because they execute inside the same run that exercises the d1 guard, so they have an independent observer. At d3 a failure produces a false green with nobody watching — that is what generates infinite regress.
- **R3 Loud beats guarded** — a defect whose failure mode is a visible error, crash, or false RED is never fixed. Only silent false-greens qualify.
- **R4 Prefer depth 0** — cover a residual by observing the ARTIFACT rather than the guard. Not a new layer; does not count against R2.
- **R5 New layers require an INSTANCE, not an argument** — layer 4 only after a layer-1-to-3 defect is demonstrated BY EXECUTION to have moved a published number. Note what the history shows: every one of the eleven was found by executing a mutation or asking "what would make this fail?" The marginal control that pays is EXECUTE THE MUTATION, not ADD A LAYER.
- **R6 Disclose with a measured bound**, never a hedge. "2–3×" is a bound; "may not catch everything" is not.

Evidence the rule has teeth: applied blind to twelve B-items it produced 4 FIX / 5 ACCEPT / 3 REJECT — neither "accept everything" nor "fix everything".

## PRE-REGISTRATION CONTENTS (26 items, abbreviated)

**A. Identity** — title/authors/date; EXACT git SHA and tag; environment including `numpy==2.4.1` and the statement that the ladder is conditional on it; H1 verbatim; scope and out-of-scope.

**B. Instrument frozen** — the six core modules at the SHA; Y14.5 formulas as implemented, B-4 only with B-5 unimplemented so fixed verdicts ASSUME a projected zone; six frozen tables + SHA-256 + the constants outside the hashed six; THE TWO DECLARED-INERT UNTRACED NUMBERS NAMED (`_FASTENER_LOWER_DEV_MM = -0.1`, `_TAPPED_HOLE_UPPER_DEV_MM`) with the note that −0.1 IS published in the sidecar; standards provenance including the ISO 273 "for information only" note, since taking that option was a choice; the µm/mm split at IT12.

**C. Benchmark frozen** — `_TOL_FRACTION_RANGE` verbatim AND the ladder as EXACT COUNTS (31/159, 99/301, 239/452, 421/609) over seeds 0–199 plus the digest and its recipe; corpus size and the `mc_seed` rule; the sidecar schema; and KNOWN DEGENERACIES STATED AS LIMITATIONS — I2 (iso_fit labels 100% predictable from the shaft letter) and the fact that fixed vs floating is distinguishable only by hole diameter, no thread geometry.

**D. Gates and statistics** — §7 verbatim; the COMPLETE correction log including the new entries; §8 verbatim; THE RELIABILITY DECLARATION including the frozen mate set, the 3.5e-4 free parameter, and the measured k-sweep as the honest sensitivity bound; the pre-declared seed set for EVERY statistic and the commitment that no result comes from a single draw; the null contingency IN FULL, in advance; the deviations-table commitment.

**E. Oracles** — the NIST criterion's operationalisation and the definition of "decidable case" fixed BEFORE any case is inspected; whether TolAnalyst is blocking or supplementary; the NIST archive URL + SHA-256 + acknowledgement.

**F. Integrity disclosures** — that the anti-vacuity layer exists, what it does NOT cover, and the accepted residuals with rulings. Disclosing eleven-plus self-caught instances is the single most credible thing in the registration and pre-empts the exact hostile attack.

**EXPLICITLY NOT FROZEN**: mutation score, coverage floor, survivor counts — telemetry, not published numbers. Freezing them would re-open B12.

## THE RISK THE ARCHITECT DID NOT SOLVE

F8. `metrics/`, `harness/`, `analysis/` do not exist and ≥8 baselines must be integrated behind CADBench's unified protocol. That is the bulk of remaining calendar time. The architect declines to estimate it and says it must NOT be estimated from the checker's velocity — the checker is 1,586 lines of pure numpy with exact answers; baseline integration is neither.
