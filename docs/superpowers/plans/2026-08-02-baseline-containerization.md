# Baseline Containerization Implementation Plan (Phase 4 prerequisite)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible, one-command-per-model container harness over the nine baseline
models named at `docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md:178`, and —
because Gate C's **frozen** criterion is *"effect holds across ≥ 6 of the ≥ 8 baseline models"*
while the spec names exactly **nine**, leaving **one spare** — produce, **before
pre-registration**, a defensible, committed answer to the only question that matters here: *how
many of these nine actually run?* Lose two models and a frozen criterion becomes unmeetable, and
after the Phase 3.5 freeze there is no honest recovery. The deliverable is therefore not nine
containers. It is `harness/RESULTS.md`.

**Architecture:** A new top-level `harness/` package, one-directional like `validation/` — it may
import `tolcad`; `tolcad` may never import it. Three layers. (a) A **contract** module,
stdlib-only and Python-3.7-compatible, that is COPYed into every baseline image so the host and
all nine containers share one definition of paths, statuses and exit codes. (b) A **host driver**
(`oci.py`, `runner.py`) that abstracts docker-vs-podman and issues exactly one command per model.
(c) Nine **model directories**, each a Dockerfile whose CUDA/PyTorch selection is a build `ARG`
resolved from a single build matrix, a lock file produced by that model's spike, and a thin
adapter. Verification is split into two stages with different evidentiary weight, and the split is
recorded per task.

**Tech Stack:** Python 3.13 on the host (3.7+ inside the contract module), Docker Engine / Podman,
`nvidia/cuda` base images, CadQuery 2.8.0 for input synthesis and artifact parsing, pytest 9.0.2,
tomllib.

## Hardware reality — read this before writing a single Dockerfile

| Machine | Role | GPU | Compute capability | Minimum CUDA | Container runtime |
|---|---|---|---|---|---|
| RHEL workstation | **Deployment target**, primary | 4× RTX A6000 Ada, 48 GB | **sm_89** | 11.8 | **podman**, possibly rootless, SELinux enforcing |
| Windows/WSL2 workstation | **Deployment target**, ablation farm | 4× RTX A6000 Ada, 48 GB | **sm_89** | 11.8 | Docker Desktop / WSL2 |
| Laptop | **Where this plan is executed** | 1× RTX 5060, 8 GB | **sm_120 (Blackwell)** | **12.8** | Docker Desktop / WSL2 |

The laptop's GPU requires a **newer** toolchain than the deployment target, not an older one.
Three consequences, and every one of them is a way this exercise can quietly become theatre:

1. **A container proven on the laptop GPU is not evidence it runs on the workstation.** It is
   evidence about sm_120 under CUDA 12.8+. The workstation is sm_89, and DeepCAD's 2021
   expectations are a *third* toolchain again. A green laptop-GPU run is not transferable and,
   worse, is persuasive — it looks like Stage 2 evidence and is not.
2. **Therefore Stage 1 on the laptop is CPU-only.** Not "CPU preferred" — CPU-only. Building a
   `cu128` image to satisfy the laptop GPU pins a PyTorch that is wrong for Ada; if that pin then
   gets baked, all nine images are rebuilt on the workstation and Stage 1 bought nothing.
3. **CUDA/PyTorch is a Docker `ARG`, never baked, and its default is the *deployment* value
   (`cu118`), not the laptop's.** A forgotten `--build-arg` must land you on the workstation
   target. Task 2 makes this a lint over all nine Dockerfiles, with negative fixtures, because a
   convention nobody checks is a convention that has already been violated.

## The two-stage validation contract

**Stage 1 — laptop, CPU-only.** What is *genuinely* verifiable here, and it is most of the
realistic failure surface: the image builds; dependency resolution converges to a lock file;
weights download and their **sha256 checksums are pinned**; the package imports; the adapter
honours the uniform CLI contract; and a tiny CPU forward pass wherever the model permits one.
This closes dead links, unresolvable pins, undocumented preprocessing, assumed dataset layouts
nobody ships, and entrypoints that do not exist.

**Stage 2 — workstation, GPU.** Real inference at real precision on sm_89, real artifacts, one
command. Only Stage 2 evidence counts toward the Gate C headroom number.

**Every task below states the stage it is verified in.** A task claiming Stage 1 evidence for a
Stage 2 property is this project's dominant historical failure mode — *the test that cannot fail*
— wearing a container. The three-layer suite-integrity machinery found zero of eleven historical
instances of it; a reader over a diff found ten. Read every "Expected:" line in this plan asking
what would have to be true for it to print FAIL, and if the answer is "nothing", say so.

## Global Constraints

- **The frozen Gate C criterion is `≥ 6 of the ≥ 8 baseline models`** (design spec §7, Gate C
  table). It is pre-registered and must not be revised. This plan **measures against** it and
  never edits it. Task 7 pins the constant two-sided against the spec text.
- **Nothing in this plan modifies `src/tolcad/`.** The checker is frozen for the duration. New
  code lives in `harness/`, new tests in `tests/harness/`, one new fetch script in `scripts/`.
- **`harness/` may import `tolcad`; no module under `src/tolcad/` may import `harness`.** Same
  one-directional rule as `validation/`, enforced in `tests/test_architecture.py` (Task 1).
- **`harness/contract.py` is stdlib-only and must run on Python 3.7.** It is COPYed into all nine
  images, one of which is a 2021 dependency set. No `tomllib`, no `|` unions at runtime, no
  numpy. Enforced by an AST lint in Task 1.
- **`harness/entrypoint.py` is stdlib-only for the same reason.** Its only non-stdlib import is
  the per-model `adapter`, imported lazily *after* the run manifest is opened, so an import
  failure is recorded rather than silent.
- **Weights are never committed.** Fetch script + tracked manifest with sha256 + gitignored
  payload, mirroring `scripts/fetch_nist_pmi.py` and `papers/literature/`, including that
  script's count-mismatch guard (`fetch_nist_pmi.py:56-63`).
- **No Docker-only semantics.** Every runtime invocation goes through `harness/oci.py`. Raw
  `docker` strings outside that module are a lint failure (Task 3).
- **A result that is not committed is not a result.** `harness/results.json` is the source of
  truth and `harness/RESULTS.md` is rendered from it by a test that fails when they diverge. The
  *Unencoded* defect shape — a finding that lived only in a shell scrollback — has already bitten
  this project.
- **`crashed`, `unparseable`, and `parsed` are three distinct outcomes and must never be
  collapsed.** A model that dies and a model that emits non-assemblable geometry are different
  findings in the paper. Per spec §8.4 neither is dropped; failures take worst-case metric values.
- **Verified fact, do not re-derive:** adding tests under `tests/harness/` cannot perturb the two
  integrity pins. `scripts/check_suite_integrity.py:99` builds its coverage subset as
  `[f"tests/test_{name}.py" for name in CORE_MODULES]` and `cosmic-ray.toml`'s `test-command`
  names the same six files literally. Neither globs.
- **Do not run anything in this plan concurrently with `pytest`.** `CLAUDE.md`'s concurrency rule
  applies unchanged; `.mutation-in-progress` guards the readers of `src/`, not this harness.

## Spikes

Genuine unknowns are marked **SPIKE** with a time box and a stated fallback. This plan was written
without network access: no upstream repository was read, so **no `pip install` line for any
baseline is asserted anywhere in it**. Where a real command depends on a repo's actual contents,
the plan gives a complete, runnable *procedure* whose output is a lock file, rather than a
fabricated line. Five consecutive plans in this project shipped snippets that did not run as
written; that record ends here by refusing to guess.

Cross-reference `docs/SPIKES.md` (authored in parallel; it owns the `S-xx` numbering — **cite by
title, do not invent an id**):

| Referenced by | `docs/SPIKES.md` title |
|---|---|
| Task 3 | *Podman rootless with SELinux volume labels on the RHEL host* |
| Task 5 | *Point-cloud conditioning inputs for the baseline harness* |
| Task 6 | *DeepCAD's 2021 dependency set under a modern base image* |
| Task 9 | *Per-baseline upstream inference entrypoint discovery* |
| Task 10 | *HoLa weight availability outside the HuggingFace Space* |

---

## File structure

| File | Change | Responsibility |
|---|---|---|
| `harness/__init__.py` | Create | Package marker; states the one-directional import rule |
| `harness/contract.py` | Create | **The contract.** Paths, filenames, modalities, exit codes, item/run schemas, `validate_out_dir`. Stdlib-only, py3.7-safe, COPYed into every image |
| `harness/entrypoint.py` | Create | Uniform in-container entrypoint. Owns argument parsing, per-item status, run manifest, exit codes. Stdlib-only |
| `harness/matrix.py` | Create | Loads `build_matrix.toml`; resolves a variant to `(base_image, torch_index_url)` |
| `harness/build_matrix.toml` | Create | Single source of truth for the three build variants |
| `harness/oci.py` | Create | docker/podman detection, rootless + SELinux handling, `build_argv` / `run_argv` |
| `harness/runner.py` | Create | `run_model(...)`; the one command per model; `python -m harness.runner` |
| `harness/artifacts.py` | Create | `classify(item_dir) -> "crashed" \| "unparseable" \| "parsed"` |
| `harness/results.py` | Create | `results.json` ↔ `RESULTS.md`; `gate_c_headroom` |
| `harness/results.json` | Create | Source of truth for the results table |
| `harness/RESULTS.md` | Create | **The deliverable.** Rendered, committed, render-checked |
| `harness/LICENCES.md` | Create | Per-model licence and redistribution verdict |
| `harness/make_inputs.py` | Create | Synthesises the smoke input set (STEP + point cloud) from the existing generator |
| `harness/prompts/smoke.jsonl` | Create | Three tracked smoke items |
| `harness/weights/MANIFEST.toml` | Create | Tracked weight manifest: url, sha256, bytes |
| `harness/models/<slug>/Dockerfile` | Create ×9 | ARG-parameterised image |
| `harness/models/<slug>/requirements.lock.txt` | Create ×9 | Spike output: the resolved dependency set |
| `harness/models/<slug>/adapter.py` | Create ×9 | `INPUT_MODALITY`, `load_model`, `generate` |
| `harness/models/<slug>/MODEL.md` | Create ×9 | Upstream commit, licence, spike log, Stage 1/2 verdicts |
| `scripts/fetch_baseline_weights.py` | Create | Fetch + verify, count-mismatch guard, payload gitignored |
| `tests/harness/test_*.py` | Create | Stage 1 tests |
| `tests/test_architecture.py` | Modify | `tolcad` must not import `harness` |
| `.gitignore` | Modify | `harness/weights/payload/`, `harness/out/`, `harness/prompts/steps/`, `harness/prompts/clouds/` |

The nine slugs, fixed once here and never spelled differently again:

```
cadrille  deepcad  brepgen  text2cad  cad-recode  dtgbrepgen  hola  cad-coder-mit  text-to-cadquery
```

`cad-coder-mit` carries the disambiguator in its own name deliberately: two distinct papers are
titled "CAD-Coder". **2505.14646 is Doris et al. (MIT)** and is the one in scope; 2505.19713 is
Guan et al. (Beihang) and is a different work. `papers/literature/` already keeps them apart as
`cad-coder-mit` and `cad-coder-beihang`; this harness uses the same slug so a grep across the repo
never conflates them.

---

### Task 1: The uniform contract, executable

**Verified in: Stage 1 (laptop, CPU). No container required.**

**Files:**
- Create: `harness/__init__.py`
- Create: `harness/contract.py`
- Modify: `tests/test_architecture.py`
- Test: `tests/harness/__init__.py`, `tests/harness/test_contract.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `CONTRACT_VERSION: str = "1.0"`
  - `IN_ROOT = "/in"`, `OUT_ROOT = "/out"`, `WEIGHTS_ROOT = "/weights"`, `CODE_ROOT = "/opt/tolcad"`
  - `PROMPTS_FILENAME`, `RUN_MANIFEST_FILENAME`, `ITEM_STATUS_FILENAME`, `CADQUERY_ARTIFACT`, `STEP_ARTIFACT`
  - `MODEL_SLUGS: tuple[str, ...]` — the nine, in the order above
  - `MODALITIES: tuple[str, ...] = ("text", "pointcloud", "brep", "unconditional")`
  - `class ExitCode(IntEnum)` — `OK=0`, `CONTRACT_VIOLATION=2`, `ENVIRONMENT=3`, `NO_OUTPUT=4`
  - `class ItemStatus` / `class RunManifest` — frozen dataclasses with `to_dict()` / `from_dict()`
  - `def image_name(slug: str, variant: str) -> str`
  - `def validate_out_dir(out_root, expected_ids) -> list[str]` — returns violation strings, `[]` when clean

Comparability is the entire reason for having eight baselines. If each model's output shape drifts,
the checker needs per-model glue, and per-model glue is where a comparison quietly stops being one.
So the contract is written first, as code, and every model bends to it.

Everything in this module is COPYed into a 2021 container, so it is stdlib-only and py3.7-safe.
The AST lint below is what keeps it that way after the fourth Dockerfile makes someone impatient.

- [ ] **Step 1: Write the failing test**

Create `tests/harness/__init__.py` (empty file) and `tests/harness/test_contract.py`:

```python
"""The contract is the comparability guarantee. Test it like one."""

import ast
import json
import pathlib

import pytest

from harness import contract

REPO = pathlib.Path(__file__).resolve().parents[2]

# Modules COPYed into every baseline image, including a 2021 dependency set.
PORTABLE_MODULES = ("contract.py", "entrypoint.py")
STDLIB_ALLOWED = {
    "argparse", "dataclasses", "enum", "importlib", "json", "os", "pathlib",
    "sys", "time", "traceback", "typing", "__future__",
}


def _imported_roots(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_portable_modules_import_only_the_allowed_stdlib():
    """These files run inside nine foreign environments. numpy is not available."""
    offenders = []
    for name in PORTABLE_MODULES:
        path = REPO / "harness" / name
        if not path.is_file():
            continue  # entrypoint.py arrives in Task 5; contract.py must exist now
        bad = _imported_roots(path) - STDLIB_ALLOWED
        if bad:
            offenders.append(f"{name} imports {sorted(bad)}")
    assert (REPO / "harness" / "contract.py").is_file(), "contract.py must exist"
    assert not offenders, "portable modules must stay stdlib-only: " + "; ".join(offenders)


def test_the_portability_lint_would_actually_reject_something(tmp_path):
    """A lint with no failing input is a test that cannot fail. Give it one."""
    victim = tmp_path / "bad.py"
    victim.write_text("import numpy\nimport json\n", encoding="utf-8")
    assert _imported_roots(victim) - STDLIB_ALLOWED == {"numpy"}


def test_there_are_exactly_nine_slugs_and_they_are_unique():
    assert len(contract.MODEL_SLUGS) == 9
    assert len(set(contract.MODEL_SLUGS)) == 9
    assert "cad-coder-mit" in contract.MODEL_SLUGS
    # 2505.19713 (Beihang) is a different paper and is NOT a baseline here.
    assert "cad-coder-beihang" not in contract.MODEL_SLUGS


def test_image_names_are_stable_and_carry_the_variant():
    assert contract.image_name("cadrille", "cu118") == "tolcad-baseline/cadrille:cu118"


def test_image_name_rejects_an_unknown_slug():
    with pytest.raises(ValueError, match="unknown model slug"):
        contract.image_name("not-a-model", "cpu")


def test_validate_out_dir_flags_a_missing_run_manifest(tmp_path):
    violations = contract.validate_out_dir(tmp_path, ["a"])
    assert any("run.json" in v for v in violations)


def test_validate_out_dir_flags_a_missing_item(tmp_path):
    (tmp_path / "run.json").write_text("{}", encoding="utf-8")
    violations = contract.validate_out_dir(tmp_path, ["a"])
    assert any("a" in v and "status.json" in v for v in violations)


def test_validate_out_dir_accepts_an_item_that_errored(tmp_path):
    """An item may legitimately fail. That is a MODEL result, not a CONTRACT breach.

    Conflating the two is the exact distinction the paper depends on.
    """
    (tmp_path / "run.json").write_text("{}", encoding="utf-8")
    item = tmp_path / "a"
    item.mkdir()
    (item / "status.json").write_text(
        json.dumps({"id": "a", "status": "error", "error": "boom",
                    "artifacts": [], "wall_s": 0.1}), encoding="utf-8")
    assert contract.validate_out_dir(tmp_path, ["a"]) == []


def test_item_status_round_trips():
    s = contract.ItemStatus(id="a", status="ok", error=None,
                            artifacts=["model.step"], wall_s=1.5)
    assert contract.ItemStatus.from_dict(s.to_dict()) == s
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/harness/test_contract.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'harness'`. `pythonpath` in
`pyproject.toml` already contains `"."`, so no config change is needed once the package exists.

- [ ] **Step 3: Write the contract**

Create `harness/__init__.py`:

```python
"""Uniform runner over the baseline models (design spec section 5, `harness/`).

One-directional, exactly like `validation/`: this package may import `tolcad`;
no module under `src/tolcad/` may import this one. Enforced by
tests/test_architecture.py.
"""
```

Create `harness/contract.py`:

```python
"""The uniform container contract shared by the host and all nine baselines.

STDLIB ONLY, AND MUST PARSE AND RUN ON PYTHON 3.7. This file is COPYed into
every baseline image, and one of those images carries a 2021 dependency set.
tests/harness/test_contract.py enforces both properties.

Layout inside a container:

    /in        read-only   prompts.jsonl plus any payload it references
    /weights   read-only   this model's fetched weights
    /out       read-write  everything the model produces
    /opt/tolcad            contract.py, entrypoint.py, adapter.py

Layout the model must write under /out:

    /out/run.json              one per run
    /out/<id>/status.json      one per input item, ALWAYS, even on failure
    /out/<id>/model.py         a CadQuery script defining module-level `result`
    /out/<id>/model.step       a STEP file
                               (at least one of the two when status == "ok")
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Sequence

CONTRACT_VERSION = "1.0"

IN_ROOT = "/in"
OUT_ROOT = "/out"
WEIGHTS_ROOT = "/weights"
CODE_ROOT = "/opt/tolcad"

PROMPTS_FILENAME = "prompts.jsonl"
RUN_MANIFEST_FILENAME = "run.json"
ITEM_STATUS_FILENAME = "status.json"
CADQUERY_ARTIFACT = "model.py"
STEP_ARTIFACT = "model.step"

IMAGE_NAMESPACE = "tolcad-baseline"

# Fixed order. Never re-spell a slug; `cad-coder-mit` is 2505.14646 (Doris
# et al., MIT). 2505.19713 (Guan et al., Beihang) shares the paper title and is
# NOT a baseline here.
MODEL_SLUGS = (
    "cadrille",
    "deepcad",
    "brepgen",
    "text2cad",
    "cad-recode",
    "dtgbrepgen",
    "hola",
    "cad-coder-mit",
    "text-to-cadquery",
)

# What an adapter consumes. `unconditional` models ignore every field but `seed`.
MODALITIES = ("text", "pointcloud", "brep", "unconditional")

ITEM_STATUSES = ("ok", "error", "skipped")


class ExitCode(IntEnum):
    """Exit codes are the crash-versus-bad-geometry boundary. Read the values.

    OK does NOT mean the model succeeded. It means the container honoured the
    contract: every requested id has a status.json. Individual items may carry
    status == "error", and that is a model finding, not a harness failure.
    """

    OK = 0
    CONTRACT_VIOLATION = 2   # ran, but /out does not satisfy the schema
    ENVIRONMENT = 3          # weights absent, adapter import failed, no CUDA
    NO_OUTPUT = 4            # ran, honoured the schema, produced zero artifacts

    # Anything else -- 1, 137 (OOM kill), 139 (segfault) -- is an uncaught
    # crash and is recorded verbatim rather than mapped onto one of the above.


@dataclass(frozen=True)
class ItemStatus:
    id: str
    status: str
    error: Optional[str]
    artifacts: List[str]
    wall_s: float

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict) -> "ItemStatus":
        return ItemStatus(
            id=d["id"],
            status=d["status"],
            error=d.get("error"),
            artifacts=list(d.get("artifacts", [])),
            wall_s=float(d.get("wall_s", 0.0)),
        )


@dataclass(frozen=True)
class RunManifest:
    model: str
    image: str
    contract_version: str
    device: str
    input_modality: str
    n_requested: int
    n_ok: int
    n_error: int
    n_skipped: int
    weights_sha256: str
    upstream_commit: str
    extra: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict) -> "RunManifest":
        known = {f for f in RunManifest.__dataclass_fields__ if f != "extra"}
        return RunManifest(extra=d.get("extra", {}),
                           **{k: d[k] for k in known})


def image_name(slug, variant):
    # type: (str, str) -> str
    """Image tag for a model/variant pair, e.g. tolcad-baseline/cadrille:cu118."""
    if slug not in MODEL_SLUGS:
        raise ValueError("unknown model slug %r; expected one of %s"
                         % (slug, ", ".join(MODEL_SLUGS)))
    return "%s/%s:%s" % (IMAGE_NAMESPACE, slug, variant)


def read_items(prompts_path):
    # type: (str) -> List[Dict]
    """Read prompts.jsonl. One JSON object per non-blank line."""
    items = []
    with open(prompts_path, "r") as handle:
        for lineno, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except ValueError as exc:
                raise ValueError("%s line %d is not JSON: %s"
                                 % (prompts_path, lineno, exc))
    return items


def validate_out_dir(out_root, expected_ids):
    # type: (object, Sequence[str]) -> List[str]
    """Return contract violations in an output tree. Empty list means clean.

    A violation is a CONTRACT breach -- the container did not speak the
    protocol. An item whose status is "error" is NOT a violation: the model was
    asked, and it failed, and that is a recorded result.
    """
    root = str(out_root)
    violations = []
    if not os.path.isfile(os.path.join(root, RUN_MANIFEST_FILENAME)):
        violations.append("missing %s" % RUN_MANIFEST_FILENAME)
    for item_id in expected_ids:
        status_path = os.path.join(root, item_id, ITEM_STATUS_FILENAME)
        if not os.path.isfile(status_path):
            violations.append("item %r: missing %s" % (item_id, ITEM_STATUS_FILENAME))
            continue
        with open(status_path, "r") as handle:
            payload = json.load(handle)
        if payload.get("status") not in ITEM_STATUSES:
            violations.append("item %r: status %r not in %s"
                              % (item_id, payload.get("status"), list(ITEM_STATUSES)))
        if payload.get("status") == "ok" and not payload.get("artifacts"):
            violations.append("item %r: status ok but no artifacts listed" % item_id)
    return violations
```

- [ ] **Step 4: Add the import-direction guard**

Append to `tests/test_architecture.py`:

```python
def test_core_does_not_import_the_baseline_harness():
    """`harness/` may import tolcad. tolcad may never import `harness`.

    Same one-directional rule as validation/, for the same reason: the checker
    must stay installable and runnable with no CAD stack, no Docker and no
    baseline weights.
    """
    offenders = []
    for path in sorted(CORE.rglob("*.py")):
        imported = _imported_modules(path)
        if any(m == "harness" or m.startswith("harness.") for m in imported):
            offenders.append(str(path.relative_to(CORE)))
    assert not offenders, (
        "src/tolcad must not import harness: " + ", ".join(offenders)
    )
```

If `CORE` or `_imported_modules` are not in scope at that point in the file, reuse whatever the
existing `validation/` isolation test uses — do not introduce a second helper.

- [ ] **Step 5: Run the tests**

Run: `python -m pytest tests/harness/test_contract.py tests/test_architecture.py -q`
Expected: PASS.
Then `python -m pytest -q` — expected PASS, 428 baseline plus the new tests, tree clean.

- [ ] **Step 6: Commit**

```bash
git add harness/__init__.py harness/contract.py tests/harness/ tests/test_architecture.py
git commit -m "feat: uniform container contract for the nine baseline models"
```

---

### Task 2: The build matrix, and a lint that makes the CUDA `ARG` rule real

**Verified in: Stage 1 (laptop, CPU). Text analysis only — no image is built here.**

**Files:**
- Create: `harness/build_matrix.toml`
- Create: `harness/matrix.py`
- Create: `tests/harness/fixtures/Dockerfile.baked` (negative fixture)
- Create: `tests/harness/fixtures/Dockerfile.good` (positive fixture)
- Test: `tests/harness/test_build_matrix.py`

**Interfaces:**
- Consumes: `harness.contract.MODEL_SLUGS`
- Produces:
  - `VARIANTS: tuple[str, ...] = ("cpu", "cu118", "cu128")`
  - `DEFAULT_VARIANT: str = "cu118"`
  - `load_matrix(path=None) -> dict[str, Variant]` where `Variant` is a frozen dataclass with `base_image: str`, `torch_index_url: str`, `targets: tuple[str, ...]`
  - `build_args(variant: str) -> dict[str, str]` → `{"BASE_IMAGE": ..., "TORCH_INDEX_URL": ...}`
  - `lint_dockerfile(text: str) -> list[str]` — violation strings, `[]` when clean

This is the task that stops the exercise being theatre. If one Dockerfile hardcodes the version
that happens to work on the laptop, that model gets rebuilt from scratch on the workstation and
every hour spent on it bought nothing. The default variant is **`cu118` — the deployment target**,
so a forgotten `--build-arg` lands on Ada, not on Blackwell.

- [ ] **Step 1: Write the failing test**

Create `tests/harness/fixtures/Dockerfile.baked`:

```dockerfile
# Deliberately wrong. The lint MUST reject this file. Do not "fix" it.
FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04
RUN pip install torch==2.7.0 --index-url https://download.pytorch.org/whl/cu128
```

Create `tests/harness/fixtures/Dockerfile.good`:

```dockerfile
ARG BASE_IMAGE=nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04
FROM ${BASE_IMAGE}
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cu118
ARG TORCH_SPEC=torch==2.0.1
RUN pip install --no-cache-dir "${TORCH_SPEC}" --index-url "${TORCH_INDEX_URL}"
```

Create `tests/harness/test_build_matrix.py`:

```python
import pathlib

import pytest

from harness import contract, matrix

REPO = pathlib.Path(__file__).resolve().parents[2]
FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_the_three_variants_exist_and_ada_is_the_default():
    """A forgotten --build-arg must land on the DEPLOYMENT target, not the laptop.

    The laptop is sm_120 and needs CUDA 12.8+; the workstation is sm_89 and does
    not. Defaulting to the laptop's value silently pins a torch that is wrong for
    Ada, and nothing downstream would notice until the workstation rebuild.
    """
    m = matrix.load_matrix()
    assert set(m) == {"cpu", "cu118", "cu128"}
    assert matrix.DEFAULT_VARIANT == "cu118"
    assert "cu118" in m["cu118"].torch_index_url
    assert "cu128" in m["cu128"].torch_index_url
    assert "cpu" in m["cpu"].torch_index_url


def test_build_args_are_exactly_the_two_the_lint_requires():
    assert set(matrix.build_args("cu118")) == {"BASE_IMAGE", "TORCH_INDEX_URL"}


def test_the_lint_rejects_a_baked_dockerfile():
    """The negative fixture proves the lint bites. Without it the lint is a
    test that cannot fail, which is this project's dominant defect shape."""
    violations = matrix.lint_dockerfile(
        (FIXTURES / "Dockerfile.baked").read_text(encoding="utf-8"))
    joined = " | ".join(violations)
    assert "FROM" in joined
    assert "TORCH_INDEX_URL" in joined


def test_the_lint_accepts_a_correct_dockerfile():
    assert matrix.lint_dockerfile(
        (FIXTURES / "Dockerfile.good").read_text(encoding="utf-8")) == []


def test_the_lint_rejects_a_dockerfile_defaulting_to_the_laptop_toolchain():
    text = (FIXTURES / "Dockerfile.good").read_text(encoding="utf-8").replace(
        "https://download.pytorch.org/whl/cu118",
        "https://download.pytorch.org/whl/cu128")
    violations = matrix.lint_dockerfile(text)
    assert any("default" in v for v in violations), violations


@pytest.mark.parametrize("slug", contract.MODEL_SLUGS)
def test_every_existing_model_dockerfile_passes_the_lint(slug):
    """Skips models not yet containerised. Task 11 asserts all nine exist."""
    path = REPO / "harness" / "models" / slug / "Dockerfile"
    if not path.is_file():
        pytest.skip(f"{slug} not containerised yet")
    assert matrix.lint_dockerfile(path.read_text(encoding="utf-8")) == []
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/harness/test_build_matrix.py -q`
Expected: FAIL — `ImportError: cannot import name 'matrix' from 'harness'`.

- [ ] **Step 3: Write the matrix and the lint**

Create `harness/build_matrix.toml`:

```toml
# Single source of truth for the three build variants. See harness/matrix.py.
#
# cu118 is the DEFAULT because it is the deployment target (RTX A6000 Ada,
# sm_89, on both workstations). cu128 exists only for the development laptop
# (RTX 5060, sm_120 Blackwell, which requires CUDA 12.8+) and a green cu128 run
# is NOT Stage 2 evidence -- different architecture, different toolchain.
#
# Stage 1 uses `cpu`. There is no reason to involve a GPU in a build check.
#
# BASE IMAGE TAGS ARE NOT VERIFIED BY THE LINT. Task 2 Step 5 verifies each tag
# resolves with `docker manifest inspect`; if one does not, correct it HERE, in
# this file, and nowhere else.

contract_version = "1.0"
default_variant = "cu118"

[variants.cpu]
base_image = "python:3.11-slim-bookworm"
torch_index_url = "https://download.pytorch.org/whl/cpu"
targets = ["Stage 1 build/import/CLI verification, any machine"]

[variants.cu118]
base_image = "nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04"
torch_index_url = "https://download.pytorch.org/whl/cu118"
targets = ["RTX A6000 Ada (sm_89), RHEL workstation", "RTX A6000 Ada (sm_89), WSL2 workstation"]

[variants.cu128]
base_image = "nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04"
torch_index_url = "https://download.pytorch.org/whl/cu128"
targets = ["RTX 5060 (sm_120), development laptop -- NOT a Stage 2 target"]
```

Create `harness/matrix.py`:

```python
"""Build-variant resolution and the Dockerfile ARG lint.

Host-side only: uses tomllib, so unlike contract.py it never enters an image.
"""

from __future__ import annotations

import pathlib
import re
import tomllib
from dataclasses import dataclass

HERE = pathlib.Path(__file__).resolve().parent
MATRIX_PATH = HERE / "build_matrix.toml"

VARIANTS = ("cpu", "cu118", "cu128")
DEFAULT_VARIANT = "cu118"

# The two ARGs every Dockerfile must expose.
REQUIRED_ARGS = ("BASE_IMAGE", "TORCH_INDEX_URL")

_FROM_RE = re.compile(r"^\s*FROM\s+(\S+)", re.MULTILINE)
_ARG_RE = re.compile(r"^\s*ARG\s+([A-Z_][A-Z0-9_]*)\s*=?\s*(.*)$", re.MULTILINE)
_BAKED_INDEX_RE = re.compile(r"download\.pytorch\.org/whl/(cpu|cu\d{3})")


@dataclass(frozen=True)
class Variant:
    name: str
    base_image: str
    torch_index_url: str
    targets: tuple[str, ...]


def load_matrix(path: pathlib.Path | None = None) -> dict[str, Variant]:
    data = tomllib.loads((path or MATRIX_PATH).read_text(encoding="utf-8"))
    return {
        name: Variant(name=name,
                      base_image=body["base_image"],
                      torch_index_url=body["torch_index_url"],
                      targets=tuple(body.get("targets", ())))
        for name, body in data["variants"].items()
    }


def build_args(variant: str) -> dict[str, str]:
    v = load_matrix()[variant]
    return {"BASE_IMAGE": v.base_image, "TORCH_INDEX_URL": v.torch_index_url}


def lint_dockerfile(text: str) -> list[str]:
    """Return violations of the never-bake-the-toolchain rule. [] means clean."""
    violations: list[str] = []
    args = dict(_ARG_RE.findall(text))

    froms = _FROM_RE.findall(text)
    if not froms:
        violations.append("no FROM instruction found")
    for image in froms:
        if "${BASE_IMAGE}" not in image and "$BASE_IMAGE" not in image:
            violations.append(
                f"FROM {image!r} bakes a base image; use FROM ${{BASE_IMAGE}} "
                f"with `ARG BASE_IMAGE=` declared above it")

    for name in REQUIRED_ARGS:
        if name not in args:
            violations.append(f"missing `ARG {name}=<default>` declaration")

    default_index = args.get("TORCH_INDEX_URL", "").strip().strip('"').strip("'")
    if default_index and "cu118" not in default_index:
        violations.append(
            f"ARG TORCH_INDEX_URL default is {default_index!r}; the default must "
            f"be the cu118 deployment target so a forgotten --build-arg lands on "
            f"Ada (sm_89), not on the laptop (sm_120)")

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "TORCH_INDEX_URL" in stripped:
            continue
        if _BAKED_INDEX_RE.search(stripped):
            violations.append(
                f"literal torch wheel index in {stripped!r}; use "
                f"${{TORCH_INDEX_URL}}")
    return violations
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/harness/test_build_matrix.py -q`
Expected: PASS, with nine `SKIP` from the parametrised Dockerfile test (no model dirs yet).

- [ ] **Step 5: Verify the three base-image tags actually resolve**

The lint checks structure, not existence. Confirm each tag is real before any model depends on it:

```bash
for img in \
  python:3.11-slim-bookworm \
  nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04 \
  nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04 ; do
  echo "== $img"
  docker manifest inspect "$img" > /dev/null && echo OK || echo MISSING
done
```

Expected: three `OK`. If one prints `MISSING`, find the nearest published tag with
`docker search` / the NVIDIA NGC tag list and **edit `harness/build_matrix.toml` only** — the tag
must not appear anywhere else in the repo. NVIDIA renamed the cuDNN suffix between the 11.x and
12.x lines (`cudnn8-runtime` vs `cudnn-runtime`), which is the likeliest cause of a miss. Record
whatever you used in `harness/build_matrix.toml`'s header comment.

- [ ] **Step 6: Commit**

```bash
git add harness/build_matrix.toml harness/matrix.py tests/harness/test_build_matrix.py tests/harness/fixtures/
git commit -m "feat: build matrix and a lint forbidding baked CUDA/torch versions"
```

---

### Task 3: Container runtime abstraction and the one-command-per-model runner

**Verified in: Stage 1 (laptop, Docker) for the docker path. The podman/SELinux/rootless path is
a SPIKE and is NOT verified until Stage 2 — it must be labelled unverified in code and in
`RESULTS.md` until then.**

**Files:**
- Create: `harness/oci.py`
- Create: `harness/runner.py`
- Test: `tests/harness/test_oci.py`, `tests/harness/test_runner.py`

**Interfaces:**
- Consumes: `harness.contract` (`IN_ROOT`, `OUT_ROOT`, `WEIGHTS_ROOT`, `ExitCode`, `image_name`, `validate_out_dir`, `read_items`), `harness.matrix.build_args`
- Produces:
  - `@dataclass(frozen=True) class RuntimeCaps(name: str, rootless: bool, selinux: bool, gpu_flag: tuple[str, ...])`
  - `detect_runtime(explicit: str | None = None) -> str`
  - `probe_caps(runtime: str) -> RuntimeCaps`
  - `build_argv(caps, image, context_dir, variant, extra_args=()) -> list[str]`
  - `run_argv(caps, image, mounts: Sequence[tuple[str, str, str]], command: Sequence[str], device: str) -> list[str]` where each mount is `(host_path, container_path, "ro"|"rw")`
  - `@dataclass(frozen=True) class RunOutcome(slug, variant, device, exit_code, wall_s, violations: list[str], stdout_tail: str, stderr_tail: str)`
  - `run_model(slug, *, variant, device, prompts, out_dir, weights_dir, runtime=None, limit=None, timeout_s=3600) -> RunOutcome`

**SPIKE — *Podman rootless with SELinux volume labels on the RHEL host*. Time box: 2 hours, at the
start of Stage 2. Fallback: if rootless podman cannot mount the weights directory, run podman as
root on that host and record the deviation in `RESULTS.md`; if SELinux relabelling of a
multi-gigabyte weights tree is too slow, mount weights with `:ro,z` once and reuse the label
across runs. Neither fallback changes the contract.** The three things podman needs that Docker
does not: `:z` / `:Z` volume suffixes under SELinux, `--userns=keep-id` so a rootless container's
uid maps to yours and `/out` is writable, and `--device nvidia.com/gpu=all` (CDI) rather than
Docker's `--gpus all`.

- [ ] **Step 1: Write the failing test**

Create `tests/harness/test_oci.py`:

```python
import pathlib

import pytest

from harness import oci

REPO = pathlib.Path(__file__).resolve().parents[2]

DOCKER = oci.RuntimeCaps(name="docker", rootless=False, selinux=False,
                         gpu_flag=("--gpus", "all"))
PODMAN = oci.RuntimeCaps(name="podman", rootless=True, selinux=True,
                         gpu_flag=("--device", "nvidia.com/gpu=all"))


def test_docker_mounts_carry_no_selinux_label():
    argv = oci.run_argv(DOCKER, "img", [("/h/w", "/weights", "ro")], ["x"], "cpu")
    assert "/h/w:/weights:ro" in argv
    assert ":ro,z" not in " ".join(argv)


def test_podman_mounts_carry_the_selinux_label_and_keep_id():
    argv = oci.run_argv(PODMAN, "img", [("/h/w", "/weights", "ro")], ["x"], "cpu")
    assert "/h/w:/weights:ro,z" in argv
    assert "--userns=keep-id" in argv


def test_cpu_runs_request_no_gpu_on_either_runtime():
    """Stage 1 is CPU-only. A GPU flag leaking into Stage 1 would make a laptop
    (sm_120) result look like evidence about the workstation (sm_89)."""
    for caps in (DOCKER, PODMAN):
        argv = oci.run_argv(caps, "img", [], ["x"], "cpu")
        assert "--gpus" not in argv
        assert "nvidia.com/gpu=all" not in argv


def test_gpu_runs_use_the_runtime_specific_flag():
    assert "--gpus" in oci.run_argv(DOCKER, "img", [], ["x"], "cuda:0")
    assert "nvidia.com/gpu=all" in oci.run_argv(PODMAN, "img", [], ["x"], "cuda:0")


def test_build_argv_passes_both_required_args():
    argv = oci.build_argv(DOCKER, "img", "/ctx", "cu118")
    joined = " ".join(argv)
    assert "BASE_IMAGE=" in joined and "TORCH_INDEX_URL=" in joined
    assert "cu118" in joined


def test_no_module_outside_oci_shells_out_to_docker_directly():
    """Docker-only semantics must not leak. The RHEL host may be podman."""
    offenders = []
    for path in sorted((REPO / "harness").rglob("*.py")):
        if path.name == "oci.py":
            continue
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if '"docker"' in line or "'docker'" in line:
                offenders.append(f"{path.name}:{lineno}")
    assert not offenders, (
        "raw docker invocations outside harness/oci.py: " + ", ".join(offenders))
```

Create `tests/harness/test_runner.py`:

```python
import json
import pathlib

from harness import contract, oci, runner


def _fake_container(out_dir: pathlib.Path, ids, status="ok"):
    """Write what a well-behaved container would have written."""
    (out_dir / contract.RUN_MANIFEST_FILENAME).write_text(
        json.dumps({"model": "cadrille"}), encoding="utf-8")
    for item_id in ids:
        d = out_dir / item_id
        d.mkdir(parents=True, exist_ok=True)
        (d / contract.STEP_ARTIFACT).write_text("ISO-10303-21;", encoding="utf-8")
        (d / contract.ITEM_STATUS_FILENAME).write_text(json.dumps(
            {"id": item_id, "status": status, "error": None,
             "artifacts": [contract.STEP_ARTIFACT], "wall_s": 0.1}),
            encoding="utf-8")


def test_run_model_reports_ok_when_the_container_honours_the_contract(
        tmp_path, monkeypatch):
    prompts = tmp_path / "p.jsonl"
    prompts.write_text('{"id": "a", "seed": 0, "prompt": "a bracket"}\n',
                       encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()

    def fake_invoke(argv, timeout_s):
        _fake_container(out, ["a"])
        return 0, "", ""

    monkeypatch.setattr(runner, "_invoke", fake_invoke)
    monkeypatch.setattr(oci, "probe_caps", lambda name: oci.RuntimeCaps(
        name="docker", rootless=False, selinux=False, gpu_flag=("--gpus", "all")))

    outcome = runner.run_model("cadrille", variant="cpu", device="cpu",
                               prompts=prompts, out_dir=out,
                               weights_dir=tmp_path, runtime="docker")
    assert outcome.exit_code == contract.ExitCode.OK
    assert outcome.violations == []


def test_run_model_reports_a_contract_violation_when_output_is_missing(
        tmp_path, monkeypatch):
    """Exit 0 with no output is the worst case: it looks like success.

    This is the check that separates `the model crashed` from `the model
    produced bad geometry`. If it cannot fail, neither distinction survives.
    """
    prompts = tmp_path / "p.jsonl"
    prompts.write_text('{"id": "a", "seed": 0, "prompt": "a bracket"}\n',
                       encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()

    monkeypatch.setattr(runner, "_invoke", lambda argv, timeout_s: (0, "", ""))
    monkeypatch.setattr(oci, "probe_caps", lambda name: oci.RuntimeCaps(
        name="docker", rootless=False, selinux=False, gpu_flag=("--gpus", "all")))

    outcome = runner.run_model("cadrille", variant="cpu", device="cpu",
                               prompts=prompts, out_dir=out,
                               weights_dir=tmp_path, runtime="docker")
    assert outcome.exit_code == contract.ExitCode.CONTRACT_VIOLATION
    assert outcome.violations


def test_run_model_preserves_an_uncaught_crash_code(tmp_path, monkeypatch):
    """137 is an OOM kill. It must not be laundered into one of our codes."""
    prompts = tmp_path / "p.jsonl"
    prompts.write_text('{"id": "a", "seed": 0}\n', encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()

    monkeypatch.setattr(runner, "_invoke", lambda argv, timeout_s: (137, "", "Killed"))
    monkeypatch.setattr(oci, "probe_caps", lambda name: oci.RuntimeCaps(
        name="docker", rootless=False, selinux=False, gpu_flag=("--gpus", "all")))

    outcome = runner.run_model("cadrille", variant="cpu", device="cpu",
                               prompts=prompts, out_dir=out,
                               weights_dir=tmp_path, runtime="docker")
    assert outcome.exit_code == 137
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/harness/test_oci.py tests/harness/test_runner.py -q`
Expected: FAIL — `cannot import name 'oci'`.

- [ ] **Step 3: Implement the runtime layer**

Create `harness/oci.py`:

```python
"""docker / podman abstraction. The RHEL host may be rootless podman under SELinux.

Every container invocation in this repo goes through this module;
tests/harness/test_oci.py fails the suite if a raw "docker" string appears
anywhere else under harness/.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import Sequence

from harness.matrix import build_args


@dataclass(frozen=True)
class RuntimeCaps:
    name: str
    rootless: bool
    selinux: bool
    gpu_flag: tuple[str, ...]


def detect_runtime(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    for candidate in ("docker", "podman"):
        if shutil.which(candidate):
            return candidate
    raise RuntimeError(
        "no container runtime found; install docker or podman, or pass "
        "--runtime explicitly")


def probe_caps(runtime: str) -> RuntimeCaps:
    """Ask the runtime about itself. Never guess from the binary name alone."""
    rootless = False
    selinux = False
    try:
        info = subprocess.run(
            [runtime, "info", "--format", "{{json .}}"],
            capture_output=True, text=True, timeout=60)
        blob = info.stdout
        rootless = '"rootless":true' in blob.replace(" ", "").lower()
        selinux = "selinux" in blob.lower()
    except (OSError, subprocess.SubprocessError):
        pass
    gpu_flag = (("--device", "nvidia.com/gpu=all") if runtime == "podman"
                else ("--gpus", "all"))
    return RuntimeCaps(name=runtime, rootless=rootless, selinux=selinux,
                       gpu_flag=gpu_flag)


def _mount_spec(caps: RuntimeCaps, host: str, target: str, mode: str) -> str:
    suffix = f"{mode},z" if caps.selinux else mode
    return f"{host}:{target}:{suffix}"


def build_argv(caps: RuntimeCaps, image: str, context_dir: str, variant: str,
               extra_args: Sequence[str] = ()) -> list[str]:
    argv = [caps.name, "build", "-t", image]
    for key, value in build_args(variant).items():
        argv += ["--build-arg", f"{key}={value}"]
    argv += list(extra_args)
    argv += ["-f", f"{context_dir}/Dockerfile", context_dir]
    return argv


def run_argv(caps: RuntimeCaps, image: str,
             mounts: Sequence[tuple[str, str, str]],
             command: Sequence[str], device: str) -> list[str]:
    argv = [caps.name, "run", "--rm", "--network=none"]
    if caps.rootless:
        argv.append("--userns=keep-id")
    if device != "cpu":
        argv += list(caps.gpu_flag)
    for host, target, mode in mounts:
        argv += ["-v", _mount_spec(caps, host, target, mode)]
    argv.append(image)
    argv += list(command)
    return argv
```

`--network=none` is deliberate: a container that reaches the internet at inference time is not
reproducible, and a model that silently downloads a checkpoint on first use would otherwise pass
Stage 1 while having no pinned weights at all. If a model fails only under `--network=none`, that
is a finding, and it goes in `MODEL.md`.

Create `harness/runner.py`:

```python
"""One command per model. `python -m harness.runner --model cadrille ...`"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import time
from dataclasses import dataclass, field

from harness import contract, matrix, oci


@dataclass(frozen=True)
class RunOutcome:
    slug: str
    variant: str
    device: str
    exit_code: int
    wall_s: float
    violations: list[str] = field(default_factory=list)
    stdout_tail: str = ""
    stderr_tail: str = ""


def _invoke(argv: list[str], timeout_s: int) -> tuple[int, str, str]:
    """Seam. tests/harness/test_runner.py monkeypatches this."""
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_s)
    return proc.returncode, proc.stdout, proc.stderr


def run_model(slug: str, *, variant: str, device: str,
              prompts: pathlib.Path, out_dir: pathlib.Path,
              weights_dir: pathlib.Path, runtime: str | None = None,
              limit: int | None = None, timeout_s: int = 3600) -> RunOutcome:
    image = contract.image_name(slug, variant)
    caps = oci.probe_caps(oci.detect_runtime(runtime))

    prompts = pathlib.Path(prompts).resolve()
    out_dir = pathlib.Path(out_dir).resolve()
    weights_dir = pathlib.Path(weights_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    items = contract.read_items(str(prompts))
    if limit is not None:
        items = items[:limit]
    expected_ids = [item["id"] for item in items]

    command = ["python", f"{contract.CODE_ROOT}/entrypoint.py",
               "--in", f"{contract.IN_ROOT}/{prompts.name}",
               "--out", contract.OUT_ROOT,
               "--weights", contract.WEIGHTS_ROOT,
               "--device", device]
    if limit is not None:
        command += ["--limit", str(limit)]

    argv = oci.run_argv(
        caps, image,
        [(str(prompts.parent), contract.IN_ROOT, "ro"),
         (str(weights_dir), contract.WEIGHTS_ROOT, "ro"),
         (str(out_dir), contract.OUT_ROOT, "rw")],
        command, device)

    started = time.time()
    code, stdout, stderr = _invoke(argv, timeout_s)
    wall_s = time.time() - started

    violations = contract.validate_out_dir(out_dir, expected_ids)
    # A clean exit with a broken output tree is the dangerous case: it reads as
    # success everywhere downstream. Promote it.
    if code == 0 and violations:
        code = int(contract.ExitCode.CONTRACT_VIOLATION)

    return RunOutcome(slug=slug, variant=variant, device=device, exit_code=code,
                      wall_s=wall_s, violations=violations,
                      stdout_tail=stdout[-4000:], stderr_tail=stderr[-4000:])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=contract.MODEL_SLUGS)
    parser.add_argument("--variant", default=matrix.DEFAULT_VARIANT,
                        choices=matrix.VARIANTS)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--prompts", default="harness/prompts/smoke.jsonl")
    parser.add_argument("--out", default=None)
    parser.add_argument("--weights", default=None)
    parser.add_argument("--runtime", default=None, choices=(None, "docker", "podman"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--timeout-s", type=int, default=3600)
    args = parser.parse_args(argv)

    repo = pathlib.Path(__file__).resolve().parent.parent
    out = pathlib.Path(args.out or repo / "harness" / "out" / args.model)
    weights = pathlib.Path(
        args.weights or repo / "harness" / "weights" / "payload" / args.model)

    outcome = run_model(args.model, variant=args.variant, device=args.device,
                        prompts=pathlib.Path(args.prompts), out_dir=out,
                        weights_dir=weights, runtime=args.runtime,
                        limit=args.limit, timeout_s=args.timeout_s)
    print(json.dumps({
        "model": outcome.slug, "variant": outcome.variant,
        "device": outcome.device, "exit_code": int(outcome.exit_code),
        "wall_s": round(outcome.wall_s, 2), "violations": outcome.violations,
    }, indent=2))
    if outcome.stderr_tail:
        print(outcome.stderr_tail, file=sys.stderr)
    return int(outcome.exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/harness/ -q`
Expected: PASS.

- [ ] **Step 5: Record the podman path as unverified**

Add to `harness/oci.py`, immediately under the module docstring:

```python
# STAGE STATUS. The docker path is exercised on the development laptop from
# Task 5 onward. The podman path -- SELinux `:z`, rootless `--userns=keep-id`,
# CDI `--device nvidia.com/gpu=all` -- is UNVERIFIED until Stage 2 runs on the
# RHEL workstation. tests/harness/test_oci.py checks the argv we CONSTRUCT for
# podman; it cannot check that podman accepts it. Do not describe podman
# support as working, in RESULTS.md or anywhere else, until Task 11 says so.
```

- [ ] **Step 6: Commit**

```bash
git add harness/oci.py harness/runner.py tests/harness/test_oci.py tests/harness/test_runner.py
git commit -m "feat: docker/podman abstraction and the per-model runner"
```

---

### Task 4: Weight manifest and fetch script

**Verified in: Stage 1 (laptop, CPU).**

**Files:**
- Create: `harness/weights/MANIFEST.toml`
- Create: `scripts/fetch_baseline_weights.py`
- Modify: `.gitignore`
- Test: `tests/harness/test_fetch_weights.py`

**Interfaces:**
- Consumes: `harness.contract.MODEL_SLUGS`
- Produces:
  - `load_manifest(path=None) -> dict[str, list[Artifact]]` with `Artifact(filename, url, sha256, bytes)`
  - `sha256_of(path) -> str`
  - `verify(slug, payload_dir) -> list[str]` — failures, `[]` when clean
  - `main(argv=None) -> int` — CLI, exit 1 on any mismatch

House style, taken from `scripts/fetch_nist_pmi.py`: tracked script, tracked manifest, gitignored
payload, and a **count-mismatch guard** (`fetch_nist_pmi.py:56-63`) that returns non-zero and says
*"the upstream archive may have changed; verify before using these as an oracle."* The same
sentence applies with more force here: a silently-changed checkpoint is a silently-changed
baseline number.

The manifest starts **empty of artifacts** and is filled in one model at a time by Tasks 5, 6, 9
and 10, because none of these URLs can be known without network access. What Task 4 delivers is
the schema, the verifier and the guard — all of which are testable today with synthetic data.

- [ ] **Step 1: Write the failing test**

Create `tests/harness/test_fetch_weights.py`:

```python
import hashlib
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import fetch_baseline_weights as fbw  # noqa: E402

from harness import contract  # noqa: E402


def test_manifest_has_a_section_for_every_slug():
    """A model missing from the manifest is a model nobody will remember to fetch."""
    manifest = fbw.load_manifest()
    assert set(manifest) == set(contract.MODEL_SLUGS)


def test_every_declared_artifact_has_a_full_length_sha256():
    for slug, artifacts in fbw.load_manifest().items():
        for art in artifacts:
            assert len(art.sha256) == 64, f"{slug}/{art.filename}"
            assert int(art.sha256, 16) >= 0, f"{slug}/{art.filename} not hex"
            assert art.bytes > 0, f"{slug}/{art.filename}"


def test_verify_reports_a_missing_file(tmp_path, monkeypatch):
    art = fbw.Artifact(filename="w.bin", url="https://example.invalid/w.bin",
                       sha256="0" * 64, bytes=3)
    monkeypatch.setattr(fbw, "load_manifest", lambda path=None: {"cadrille": [art]})
    failures = fbw.verify("cadrille", tmp_path)
    assert any("missing" in f for f in failures)


def test_verify_reports_a_checksum_mismatch(tmp_path, monkeypatch):
    """The guard that matters. A changed checkpoint is a changed baseline number."""
    payload = tmp_path / "w.bin"
    payload.write_bytes(b"abc")
    art = fbw.Artifact(filename="w.bin", url="https://example.invalid/w.bin",
                       sha256="1" * 64, bytes=3)
    monkeypatch.setattr(fbw, "load_manifest", lambda path=None: {"cadrille": [art]})
    failures = fbw.verify("cadrille", tmp_path)
    assert any("sha256" in f for f in failures)


def test_verify_accepts_a_correct_payload(tmp_path, monkeypatch):
    payload = tmp_path / "w.bin"
    payload.write_bytes(b"abc")
    digest = hashlib.sha256(b"abc").hexdigest()
    art = fbw.Artifact(filename="w.bin", url="https://example.invalid/w.bin",
                       sha256=digest, bytes=3)
    monkeypatch.setattr(fbw, "load_manifest", lambda path=None: {"cadrille": [art]})
    assert fbw.verify("cadrille", tmp_path) == []


def test_weight_payload_is_gitignored():
    ignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert "harness/weights/payload/" in ignore
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/harness/test_fetch_weights.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'fetch_baseline_weights'`.

- [ ] **Step 3: Write the manifest and the script**

Create `harness/weights/MANIFEST.toml`:

```toml
# Baseline model weights. TRACKED manifest, GITIGNORED payload -- the same
# pattern as papers/literature/ (index tracked, ~1 GB of PDFs ignored) and
# data/nist_pmi/ (script tracked, archive ignored).
#
# Fetch with:  python scripts/fetch_baseline_weights.py [--model <slug>]
# Payload lands in harness/weights/payload/<slug>/.
#
# Each artifact needs url, sha256 (64 hex chars) and bytes. The sha256 is not
# decoration: a silently-republished checkpoint is a silently-changed baseline
# number, and there is no other way to notice.
#
# `artifacts = []` means "not yet discovered" -- the fetch script exits 1 for
# that model and says so. Tasks 5, 6, 9 and 10 fill these in as each model's
# spike resolves. DO NOT invent a URL to make a section look complete.

[cadrille]
artifacts = []

[deepcad]
artifacts = []

[brepgen]
artifacts = []

[text2cad]
artifacts = []

[cad-recode]
artifacts = []

[dtgbrepgen]
artifacts = []

[hola]
artifacts = []

[cad-coder-mit]
artifacts = []

[text-to-cadquery]
artifacts = []
```

Create `scripts/fetch_baseline_weights.py`:

```python
#!/usr/bin/env python
"""Fetch and verify baseline-model weights declared in harness/weights/MANIFEST.toml.

Payload lands in harness/weights/payload/<slug>/ and is gitignored; this script
and the manifest are tracked, so the weight set is reproducible from the repo
alone. Same shape as scripts/fetch_nist_pmi.py, including its count-mismatch
guard: if the number of verified artifacts does not equal the number declared,
this exits 1 rather than letting a partial fetch look like a complete one.

Usage:
    python scripts/fetch_baseline_weights.py                # all nine
    python scripts/fetch_baseline_weights.py --model cadrille
    python scripts/fetch_baseline_weights.py --verify-only
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys
import tomllib
import urllib.request
from dataclasses import dataclass

REPO = pathlib.Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO / "harness" / "weights" / "MANIFEST.toml"
PAYLOAD_ROOT = REPO / "harness" / "weights" / "payload"
USER_AGENT = "tolcad-research/0.1 (academic use)"
CHUNK = 1 << 20


@dataclass(frozen=True)
class Artifact:
    filename: str
    url: str
    sha256: str
    bytes: int


def load_manifest(path: pathlib.Path | None = None) -> dict[str, list[Artifact]]:
    data = tomllib.loads((path or MANIFEST_PATH).read_text(encoding="utf-8"))
    return {
        slug: [Artifact(**a) for a in body.get("artifacts", [])]
        for slug, body in data.items()
    }


def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(slug: str, payload_dir: pathlib.Path) -> list[str]:
    failures = []
    for art in load_manifest().get(slug, []):
        target = pathlib.Path(payload_dir) / art.filename
        if not target.is_file():
            failures.append(f"{slug}/{art.filename}: missing")
            continue
        actual_bytes = target.stat().st_size
        if actual_bytes != art.bytes:
            failures.append(
                f"{slug}/{art.filename}: {actual_bytes} bytes, manifest says {art.bytes}")
        actual = sha256_of(target)
        if actual != art.sha256:
            failures.append(
                f"{slug}/{art.filename}: sha256 {actual} != manifest {art.sha256}")
    return failures


def _download(art: Artifact, target: pathlib.Path) -> None:
    print(f"downloading {art.url} -> {target}")
    request = urllib.request.Request(art.url, headers={"User-Agent": USER_AGENT})
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(request) as response, target.open("wb") as out:
        while True:
            block = response.read(CHUNK)
            if not block:
                break
            out.write(block)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=None)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args(argv)

    manifest = load_manifest()
    slugs = [args.model] if args.model else sorted(manifest)

    declared = 0
    verified = 0
    undeclared: list[str] = []
    problems: list[str] = []

    for slug in slugs:
        artifacts = manifest.get(slug)
        if artifacts is None:
            problems.append(f"{slug}: no manifest section")
            continue
        if not artifacts:
            undeclared.append(slug)
            continue
        payload_dir = PAYLOAD_ROOT / slug
        for art in artifacts:
            declared += 1
            target = payload_dir / art.filename
            if not args.verify_only and not target.is_file():
                _download(art, target)
        failures = verify(slug, payload_dir)
        problems.extend(failures)
        verified += len(artifacts) - len({f.split(":")[0] for f in failures})

    for slug in undeclared:
        print(f"NOT YET DISCOVERED: {slug} declares no artifacts", file=sys.stderr)
    for problem in problems:
        print(f"FAIL: {problem}", file=sys.stderr)

    print(f"declared={declared} verified={verified} "
          f"undeclared_models={len(undeclared)} problems={len(problems)}")

    # Count-mismatch guard, mirroring scripts/fetch_nist_pmi.py:56-63. A partial
    # fetch must never read as a complete one.
    if verified != declared:
        print(f"WARNING: expected {declared} verified artifacts, got {verified}. "
              f"The upstream release may have changed; verify before using these "
              f"weights for any published number.", file=sys.stderr)
        return 1
    if undeclared or problems:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Extend `.gitignore`**

Append:

```gitignore
# Baseline model weights: multi-GB, reproducible via
# scripts/fetch_baseline_weights.py against the tracked
# harness/weights/MANIFEST.toml. Same pattern as papers/literature/*.pdf.
harness/weights/payload/

# Harness run outputs and synthesised conditioning inputs: regenerable.
harness/out/
harness/prompts/steps/
harness/prompts/clouds/
```

- [ ] **Step 5: Run the tests**

Run: `python -m pytest tests/harness/test_fetch_weights.py -q`
Expected: PASS. `test_every_declared_artifact_has_a_full_length_sha256` passes vacuously today —
there are no artifacts yet — and starts biting in Task 5. Note that in the commit message so the
next reader knows it is temporarily vacuous by construction, not by accident.

Then: `python scripts/fetch_baseline_weights.py --verify-only`
Expected: exit 1, nine `NOT YET DISCOVERED` lines. That is the correct state today.

- [ ] **Step 6: Commit**

```bash
git add harness/weights/MANIFEST.toml scripts/fetch_baseline_weights.py .gitignore tests/harness/test_fetch_weights.py
git commit -m "feat: tracked weight manifest with sha256 pins and a count-mismatch guard

The per-artifact assertions are vacuous until Task 5 lands the first real
entry; every section is declared with artifacts = [] and the fetch script
exits 1 for each, so the vacuity is visible rather than silent."
```

---

### Task 5: Pilot A — cadrille. Prove the happy path and lock the contract

**Verified in: Stage 1 (laptop, CPU). Explicitly NOT Stage 2.**

**Files:**
- Create: `harness/entrypoint.py`
- Create: `harness/make_inputs.py`
- Create: `harness/prompts/smoke.jsonl`
- Create: `harness/models/cadrille/{Dockerfile,adapter.py,requirements.lock.txt,MODEL.md}`
- Modify: `harness/weights/MANIFEST.toml`
- Test: `tests/harness/test_entrypoint.py`

**Interfaces:**
- Consumes: everything from Tasks 1–4
- Produces:
  - The **adapter interface** every remaining model implements:
    - `INPUT_MODALITY: str` — one of `contract.MODALITIES`
    - `UPSTREAM_COMMIT: str` — the pinned upstream git sha
    - `load_model(weights_dir: pathlib.Path, device: str) -> object`
    - `generate(model: object, item: dict, out_dir: pathlib.Path) -> list[str]` — returns the artifact filenames written inside `out_dir`; may raise, and a raise is recorded as that item's error rather than killing the run
  - `harness/entrypoint.py` — `main(argv=None) -> int`, honouring `ExitCode`
  - `make_inputs.main()` — writes `harness/prompts/steps/<id>.step` and `harness/prompts/clouds/<id>.npy`

cadrille (2505.22914) is the pilot because it is recent enough to plausibly use a modern PyTorch,
so it exercises the happy path and forces every interface decision to be made against something
real. Nothing about the design is settled until one model has actually run through it.

**SPIKE — *Point-cloud conditioning inputs for the baseline harness*. Time box: 2 hours.** Several
baselines are point-cloud conditioned. Step 3 below synthesises clouds by exporting STL from the
existing generator and area-weighted-sampling its triangles, which is fully specified and uses
only `cadquery.exporters.export` plus numpy. **Fallback if `exporters.export` cannot infer STL from
the extension:** pass `exportType="STL"` explicitly. **Fallback if a model wants a different point
count or normalisation:** `make_inputs.py` takes `--n-points` and `--normalise {unit_sphere,none}`;
record the model's requirement in its `MODEL.md` and regenerate. Do not change the contract.

- [ ] **Step 1: Write the failing test**

Create `tests/harness/test_entrypoint.py`:

```python
"""The entrypoint is the same code in all nine images. Test it on the host."""

import json
import pathlib
import subprocess
import sys
import textwrap

REPO = pathlib.Path(__file__).resolve().parents[2]
ENTRYPOINT = REPO / "harness" / "entrypoint.py"

GOOD_ADAPTER = textwrap.dedent('''
    INPUT_MODALITY = "text"
    UPSTREAM_COMMIT = "0" * 40

    def load_model(weights_dir, device):
        return {"device": device}

    def generate(model, item, out_dir):
        (out_dir / "model.py").write_text(
            "import cadquery as cq\\nresult = cq.Workplane().box(1, 1, 1)\\n",
            encoding="utf-8")
        return ["model.py"]
''')

RAISING_ADAPTER = textwrap.dedent('''
    INPUT_MODALITY = "text"
    UPSTREAM_COMMIT = "0" * 40

    def load_model(weights_dir, device):
        return None

    def generate(model, item, out_dir):
        raise RuntimeError("the model exploded")
''')

BROKEN_IMPORT_ADAPTER = "import a_package_that_does_not_exist\n"


def _stage(tmp_path, adapter_src):
    code = tmp_path / "code"
    code.mkdir()
    (code / "entrypoint.py").write_bytes(ENTRYPOINT.read_bytes())
    (code / "contract.py").write_bytes(
        (REPO / "harness" / "contract.py").read_bytes())
    (code / "adapter.py").write_text(adapter_src, encoding="utf-8")

    prompts = tmp_path / "prompts.jsonl"
    prompts.write_text('{"id": "a", "seed": 0, "prompt": "a bracket"}\n',
                       encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    weights = tmp_path / "weights"
    weights.mkdir()
    return code, prompts, out, weights


def _run(code, prompts, out, weights):
    return subprocess.run(
        [sys.executable, str(code / "entrypoint.py"),
         "--in", str(prompts), "--out", str(out),
         "--weights", str(weights), "--device", "cpu",
         "--model-slug", "cadrille"],
        capture_output=True, text=True)


def test_a_working_adapter_exits_zero_and_writes_the_contract(tmp_path):
    proc = _run(*_stage(tmp_path, GOOD_ADAPTER))
    out = tmp_path / "out"
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((out / "run.json").read_text(encoding="utf-8"))
    assert manifest["n_ok"] == 1 and manifest["n_error"] == 0
    status = json.loads((out / "a" / "status.json").read_text(encoding="utf-8"))
    assert status["status"] == "ok" and status["artifacts"] == ["model.py"]


def test_a_raising_adapter_still_exits_and_records_the_error(tmp_path):
    """A model that fails every item is a RESULT, not a harness crash.

    Exit code 4 (NO_OUTPUT) says the contract was honoured and nothing was
    produced -- which is exactly the finding the paper needs to distinguish
    from `produced bad geometry`.
    """
    proc = _run(*_stage(tmp_path, RAISING_ADAPTER))
    out = tmp_path / "out"
    assert proc.returncode == 4, (proc.returncode, proc.stderr)
    status = json.loads((out / "a" / "status.json").read_text(encoding="utf-8"))
    assert status["status"] == "error"
    assert "the model exploded" in status["error"]


def test_an_unimportable_adapter_is_an_environment_failure(tmp_path):
    proc = _run(*_stage(tmp_path, BROKEN_IMPORT_ADAPTER))
    assert proc.returncode == 3, (proc.returncode, proc.stderr)
    assert (tmp_path / "out" / "run.json").is_file(), (
        "the run manifest must exist even when the adapter cannot import")


def test_self_check_needs_no_weights_and_no_model(tmp_path):
    code, prompts, out, weights = _stage(tmp_path, GOOD_ADAPTER)
    proc = subprocess.run(
        [sys.executable, str(code / "entrypoint.py"), "--self-check",
         "--model-slug", "cadrille"],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "contract_version" in proc.stdout
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/harness/test_entrypoint.py -q`
Expected: FAIL — `harness/entrypoint.py` does not exist, so `_stage` raises `FileNotFoundError`.

- [ ] **Step 3: Write the entrypoint and the input synthesiser**

Create `harness/entrypoint.py`:

```python
#!/usr/bin/env python
"""Uniform in-container entrypoint. COPYed unchanged into all nine images.

STDLIB ONLY, PYTHON 3.7 COMPATIBLE -- see harness/contract.py's header. The one
non-stdlib import is the per-model `adapter`, imported lazily AFTER the run
manifest directory exists, so an import failure is recorded rather than silent.

The entrypoint owns the whole contract: argument parsing, per-item status files,
the run manifest and the exit codes. No per-model code may touch them. That is
what makes nine models comparable.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import contract  # noqa: E402  (COPYed alongside this file)


def _write_json(path, payload):
    with open(path, "w") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _self_check(slug, device):
    info = {"contract_version": contract.CONTRACT_VERSION, "model": slug,
            "device": device, "python": sys.version.split()[0]}
    try:
        import adapter
        info["input_modality"] = adapter.INPUT_MODALITY
        info["upstream_commit"] = adapter.UPSTREAM_COMMIT
    except Exception as exc:  # noqa: BLE001
        info["adapter_error"] = "%s: %s" % (type(exc).__name__, exc)
    try:
        import torch
        info["torch"] = torch.__version__
        info["cuda_available"] = bool(torch.cuda.is_available())
    except Exception as exc:  # noqa: BLE001
        info["torch_error"] = "%s: %s" % (type(exc).__name__, exc)
    print(json.dumps(info, indent=2, sort_keys=True))
    return 0 if "adapter_error" not in info else int(contract.ExitCode.ENVIRONMENT)


def main(argv=None):
    parser = argparse.ArgumentParser(description="tolcad baseline entrypoint")
    parser.add_argument("--in", dest="in_path",
                        default=contract.IN_ROOT + "/" + contract.PROMPTS_FILENAME)
    parser.add_argument("--out", dest="out_root", default=contract.OUT_ROOT)
    parser.add_argument("--weights", dest="weights_root",
                        default=contract.WEIGHTS_ROOT)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--model-slug", default="unknown")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)

    if args.self_check:
        return _self_check(args.model_slug, args.device)

    out_root = args.out_root
    if not os.path.isdir(out_root):
        os.makedirs(out_root)

    manifest = {
        "model": args.model_slug,
        "image": os.environ.get("TOLCAD_IMAGE", ""),
        "contract_version": contract.CONTRACT_VERSION,
        "device": args.device,
        "input_modality": "unknown",
        "n_requested": 0, "n_ok": 0, "n_error": 0, "n_skipped": 0,
        "weights_sha256": os.environ.get("TOLCAD_WEIGHTS_SHA256", ""),
        "upstream_commit": "",
        "extra": {},
    }
    manifest_path = os.path.join(out_root, contract.RUN_MANIFEST_FILENAME)

    try:
        import adapter
    except Exception as exc:  # noqa: BLE001
        manifest["extra"]["adapter_import_error"] = traceback.format_exc()[-4000:]
        _write_json(manifest_path, manifest)
        print("ADAPTER IMPORT FAILED: %s" % exc, file=sys.stderr)
        return int(contract.ExitCode.ENVIRONMENT)

    manifest["input_modality"] = adapter.INPUT_MODALITY
    manifest["upstream_commit"] = adapter.UPSTREAM_COMMIT

    items = contract.read_items(args.in_path)
    if args.limit is not None:
        items = items[:args.limit]
    manifest["n_requested"] = len(items)

    try:
        model = adapter.load_model(args.weights_root, args.device)
    except Exception as exc:  # noqa: BLE001
        manifest["extra"]["load_model_error"] = traceback.format_exc()[-4000:]
        _write_json(manifest_path, manifest)
        print("LOAD FAILED: %s" % exc, file=sys.stderr)
        return int(contract.ExitCode.ENVIRONMENT)

    total_artifacts = 0
    for item in items:
        item_dir = os.path.join(out_root, item["id"])
        if not os.path.isdir(item_dir):
            os.makedirs(item_dir)
        started = time.time()
        try:
            artifacts = adapter.generate(model, item, _PathLike(item_dir))
            status = "ok" if artifacts else "error"
            error = None if artifacts else "adapter returned no artifacts"
            manifest["n_ok" if artifacts else "n_error"] += 1
            total_artifacts += len(artifacts)
        except Exception:  # noqa: BLE001
            artifacts = []
            status = "error"
            error = traceback.format_exc()[-4000:]
            manifest["n_error"] += 1
        _write_json(os.path.join(item_dir, contract.ITEM_STATUS_FILENAME), {
            "id": item["id"], "status": status, "error": error,
            "artifacts": list(artifacts), "wall_s": round(time.time() - started, 3),
        })

    _write_json(manifest_path, manifest)

    violations = contract.validate_out_dir(out_root, [i["id"] for i in items])
    if violations:
        for v in violations:
            print("CONTRACT VIOLATION: %s" % v, file=sys.stderr)
        return int(contract.ExitCode.CONTRACT_VIOLATION)
    if total_artifacts == 0:
        print("model produced zero artifacts across %d items" % len(items),
              file=sys.stderr)
        return int(contract.ExitCode.NO_OUTPUT)
    return int(contract.ExitCode.OK)


class _PathLike(str):
    """A str that also answers `/` and `.write_text`, so adapters can use either.

    pathlib exists in 3.7, but some 2021-era environments patch it oddly; this
    keeps the adapter API pleasant without importing pathlib in the hot path.
    """

    def __truediv__(self, other):
        return _PathLike(os.path.join(str(self), str(other)))

    def write_text(self, text, encoding="utf-8"):
        with open(str(self), "w") as handle:
            handle.write(text)

    def write_bytes(self, data):
        with open(str(self), "wb") as handle:
            handle.write(data)


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `harness/make_inputs.py`:

```python
"""Synthesise the conditioning inputs the smoke set references.

Text prompts are tracked in harness/prompts/smoke.jsonl. The STEP and
point-cloud payloads are regenerable and gitignored, exactly like the NIST
archive: the recipe is tracked, the bytes are not.

Requires `pip install -e ".[gen]"`. Run:  python -m harness.make_inputs
"""

from __future__ import annotations

import argparse
import json
import pathlib
import struct

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
PROMPTS = HERE / "prompts" / "smoke.jsonl"


def _read_binary_stl(path: pathlib.Path) -> np.ndarray:
    """Return an (n, 3, 3) array of triangle vertices from a binary STL."""
    data = path.read_bytes()
    (count,) = struct.unpack("<I", data[80:84])
    tris = np.empty((count, 3, 3), dtype=np.float64)
    offset = 84
    for i in range(count):
        values = struct.unpack("<12f", data[offset:offset + 48])
        tris[i] = np.asarray(values[3:12], dtype=np.float64).reshape(3, 3)
        offset += 50
    return tris


def _sample_surface(tris: np.ndarray, n_points: int, rng) -> np.ndarray:
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    areas = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    probs = areas / areas.sum()
    idx = rng.choice(len(tris), size=n_points, p=probs)
    u = rng.random((n_points, 1))
    v = rng.random((n_points, 1))
    flip = (u + v) > 1.0
    u[flip] = 1.0 - u[flip]
    v[flip] = 1.0 - v[flip]
    return a[idx] + u * (b[idx] - a[idx]) + v * (c[idx] - a[idx])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-points", type=int, default=2048)
    parser.add_argument("--normalise", choices=("unit_sphere", "none"),
                        default="unit_sphere")
    parser.add_argument("--out", default=str(HERE / "prompts"))
    args = parser.parse_args(argv)

    import cadquery as cq  # noqa: F401  (imported for its side effect on OCP)
    from tolcad.gen.build import build_assembly
    from tolcad.gen.sampler import sample_assembly

    out = pathlib.Path(args.out)
    (out / "steps").mkdir(parents=True, exist_ok=True)
    (out / "clouds").mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(0)
    for line in PROMPTS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        spec = sample_assembly(seed=item["seed"], difficulty=1)
        assembly = build_assembly(spec)

        step_path = out / "steps" / f"{item['id']}.step"
        assembly.export(str(step_path))

        stl_path = out / "steps" / f"{item['id']}.stl"
        shape = assembly.toCompound()
        cq.exporters.export(cq.Workplane(obj=shape), str(stl_path),
                            exportType="STL")

        points = _sample_surface(_read_binary_stl(stl_path), args.n_points, rng)
        if args.normalise == "unit_sphere":
            points = points - points.mean(axis=0)
            points = points / np.linalg.norm(points, axis=1).max()
        np.save(out / "clouds" / f"{item['id']}.npy", points.astype(np.float32))
        stl_path.unlink()
        print(f"{item['id']}: {step_path.name}, {args.n_points} points")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Check `sample_assembly`'s actual name and signature in `src/tolcad/gen/sampler.py` before running;
`export_assembly` in `src/tolcad/gen/export.py` is an alternative that writes both STEP and the
sidecar JSON in one call. Use whichever the module actually exposes — **do not add a wrapper to
`src/tolcad/`**, which is frozen for this plan.

Create `harness/prompts/smoke.jsonl`:

```jsonl
{"id": "smoke-001", "seed": 0, "prompt": "A rectangular steel plate 60 mm by 40 mm and 8 mm thick, with two 8.5 mm through holes on the long centreline, 30 mm apart.", "step": "steps/smoke-001.step", "pointcloud": "clouds/smoke-001.npy"}
{"id": "smoke-002", "seed": 1, "prompt": "A flat bracket 50 mm square and 6 mm thick with a single 10 mm central bore and a 4 mm chamfer on the top edge.", "step": "steps/smoke-002.step", "pointcloud": "clouds/smoke-002.npy"}
{"id": "smoke-003", "seed": 2, "prompt": "A 70 mm by 30 mm cover plate 5 mm thick with four 6.6 mm clearance holes, one 8 mm in from each corner.", "step": "steps/smoke-003.step", "pointcloud": "clouds/smoke-003.npy"}
```

- [ ] **Step 4: Run the entrypoint tests**

Run: `python -m pytest tests/harness/test_entrypoint.py -q`
Expected: PASS, all five.

Then: `python -m harness.make_inputs`
Expected: three lines, and `harness/prompts/steps/` plus `harness/prompts/clouds/` populated.
Confirm they are ignored: `git status --porcelain harness/prompts/` must be empty.

- [ ] **Step 5: Resolve cadrille's dependency set into a lock file**

This is the part no plan can write for you without network access, so here is the **procedure**,
which is complete, rather than a `pip install` line, which would be a guess.

```bash
mkdir -p /tmp/cadrille-spike && cd /tmp/cadrille-spike
git clone https://github.com/<upstream>/cadrille.git src   # URL from arXiv 2505.22914
cd src && git rev-parse HEAD                                # -> UPSTREAM_COMMIT
ls -1                                                       # inference entrypoint? requirements?
```

Then resolve inside the CPU base image, so the lock file is produced by the same interpreter the
Dockerfile will use:

```bash
docker run --rm -v "$PWD":/src -w /src python:3.11-slim-bookworm bash -lc '
  apt-get update -qq && apt-get install -y -qq git build-essential >/dev/null
  pip install --no-cache-dir pip-tools
  # Whichever the repo actually ships -- check with `ls`:
  #   requirements.txt  -> pip-compile requirements.txt -o /src/lock.txt
  #   pyproject.toml    -> pip-compile pyproject.toml   -o /src/lock.txt
  #   environment.yml   -> convert its pip: section by hand, then pip-compile
  pip-compile --index-url https://download.pytorch.org/whl/cpu \
              --extra-index-url https://pypi.org/simple \
              --output-file /src/lock.txt <INPUT>
'
cp lock.txt <repo>/harness/models/cadrille/requirements.lock.txt
```

**Remove any `torch`, `torchvision`, `torchaudio` and `nvidia-*` line from the lock file** and
record the torch version separately as the Dockerfile's `ARG TORCH_SPEC` default. Those are the
packages whose wheel index must stay a build arg; leaving them pinned in the lock file is exactly
the baking the Task 2 lint forbids, and the lint cannot see inside a lock file.

Record in `harness/models/cadrille/MODEL.md`: upstream URL, `UPSTREAM_COMMIT`, the entrypoint you
found, the input modality, the weight URLs and their `sha256sum`, the licence file's SPDX
identifier, and every surprise. Add the weight artifacts to `harness/weights/MANIFEST.toml` under
`[cadrille]`.

Time box: **4 hours.** If the resolve has not converged by then, stop, write what you learned into
`MODEL.md`, mark cadrille `FAIL` at Stage 1 with reason `dependency resolution did not converge`,
and go straight to Task 6 — because a pilot that cannot be piloted is itself the finding, and
DeepCAD is the more informative failure.

- [ ] **Step 6: Write the Dockerfile and the adapter**

Create `harness/models/cadrille/Dockerfile`:

```dockerfile
# cadrille (arXiv 2505.22914). Pilot model: this file is the template the
# other eight follow. See harness/build_matrix.toml for the variants and
# harness/matrix.py::lint_dockerfile for the rules this must satisfy.
#
# Build:
#   python -m harness.build --model cadrille --variant cpu     (Stage 1)
#   python -m harness.build --model cadrille --variant cu118   (Stage 2, Ada)
#
# NEVER bake BASE_IMAGE or TORCH_INDEX_URL. The default is the cu118
# deployment target, so a forgotten --build-arg lands on Ada (sm_89), not on
# the development laptop (sm_120).

ARG BASE_IMAGE=nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04
FROM ${BASE_IMAGE}

ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cu118
ARG TORCH_SPEC=<from Step 5's lock resolve, e.g. torch==2.4.1>
ARG UPSTREAM_REPO=<upstream git URL from Step 5>
ARG UPSTREAM_COMMIT=<40-char sha from Step 5>

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update -qq \
 && apt-get install -y -qq --no-install-recommends python3 python3-pip git ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && ln -sf /usr/bin/python3 /usr/local/bin/python

WORKDIR /opt/model
RUN git clone --filter=blob:none "${UPSTREAM_REPO}" . \
 && git checkout "${UPSTREAM_COMMIT}"

COPY harness/models/cadrille/requirements.lock.txt /tmp/lock.txt
RUN pip install --no-cache-dir "${TORCH_SPEC}" --index-url "${TORCH_INDEX_URL}" \
 && pip install --no-cache-dir -r /tmp/lock.txt

COPY harness/contract.py   /opt/tolcad/contract.py
COPY harness/entrypoint.py /opt/tolcad/entrypoint.py
COPY harness/models/cadrille/adapter.py /opt/tolcad/adapter.py

ENV PYTHONPATH=/opt/model:/opt/tolcad
ENTRYPOINT ["python", "/opt/tolcad/entrypoint.py"]
```

The three `<...>` placeholders are the **only** ones in this plan, and they are values Step 5
produces by execution. Fill them from `MODEL.md` before the first build; a `<` character surviving
into a committed Dockerfile fails the Task 11 completeness check.

Create `harness/models/cadrille/adapter.py`:

```python
"""cadrille adapter (arXiv 2505.22914).

Implements the three names harness/entrypoint.py requires. Nothing else in this
file is contractual: everything upstream-specific belongs here and nowhere else,
which is what keeps the other eight models comparable to this one.
"""

import pathlib

INPUT_MODALITY = "text"          # confirm against Step 5's findings
UPSTREAM_COMMIT = "<40-char sha>"


def load_model(weights_dir, device):
    """Load once per run. `weights_dir` is /weights, mounted read-only."""
    # Replace the body with the upstream loader found in Step 5. Keep the
    # signature. Keep the device argument honoured -- Stage 1 passes "cpu".
    raise NotImplementedError("fill in from the Step 5 spike")


def generate(model, item, out_dir):
    """Generate one item. Return the artifact filenames written in out_dir.

    Write at least one of:
        model.py    a CadQuery script defining a module-level `result`
        model.step  a STEP file
    Raising is allowed; the entrypoint records it as this item's error.
    """
    raise NotImplementedError("fill in from the Step 5 spike")
```

- [ ] **Step 7: Build and run Stage 1**

```bash
python - <<'PY'
from harness import contract, matrix, oci
caps = oci.probe_caps(oci.detect_runtime())
print(" ".join(oci.build_argv(caps, contract.image_name("cadrille", "cpu"),
                              "harness/models/cadrille", "cpu")))
PY
```

Run the printed command from the repo root — the build context must be the repo root, because the
Dockerfile `COPY`s `harness/contract.py`. Then:

```bash
python scripts/fetch_baseline_weights.py --model cadrille
python -m harness.runner --model cadrille --variant cpu --device cpu \
  --prompts harness/prompts/smoke.jsonl --limit 1
echo "exit=$?"
```

Expected: exit 0, and `harness/out/cadrille/run.json` with `n_ok: 1`. Also run the weight-free
import check, which is the cheapest Stage 1 signal and the one to reach for first:

```bash
docker run --rm tolcad-baseline/cadrille:cpu --self-check --model-slug cadrille
```

Expected: JSON with `contract_version`, `input_modality`, `upstream_commit`, `torch`, and
`cuda_available: false`. If `cuda_available` is `true` here, the `cpu` variant is not CPU-only and
the build args did not take — stop and fix that before continuing, because every subsequent Stage 1
result would be measuring the laptop's Blackwell GPU.

- [ ] **Step 8: Commit**

```bash
git add harness/entrypoint.py harness/make_inputs.py harness/prompts/smoke.jsonl \
        harness/models/cadrille/ harness/weights/MANIFEST.toml \
        tests/harness/test_entrypoint.py
git commit -m "feat: cadrille pilot container and the uniform entrypoint

Stage 1 only: built and run CPU-only on the laptop. This is NOT evidence the
image runs on sm_89; the laptop is sm_120 and the cu118 variant is unbuilt."
```

---

### Task 6: Pilot B — DeepCAD. SPIKE: find out on day one whether this is possible

**Verified in: Stage 1 (laptop, CPU).**

**SPIKE — *DeepCAD's 2021 dependency set under a modern base image*. Time box: one working day
(8 hours), hard.**

**Files:**
- Create: `harness/models/deepcad/{Dockerfile,adapter.py,requirements.lock.txt,MODEL.md}`
- Modify: `harness/weights/MANIFEST.toml`

**Interfaces:**
- Consumes: the adapter interface fixed in Task 5 (`INPUT_MODALITY`, `UPSTREAM_COMMIT`, `load_model`, `generate`)
- Produces: a `MODEL.md` containing either a working recipe or a root-caused `Stage 1 FAIL`

DeepCAD (2105.09492) is the second pilot rather than the eighth model because it is the one most
likely to be unsalvageable, and **if it cannot be containerised that must be discovered while the
model list can still change** — i.e. before the Phase 3.5 freeze. Learning it on day four costs the
same and teaches the same thing later. Its pinned PyTorch/CUDA predates both target GPUs: sm_89
(Ada) needs CUDA ≥ 11.8, and a 2021 build will not have been compiled for it.

The two failure modes to expect, and the order to try them in:

1. **The pinned torch has no wheel for CUDA 11.8.** Try the *oldest* torch that ships a `cu118`
   wheel and see whether DeepCAD's code still imports. Torch's Python API broke in specific,
   greppable places between 1.x and 2.x — `torch.solve`, `torch.symeig`, `torch.lstsq`,
   `torch.qr`, and `THCudaCheck`-era custom CUDA extensions. Grep the repo for those first; it is
   ten minutes and it predicts the outcome.
2. **A custom CUDA extension compiled with an old `nvcc`.** Then the base image must carry a
   `devel` (not `runtime`) CUDA image and the extension must be rebuilt with
   `TORCH_CUDA_ARCH_LIST="8.9"`. Add `ARG CUDA_ARCH_LIST=8.9` to this Dockerfile only, defaulting
   to the Ada value for the same reason `TORCH_INDEX_URL` does.

**Fallbacks, in the order to accept them, and each is a legitimate outcome:**

- **F1 — modernise the pin.** Newest torch that DeepCAD imports under. Record the delta from the
  paper's pin in `MODEL.md`; a reviewer will ask, and "we ran it on torch 2.x, here is the diff
  from the published environment" is a fine answer.
- **F2 — a `devel` base image and a rebuilt extension.** Slower and larger; still a pass.
- **F3 — use a maintained reimplementation** (several later CAD papers vendor DeepCAD's decoder).
  Then it is **not DeepCAD** and must be labelled `deepcad-reimpl` everywhere, with the divergence
  stated. This is a *different baseline*, and the paper must say so.
- **F4 — declare DeepCAD unrunnable.** Record `Stage 1 FAIL`, reason
  `2021 CUDA toolchain incompatible with sm_89; no maintained port`, and **immediately escalate to
  the human**: the Gate C spare is now zero, and the model list must change before
  pre-registration, not after.

Do not silently take F3. It changes what the paper claims to have measured.

- [ ] **Step 1: Predict the outcome before spending the day**

```bash
mkdir -p /tmp/deepcad-spike && cd /tmp/deepcad-spike
git clone --filter=blob:none https://github.com/<upstream>/DeepCAD.git src  # from arXiv 2105.09492
cd src && git rev-parse HEAD
grep -rn "torch.solve\|torch.symeig\|torch.lstsq\|torch\.qr(\|THCudaCheck\|AT_CHECK" . | head -40
find . -name "setup.py" -o -name "*.cu" -o -name "*.cpp" | head -20
cat requirements.txt environment.yml 2>/dev/null
```

Write the findings into `harness/models/deepcad/MODEL.md` **before** attempting a build. If the
grep is empty and there are no `.cu` files, expect F1 and budget two hours. If there are `.cu`
files, expect F2 and budget the full day.

- [ ] **Step 2: Resolve the lock file**

Follow Task 5 Step 5's procedure verbatim, with one change: resolve against
`nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04` rather than the slim Python image if Step 1 found
`.cu` files, because the extension needs `nvcc` at install time.

Strip `torch*` and `nvidia-*` from the lock file as before.

- [ ] **Step 3: Write the Dockerfile**

Copy `harness/models/cadrille/Dockerfile` to `harness/models/deepcad/Dockerfile` verbatim, then
change exactly four things: the header comment's model name and arXiv id, the three `ARG` defaults
(`TORCH_SPEC`, `UPSTREAM_REPO`, `UPSTREAM_COMMIT`), the three `COPY .../cadrille/...` paths to
`.../deepcad/...`, and — only if Step 1 found `.cu` files — add above the pip block:

```dockerfile
# DeepCAD ships a custom CUDA extension compiled for a pre-sm_89 toolchain.
# 8.9 is Ada, the deployment target; 12.0 is the laptop's Blackwell and is
# appended only for the cu128 variant. Never remove 8.9.
ARG CUDA_ARCH_LIST=8.9
ENV TORCH_CUDA_ARCH_LIST=${CUDA_ARCH_LIST}
```

Do **not** change `ARG BASE_IMAGE` or `ARG TORCH_INDEX_URL` away from their cu118 defaults. If a
`devel` image is needed, that is a *variant* concern — add `base_image_devel` to
`harness/build_matrix.toml` and pass it as `--build-arg BASE_IMAGE=...`. The lint checks the
default, not the override.

- [ ] **Step 4: Build, self-check, run**

```bash
python -m harness.runner --model deepcad --variant cpu --device cpu \
  --prompts harness/prompts/smoke.jsonl --limit 1 ; echo "exit=$?"
```

Expected: one of exit 0 (F1/F2 succeeded), exit 3 (`ENVIRONMENT` — weights or import), or exit 4
(`NO_OUTPUT`). **Any of the three is a valid spike result.** Record which, with the stderr tail, in
`MODEL.md`. DeepCAD is unconditional/latent-space rather than text-conditioned, so
`INPUT_MODALITY = "unconditional"` and `generate` keys off `item["seed"]` — the prompt string is
ignored, and `MODEL.md` must say so, because "the model ignored the prompt" would otherwise look
like a bug in the harness.

- [ ] **Step 5: Commit whatever happened**

```bash
git add harness/models/deepcad/ harness/weights/MANIFEST.toml
git commit -m "spike: DeepCAD containerisation, <F1|F2|F3|F4> — see MODEL.md"
```

A failed spike is committed with the same ceremony as a successful one. The `MODEL.md` from an F4
is the single most valuable file this plan can produce, because it is the one that changes a
decision while the decision is still open.

---

### Task 7: The results table, and the Gate C headroom number

**Verified in: Stage 1 for the mechanism; the Stage 2 column stays `NOT_ATTEMPTED` until Task 11.**

**Files:**
- Create: `harness/artifacts.py`
- Create: `harness/results.py`
- Create: `harness/results.json`
- Create: `harness/RESULTS.md`
- Test: `tests/harness/test_results.py`, `tests/harness/test_artifacts.py`

**Interfaces:**
- Consumes: `harness.contract.MODEL_SLUGS`, `harness.runner.RunOutcome`
- Produces:
  - `classify(item_dir) -> "crashed" | "unparseable" | "parsed"`
  - `class Outcome(str, Enum)`: `NOT_ATTEMPTED`, `PASS`, `FAIL`
  - `@dataclass ModelResult(slug, arxiv_id, stage1, stage1_reason, stage2, stage2_reason, n_crashed, n_unparseable, n_parsed, licence, redistributable, notes)`
  - `load_results(path=None) -> dict[str, ModelResult]`
  - `render_markdown(results) -> str`
  - `GATE_C_MIN_MODELS: int = 6`
  - `gate_c_headroom(results) -> tuple[int, int]` — `(stage-2 passes, spare above the floor)`

Two things this task exists to prevent. First, **an uncommitted result.** `results.json` is the
source of truth, `RESULTS.md` is rendered from it, and a test fails when the committed markdown
differs from the render — so a finding cannot live in a scrollback. Second, **the collapse of
`crashed` into `unparseable`.** A model that dies and a model that emits geometry the checker
cannot load are different findings, and only the second one is about CAD.

- [ ] **Step 1: Write the failing tests**

Create `tests/harness/test_artifacts.py`:

```python
import json
import pathlib

import pytest

from harness import artifacts, contract


def _item(tmp_path, status, files):
    d = tmp_path / "id"
    d.mkdir()
    (d / contract.ITEM_STATUS_FILENAME).write_text(json.dumps(
        {"id": "id", "status": status, "error": None,
         "artifacts": list(files), "wall_s": 0.1}), encoding="utf-8")
    return d


def test_an_errored_item_is_crashed(tmp_path):
    assert artifacts.classify(_item(tmp_path, "error", [])) == "crashed"


def test_a_missing_status_file_is_crashed(tmp_path):
    d = tmp_path / "id"
    d.mkdir()
    assert artifacts.classify(d) == "crashed"


def test_garbage_step_is_unparseable_not_crashed(tmp_path):
    """The distinction the paper rests on. A model that emits junk geometry has
    NOT crashed -- it produced a wrong answer, which is a different finding."""
    d = _item(tmp_path, "ok", [contract.STEP_ARTIFACT])
    (d / contract.STEP_ARTIFACT).write_text("not a step file", encoding="utf-8")
    assert artifacts.classify(d) == "unparseable"


@pytest.mark.parametrize("body", [
    "import cadquery as cq\nresult = cq.Workplane().box(1, 1, 1)\n",
])
def test_a_valid_cadquery_script_is_parsed(tmp_path, body):
    pytest.importorskip("cadquery")
    d = _item(tmp_path, "ok", [contract.CADQUERY_ARTIFACT])
    (d / contract.CADQUERY_ARTIFACT).write_text(body, encoding="utf-8")
    assert artifacts.classify(d) == "parsed"


def test_a_cadquery_script_without_result_is_unparseable(tmp_path):
    pytest.importorskip("cadquery")
    d = _item(tmp_path, "ok", [contract.CADQUERY_ARTIFACT])
    (d / contract.CADQUERY_ARTIFACT).write_text(
        "import cadquery as cq\nx = 1\n", encoding="utf-8")
    assert artifacts.classify(d) == "unparseable"
```

Create `tests/harness/test_results.py`:

```python
import pathlib
import re

from harness import contract, results

REPO = pathlib.Path(__file__).resolve().parents[2]
SPEC = REPO / "docs" / "superpowers" / "specs" / \
    "2026-07-31-tolerance-aware-cad-eval-design.md"


def test_gate_c_floor_matches_the_frozen_spec_text():
    """Two-sided pin against the frozen source, not a second copy of a threshold.

    Design spec section 7, Gate C: "Effect holds across >= 6 of the >= 8
    baseline models". Frozen. If this test fails, the SPEC changed, and that is
    a pre-registration violation -- do not edit the constant to match.
    """
    text = SPEC.read_text(encoding="utf-8")
    match = re.search(r"across\s*\u2265\s*(\d+)\s*of the\s*\u2265\s*(\d+)\s*baseline models",
                      text)
    assert match, "the Gate C criterion sentence is not where it was"
    assert int(match.group(1)) == results.GATE_C_MIN_MODELS
    assert int(match.group(2)) == 8


def test_every_slug_has_a_row():
    loaded = results.load_results()
    assert set(loaded) == set(contract.MODEL_SLUGS)


def test_the_committed_markdown_matches_the_render():
    """An uncommitted result is not a result. This is that rule, executable."""
    rendered = results.render_markdown(results.load_results())
    committed = (REPO / "harness" / "RESULTS.md").read_text(encoding="utf-8")
    assert committed == rendered, (
        "harness/RESULTS.md is stale. Regenerate with "
        "`python -m harness.results --render` and commit it.")


def test_headroom_counts_only_stage_2_passes():
    """A Stage 1 pass is a build receipt. Gate C is about models that RAN."""
    loaded = {
        "a": results.ModelResult(slug="a", arxiv_id="1", stage1=results.Outcome.PASS,
                                 stage1_reason="", stage2=results.Outcome.NOT_ATTEMPTED,
                                 stage2_reason="", n_crashed=0, n_unparseable=0,
                                 n_parsed=0, licence="MIT", redistributable=True,
                                 notes=""),
    }
    count, spare = results.gate_c_headroom(loaded)
    assert count == 0
    assert spare == -results.GATE_C_MIN_MODELS


def test_the_render_states_the_headroom_and_names_gate_c():
    rendered = results.render_markdown(results.load_results())
    assert "Gate C" in rendered
    assert "spare" in rendered.lower()
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/harness/test_results.py tests/harness/test_artifacts.py -q`
Expected: FAIL — `cannot import name 'artifacts'`.

- [ ] **Step 3: Implement**

Create `harness/artifacts.py`:

```python
"""Three-way classification of one item's output. Never collapse the three.

crashed      the model produced nothing -- died, errored, or wrote no artifact
unparseable  an artifact exists but no CAD kernel can load it
parsed       an artifact exists and loads

`crashed` and `unparseable` are different FINDINGS. The first says nothing about
CAD; the second says the model generated geometry and got it wrong. Reporting
them as one number would make a broken container look like a modelling result.
Per design spec section 8.4 neither is dropped -- both take worst-case metric
values downstream.
"""

from __future__ import annotations

import json
import pathlib

from harness import contract

Classification = str  # "crashed" | "unparseable" | "parsed"


def _loads_as_step(path: pathlib.Path) -> bool:
    try:
        import cadquery as cq
        shape = cq.importers.importStep(str(path))
        return bool(shape.val().isValid())
    except Exception:  # noqa: BLE001
        return False


def _loads_as_cadquery(path: pathlib.Path) -> bool:
    namespace: dict = {}
    try:
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"),  # noqa: S102
             namespace)
    except Exception:  # noqa: BLE001
        return False
    result = namespace.get("result")
    if result is None:
        return False
    try:
        return bool(result.val().isValid())
    except Exception:  # noqa: BLE001
        return False


def classify(item_dir) -> Classification:
    item_dir = pathlib.Path(item_dir)
    status_path = item_dir / contract.ITEM_STATUS_FILENAME
    if not status_path.is_file():
        return "crashed"
    payload = json.loads(status_path.read_text(encoding="utf-8"))
    if payload.get("status") != "ok" or not payload.get("artifacts"):
        return "crashed"

    step = item_dir / contract.STEP_ARTIFACT
    script = item_dir / contract.CADQUERY_ARTIFACT
    if step.is_file() and _loads_as_step(step):
        return "parsed"
    if script.is_file() and _loads_as_cadquery(script):
        return "parsed"
    return "unparseable"
```

`_loads_as_cadquery` executes untrusted model output. That is acceptable **only** because it runs
on artifacts this harness generated inside `--network=none` containers from pinned weights. Never
point it at a downloaded script. Say so in the review.

Create `harness/results.py`:

```python
"""The deliverable: harness/results.json (truth) -> harness/RESULTS.md (rendered).

`python -m harness.results --render` regenerates the markdown;
tests/harness/test_results.py fails when the committed file drifts from it.
That is the whole anti-scrollback mechanism.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
from enum import Enum

from harness import contract

HERE = pathlib.Path(__file__).resolve().parent
RESULTS_JSON = HERE / "results.json"
RESULTS_MD = HERE / "RESULTS.md"

# Design spec section 7, Gate C: "Effect holds across >= 6 of the >= 8 baseline
# models". FROZEN, pre-registered. Pinned two-sided against the spec text by
# tests/harness/test_results.py. Do not edit this to make a number work.
GATE_C_MIN_MODELS = 6

ARXIV_IDS = {
    "cadrille": "2505.22914",
    "deepcad": "2105.09492",
    "brepgen": "2401.15563",
    "text2cad": "2409.17106",
    "cad-recode": "2412.14042",
    "dtgbrepgen": "2503.13110",
    "hola": "2504.14257",
    "cad-coder-mit": "2505.14646",
    "text-to-cadquery": "2505.06507",
}


class Outcome(str, Enum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    PASS = "PASS"
    FAIL = "FAIL"


@dataclasses.dataclass
class ModelResult:
    slug: str
    arxiv_id: str
    stage1: Outcome
    stage1_reason: str
    stage2: Outcome
    stage2_reason: str
    n_crashed: int
    n_unparseable: int
    n_parsed: int
    licence: str
    redistributable: bool | None
    notes: str

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["stage1"] = self.stage1.value
        d["stage2"] = self.stage2.value
        return d

    @staticmethod
    def from_dict(d: dict) -> "ModelResult":
        d = dict(d)
        d["stage1"] = Outcome(d["stage1"])
        d["stage2"] = Outcome(d["stage2"])
        return ModelResult(**d)


def blank_results() -> dict[str, ModelResult]:
    return {
        slug: ModelResult(slug=slug, arxiv_id=ARXIV_IDS[slug],
                          stage1=Outcome.NOT_ATTEMPTED, stage1_reason="",
                          stage2=Outcome.NOT_ATTEMPTED, stage2_reason="",
                          n_crashed=0, n_unparseable=0, n_parsed=0,
                          licence="", redistributable=None, notes="")
        for slug in contract.MODEL_SLUGS
    }


def load_results(path: pathlib.Path | None = None) -> dict[str, ModelResult]:
    path = path or RESULTS_JSON
    if not path.is_file():
        return blank_results()
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {slug: ModelResult.from_dict(body) for slug, body in raw.items()}


def save_results(results: dict[str, ModelResult],
                 path: pathlib.Path | None = None) -> None:
    (path or RESULTS_JSON).write_text(
        json.dumps({s: r.to_dict() for s, r in results.items()},
                   indent=2, sort_keys=True) + "\n", encoding="utf-8")


def gate_c_headroom(results: dict[str, ModelResult]) -> tuple[int, int]:
    """(models passing STAGE 2, spare above the frozen Gate C floor).

    Stage 1 passes are deliberately not counted. Stage 1 proves an image builds
    and imports on a CPU; Gate C is about models that produced real inference on
    the deployment GPU.
    """
    count = sum(1 for r in results.values() if r.stage2 is Outcome.PASS)
    return count, count - GATE_C_MIN_MODELS


def render_markdown(results: dict[str, ModelResult]) -> str:
    count, spare = gate_c_headroom(results)
    lines = [
        "# Baseline containerisation results",
        "",
        "Generated by `python -m harness.results --render`. **Do not edit by hand** —",
        "`harness/results.json` is the source of truth and",
        "`tests/harness/test_results.py` fails when this file drifts from it.",
        "",
        "**Stage 1** — laptop, CPU-only: image builds, dependencies resolve, weights",
        "verify against pinned sha256, package imports, the CLI contract is honoured,",
        "and a CPU forward pass runs where the model permits one.",
        "",
        "**Stage 2** — workstation, RTX A6000 Ada (sm_89), GPU: real inference, real",
        "artifacts, one command. **Only Stage 2 counts toward Gate C.** A Stage 1 PASS",
        "on the development laptop (RTX 5060, sm_120) is not evidence about sm_89.",
        "",
        f"## Gate C headroom: {count} of {GATE_C_MIN_MODELS} required, "
        f"spare = {spare:+d}",
        "",
        "Design spec §7, Gate C (**frozen**): *effect holds across ≥ 6 of the ≥ 8",
        "baseline models*. Nine are named, so the design has one spare. A negative",
        "spare means the criterion is unmeetable and the model list must change",
        "**before** Phase 3.5 pre-registration.",
        "",
        "| Model | arXiv | Stage 1 | reason | Stage 2 | reason | crashed | unparseable | parsed | licence | redistributable |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for slug in contract.MODEL_SLUGS:
        r = results[slug]
        redis = {True: "yes", False: "no", None: "unknown"}[r.redistributable]
        lines.append(
            f"| `{slug}` | {r.arxiv_id} | {r.stage1.value} | {r.stage1_reason or '—'} "
            f"| {r.stage2.value} | {r.stage2_reason or '—'} | {r.n_crashed} "
            f"| {r.n_unparseable} | {r.n_parsed} | {r.licence or '—'} | {redis} |")
    lines += [
        "",
        "`crashed` / `unparseable` / `parsed` are three distinct outcomes and are",
        "never summed. A model that dies produced no CAD; a model whose artifact will",
        "not load produced wrong CAD. Only the second is a modelling finding. Per",
        "design spec §8.4 neither is dropped from the analysis.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--init", action="store_true")
    args = parser.parse_args(argv)
    if args.init and not RESULTS_JSON.is_file():
        save_results(blank_results())
    results = load_results()
    if args.render:
        RESULTS_MD.write_text(render_markdown(results), encoding="utf-8")
        print(f"wrote {RESULTS_MD}")
    count, spare = gate_c_headroom(results)
    print(f"gate_c_stage2_passes={count} required={GATE_C_MIN_MODELS} spare={spare:+d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Initialise, fill in the two pilots, render**

```bash
python -m harness.results --init
```

Edit `harness/results.json` for `cadrille` and `deepcad` from Tasks 5 and 6: set `stage1`,
`stage1_reason`, and the three counts (run `python - <<'PY' ... artifacts.classify ... PY` over
`harness/out/<slug>/*/`). Leave `stage2` at `NOT_ATTEMPTED` — Task 11 owns it. Then:

```bash
python -m harness.results --render
```

Expected: `gate_c_stage2_passes=0 required=6 spare=-6`. That is correct today and must stay
visible; a plan that hid it until Stage 2 would be hiding the only number that matters.

- [ ] **Step 5: Run the tests**

Run: `python -m pytest tests/harness/ -q`
Expected: PASS. Then `python -m pytest -q` to confirm the whole suite and a clean tree.

- [ ] **Step 6: Commit**

```bash
git add harness/artifacts.py harness/results.py harness/results.json harness/RESULTS.md \
        tests/harness/test_results.py tests/harness/test_artifacts.py
git commit -m "feat: committed results table with the Gate C headroom number"
```

---

### Task 8: Licence and redistribution register

**Verified in: Stage 1 (laptop). Reading licence files, no container needed.**

**Files:**
- Create: `harness/LICENCES.md`
- Modify: `harness/results.json`, `harness/RESULTS.md`
- Modify: `harness/models/<slug>/MODEL.md` (the two that exist)
- Test: `tests/harness/test_licences.py`

**Interfaces:**
- Consumes: `harness.results.load_results`
- Produces: `licence` (SPDX id or `"custom: <summary>"`) and `redistributable` (bool) populated for every attempted model

Licences differ per model and some research releases forbid redistribution — non-commercial
clauses, "research use only", weights under a separate licence from the code, or no licence file at
all, which means **no permission**, not permissive. This decides whether the artifact release can
publish the images, and it is much cheaper to answer now than during a camera-ready.

- [ ] **Step 1: Write the failing test**

Create `tests/harness/test_licences.py`:

```python
import pathlib
import re

from harness import contract, results

REPO = pathlib.Path(__file__).resolve().parents[2]
REGISTER = REPO / "harness" / "LICENCES.md"


def test_every_model_that_was_attempted_has_a_licence_recorded():
    """No licence recorded == no permission established. Absence is not MIT."""
    missing = [
        slug for slug, r in results.load_results().items()
        if r.stage1 is not results.Outcome.NOT_ATTEMPTED
        and (not r.licence or r.redistributable is None)
    ]
    assert not missing, (
        "attempted with no licence verdict: " + ", ".join(missing))


def test_the_register_has_a_section_per_slug():
    text = REGISTER.read_text(encoding="utf-8")
    missing = [s for s in contract.MODEL_SLUGS if f"## `{s}`" not in text]
    assert not missing, "no section in LICENCES.md for: " + ", ".join(missing)


def test_the_register_records_a_weights_licence_separately_from_code():
    """Weights are frequently licensed differently from the repo. Ask twice."""
    text = REGISTER.read_text(encoding="utf-8")
    for slug in contract.MODEL_SLUGS:
        section = re.split(r"^## ", text, flags=re.MULTILINE)
        body = next((s for s in section if s.startswith(f"`{slug}`")), "")
        assert "Code licence:" in body, slug
        assert "Weights licence:" in body, slug
        assert "May we publish the image:" in body, slug
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/harness/test_licences.py -q`
Expected: FAIL — `harness/LICENCES.md` does not exist.

- [ ] **Step 3: Create the register**

Create `harness/LICENCES.md` with this exact section shape, one per slug, in
`contract.MODEL_SLUGS` order:

```markdown
# Baseline licence and redistribution register

Filled in as each model is containerised. **An empty licence field means no
permission has been established, not that the work is permissive.** A research
release with no LICENSE file grants nothing.

Three questions per model, because they have three different answers:
the code licence, the weights licence, and whether we may publish a *derived
container image* containing either.

## `cadrille`

- arXiv: 2505.22914
- Upstream: <url> @ <commit>
- Code licence: <SPDX id, or "none found">
- Weights licence: <SPDX id, or "none found", or "same as code — quote the sentence">
- Redistribution of weights permitted: <yes|no|unclear>
- May we publish the image: <yes|no|code-only>
- Evidence: <path of the licence file at that commit, plus the deciding sentence>

## `deepcad`

...
```

Repeat for all nine. For any model where the answer is `no` or `unclear`, the artifact release
publishes the **Dockerfile and lock file only** — which is fully reproducible, since
`scripts/fetch_baseline_weights.py` fetches from upstream — and `RESULTS.md` records
`redistributable = false`. Note that as the default plan; it is almost certainly where several of
the nine land, and it costs nothing.

- [ ] **Step 4: Populate `results.json` and re-render**

Set `licence` and `redistributable` for cadrille and deepcad, then:

```bash
python -m harness.results --render
python -m pytest tests/harness/test_licences.py tests/harness/test_results.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add harness/LICENCES.md harness/results.json harness/RESULTS.md tests/harness/test_licences.py
git commit -m "feat: per-model licence and redistribution register"
```

---

### Task 9: Fan out to the remaining six models

**Verified in: Stage 1 (laptop, CPU) for all six.**

**SPIKE ×6 — *Per-baseline upstream inference entrypoint discovery*. Time box: 4 hours per model,
hard, running in parallel via `superpowers:dispatching-parallel-agents`. Fallback per model:
record `Stage 1 FAIL` with a root cause and move on — a time-boxed failure is a result.**

**Files (×6, for `brepgen`, `text2cad`, `cad-recode`, `dtgbrepgen`, `cad-coder-mit`, `text-to-cadquery`):**
- Create: `harness/models/<slug>/{Dockerfile,adapter.py,requirements.lock.txt,MODEL.md}`
- Modify: `harness/weights/MANIFEST.toml`, `harness/LICENCES.md`, `harness/results.json`, `harness/RESULTS.md`

**Interfaces:**
- Consumes: the adapter interface from Task 5 (`INPUT_MODALITY`, `UPSTREAM_COMMIT`, `load_model`, `generate`), the Dockerfile template from Task 5 Step 6, the lock procedure from Task 5 Step 5
- Produces: six more `harness/models/<slug>/` directories and six more filled rows

`hola` is deliberately not in this list — Task 10 owns it, because its unknown is *availability*,
not *packaging*, and it has a different decision attached.

Each of the six is the **same five steps**, and they are independent, so dispatch them in parallel.
Give each agent this and nothing else: the slug, the arXiv id, Task 5 Steps 5–7 verbatim, and the
per-model note below.

Per-model notes, which are the only things that differ:

| Slug | arXiv | Expected `INPUT_MODALITY` | The specific thing to watch |
|---|---|---|---|
| `brepgen` | 2401.15563 | `unconditional` | **OCCT/pythonocc bindings.** `pythonocc-core` is conda-first; the pip route is `cadquery-ocp`, which this repo already installs for `tolcad[gen]`. If upstream imports `OCC.Core.*`, try `cadquery-ocp` and add a `sys.modules` shim in `adapter.py` **only if the API matches** — check `BRepBuilderAPI`, `TopoDS`, `STEPControl_Writer`. If it does not, use a conda-forge base image and say so in `MODEL.md`. |
| `dtgbrepgen` | 2503.13110 | `unconditional` or `brep` | Same OCCT question as BrepGen. Solve it once, reuse the answer, and cross-reference the other `MODEL.md`. |
| `text2cad` | 2409.17106 | `text` | Prompts are in the smoke set. Check whether it expects the DeepCAD command-sequence vocabulary — if so, its artifact is a command sequence, not CadQuery or STEP, and `generate` must convert it. If conversion is not straightforward, that is a `Stage 1 FAIL` with reason `output format not convertible to STEP or CadQuery`, and it is a real finding. |
| `cad-recode` | 2412.14042 | `pointcloud` | Consumes `item["pointcloud"]`, produced by `harness/make_inputs.py`. Check the expected point count and normalisation; `make_inputs.py` takes `--n-points` and `--normalise`. Record what it wanted. |
| `cad-coder-mit` | 2505.14646 | `text` | **Doris et al. (MIT).** Not 2505.19713 (Guan et al., Beihang). Verify the repo you cloned matches 2505.14646 before spending an hour on it — `papers/literature/2505.14646_cad-coder-mit.pdf` is already fetched; read its GitHub URL from the paper. |
| `text-to-cadquery` | 2505.06507 | `text` | Emits CadQuery directly, so `generate` writes `model.py` and the harness needs no conversion. The easiest of the six; do it first to calibrate the others. |

- [ ] **Step 1: Dispatch the six in parallel**

Use `superpowers:dispatching-parallel-agents`. Each agent's brief:

> Containerise `<slug>` (arXiv `<id>`) following `harness/models/cadrille/` exactly. Execute Task 5
> Steps 5, 6 and 7 of `docs/superpowers/plans/2026-08-02-baseline-containerization.md`, substituting
> the slug. Watch for: `<the per-model note>`. Time box 4 hours; on expiry write `MODEL.md` with the
> root cause and stop. **Touch only `harness/models/<slug>/`, `harness/weights/MANIFEST.toml` and
> `harness/LICENCES.md`.** Do not touch `src/`, `scripts/`, `tests/`, `harness/contract.py`,
> `harness/entrypoint.py`, `harness/results.py` or any other model's directory. If the contract
> does not fit your model, **do not change the contract** — report the mismatch and stop, because
> the contract is what makes the nine comparable and a per-model exception destroys that.

`harness/weights/MANIFEST.toml` and `harness/LICENCES.md` are shared, so six parallel agents will
conflict on them. Have each agent write `harness/models/<slug>/weights.toml` and a
`## \`<slug>\`` block in `harness/models/<slug>/MODEL.md` instead, and merge them yourself in
Step 3. That is cheaper than serialising six four-hour spikes.

- [ ] **Step 2: Verify each result yourself before believing it**

For each returned slug, on your own machine:

```bash
docker run --rm tolcad-baseline/<slug>:cpu --self-check --model-slug <slug>
python -m harness.runner --model <slug> --variant cpu --device cpu \
  --prompts harness/prompts/smoke.jsonl --limit 1 ; echo "exit=$?"
python -m pytest tests/harness/test_build_matrix.py -q   # the Dockerfile lint now applies
```

Expected: `--self-check` prints `cuda_available: false`; the runner exits 0, 3 or 4; the lint
passes. An agent reporting success whose `--self-check` you have not run is not a verified result.
This project's own history is that reported greens and measured greens diverge.

- [ ] **Step 3: Merge the manifests and record the rows**

Fold each `harness/models/<slug>/weights.toml` into `harness/weights/MANIFEST.toml`, each licence
block into `harness/LICENCES.md`, then:

```bash
python scripts/fetch_baseline_weights.py --verify-only
```

Expected: exit 0 if every attempted model's weights are present and hash-correct; otherwise a
`FAIL:` line per problem. Do not proceed past a checksum mismatch.

Update `harness/results.json` from your Step 2 observations, not from the agents' reports, then
`python -m harness.results --render`.

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest -q`
Expected: PASS, tree clean. The nine-way parametrised Dockerfile lint should now report eight
passes and one skip (`hola`).

- [ ] **Step 5: Commit**

```bash
git add harness/models/ harness/weights/MANIFEST.toml harness/LICENCES.md \
        harness/results.json harness/RESULTS.md
git commit -m "feat: containerise six more baselines; Stage 1 results recorded"
```

---

### Task 10: HoLa — SPIKE on availability, and the Gate C decision point

**Verified in: Stage 1 (laptop, CPU), if it is verifiable at all.**

**SPIKE — *HoLa weight availability outside the HuggingFace Space*. Time box: 3 hours, hard.**

**Files:**
- Create: `harness/models/hola/MODEL.md` (always), and `{Dockerfile,adapter.py,requirements.lock.txt}` only if weights exist
- Modify: `harness/results.json`, `harness/RESULTS.md`, `harness/LICENCES.md`

**Interfaces:**
- Consumes: the Task 5 adapter interface
- Produces: a decision, recorded in `MODEL.md` and reflected in the headroom number

HoLa (2504.14257) is listed in the design spec as *"HF Space"* rather than "code+weights", which is
the spec quietly recording that it may not be independently runnable. This task settles it.

- [ ] **Step 1: Establish whether weights exist outside the Space**

In order, stopping at the first that succeeds:

1. The arXiv page and the paper's own links — `papers/literature/2504.14257_hola-brep.pdf` is
   already fetched. Read its abstract page and any code/data availability statement.
2. The HF Space's **Files** tab. A Space that runs inference must load weights from somewhere:
   either files in the Space repo, or a `from_pretrained("<org>/<model>")` call in `app.py`
   pointing at a separate model repo — which *is* a downloadable release.
3. A GitHub repo linked from the paper or the Space README.
4. `huggingface_hub.list_models(author=...)` / `search="hola"`.

If any of 1–4 yields a downloadable checkpoint with a `sha256`, HoLa is a normal model: follow
Task 5 Steps 5–7 and stop reading here.

- [ ] **Step 2: If there are no weights, do NOT fall back to the Space API**

Record `Stage 1 FAIL`, reason `weights not released; HF Space only`. Calling a hosted Space from
the harness would be worse than dropping it, for three reasons worth writing down in `MODEL.md`:

- It is **not reproducible.** The Space can change, rate-limit, or vanish, and a paper's headline
  cannot depend on someone else's uptime.
- It **cannot run under `--network=none`,** so it breaks the isolation every other baseline honours.
- It runs on **unknown hardware with unknown precision**, so its numbers are not comparable to
  eight models measured on the same A6000 Ada. Comparability is the whole reason for eight
  baselines.

- [ ] **Step 3: Compute the headroom and escalate if it is negative**

```bash
python -m harness.results --render
```

Read the printed `spare=`. Then apply this rule, which exists so the decision is made by
arithmetic and not by mood:

| Stage 1 passes out of nine | Meaning | Action |
|---|---|---|
| ≥ 8 | Comfortable | Proceed to Stage 2 |
| 7 | Exactly one spare, and Stage 2 has not run yet | Proceed, but flag to the human that **any** Stage 2 loss is fatal |
| ≤ 6 | Gate C is at or below its floor **before GPU verification has even started** | **STOP. Escalate to the human before Task 11.** |

At `≤ 6`, the honest options are: add baselines to the list *before* Phase 3.5 pre-registration
(the spec's own §6 says "Plus prompted frontier VLMs emitting CadQuery" — those are additional
baselines and they are cheap); or pre-register a Gate C criterion phrased over the models that
actually run. **Both must happen before the freeze.** After the freeze, neither is available, and
the criterion is simply unmeetable — which is precisely why this plan runs first.

Write the recommendation into `harness/RESULTS.md` via a `notes` entry, not into a chat message.

- [ ] **Step 4: Commit**

```bash
git add harness/models/hola/ harness/results.json harness/RESULTS.md harness/LICENCES.md
git commit -m "spike: HoLa weight availability; Gate C headroom recomputed"
```

---

### Task 11: Stage 2 on the workstation, and the pre-registration memo

**Verified in: Stage 2 (RHEL and WSL2 workstations, RTX A6000 Ada, sm_89, GPU). This is the only
task that produces Stage 2 evidence.**

**Files:**
- Modify: `harness/results.json`, `harness/RESULTS.md`
- Modify: `harness/oci.py` (remove or update the unverified-podman notice)
- Modify: `harness/build_matrix.toml` (record verified base-image tags)
- Test: `tests/harness/test_stage2_completeness.py`

**Interfaces:**
- Consumes: every model directory from Tasks 5, 6, 9, 10
- Produces: the `stage2` column of `harness/results.json`, and the go/no-go paragraph for Phase 3.5

Everything before this was a build receipt. Nothing before this is evidence that any model runs on
sm_89, and the laptop cannot supply that evidence at any price: it is sm_120 on a CUDA 12.8+
toolchain, a *different* architecture on a *newer* stack than the deployment target. A `cu128`
image that ran green on the laptop tells you nothing about the `cu118` image on Ada.

- [ ] **Step 1: Write the completeness test**

Create `tests/harness/test_stage2_completeness.py`:

```python
import pathlib

import pytest

from harness import contract, matrix, results

REPO = pathlib.Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("slug", contract.MODEL_SLUGS)
def test_an_attempted_model_has_a_complete_dockerfile(slug):
    """No unfilled template markers may reach a committed Dockerfile."""
    path = REPO / "harness" / "models" / slug / "Dockerfile"
    if not path.is_file():
        pytest.skip(f"{slug} has no Dockerfile (see harness/RESULTS.md)")
    text = path.read_text(encoding="utf-8")
    assert "<" not in text.replace("<<", ""), (
        f"{slug}/Dockerfile still contains an unfilled placeholder")
    assert matrix.lint_dockerfile(text) == []


def test_stage2_passes_are_never_recorded_without_a_stage1_pass():
    """Stage 2 without Stage 1 means the evidence chain skipped a link."""
    bad = [s for s, r in results.load_results().items()
           if r.stage2 is results.Outcome.PASS
           and r.stage1 is not results.Outcome.PASS]
    assert not bad, "stage2 PASS with no stage1 PASS: " + ", ".join(bad)


def test_every_model_has_a_reason_when_it_failed():
    bad = [s for s, r in results.load_results().items()
           if (r.stage1 is results.Outcome.FAIL and not r.stage1_reason)
           or (r.stage2 is results.Outcome.FAIL and not r.stage2_reason)]
    assert not bad, "FAIL with no recorded reason: " + ", ".join(bad)
```

- [ ] **Step 2: Build the `cu118` images on the RHEL workstation**

```bash
git clone <repo> tolcad && cd tolcad
pip install -e ".[dev,gen]"
python -m pytest -q                      # the tree must be green here first
python -c "from harness import oci; print(oci.probe_caps(oci.detect_runtime()))"
```

Expected: `RuntimeCaps(name='podman', rootless=..., selinux=..., gpu_flag=('--device', 'nvidia.com/gpu=all'))`.
This is the moment the Task 3 spike resolves. If `rootless` or `selinux` came back wrong, fix
`probe_caps` — its parsing is deliberately crude and this is the first machine that can correct it.

Then, per model that passed Stage 1:

```bash
python - <<'PY'
from harness import contract, oci
caps = oci.probe_caps(oci.detect_runtime())
for slug in ("cadrille",):  # extend to every Stage 1 PASS
    print(" ".join(oci.build_argv(caps, contract.image_name(slug, "cu118"),
                                  f"harness/models/{slug}", "cu118")))
PY
```

- [ ] **Step 3: Verify the GPU is actually being used**

```bash
podman run --rm --device nvidia.com/gpu=all tolcad-baseline/<slug>:cu118 \
  --self-check --model-slug <slug>
```

Expected: `"cuda_available": true`. **If this prints `false`, every subsequent "Stage 2 PASS" is a
CPU run wearing a GPU label** — the exact defect this plan warns about, arriving from the other
direction. Do not record any Stage 2 result until it prints `true`.

Then confirm the arch is right, which `cuda_available` does not tell you:

```bash
podman run --rm --device nvidia.com/gpu=all tolcad-baseline/<slug>:cu118 \
  python -c "import torch; print(torch.cuda.get_device_capability(0), torch.version.cuda)"
```

Expected: `(8, 9)` and a CUDA 11.8-series version. `(8, 9)` is Ada. If you see `(12, 0)` you are
on the laptop and this is not Stage 2.

- [ ] **Step 4: Run the real thing, one command per model**

```bash
for slug in <every Stage 1 PASS> ; do
  python -m harness.runner --model "$slug" --variant cu118 --device cuda:0 \
    --prompts harness/prompts/smoke.jsonl
  echo "$slug exit=$?"
done
```

Record per model: the exit code, and the `crashed` / `unparseable` / `parsed` counts from
`harness.artifacts.classify` over `harness/out/<slug>/*/`. A model is `stage2 = PASS` **iff** the
runner exited 0 **and** at least one item classified `parsed`. Exit 0 with three `unparseable`
items is `stage2 = PASS` too — the model ran and produced wrong geometry, which is a finding, not a
harness failure. Put the distinction in `stage2_reason`.

- [ ] **Step 5: Repeat on the WSL2 workstation**

Same commands with `--runtime docker`. Both boxes are Ada, so a divergence between them is a
runtime or driver issue, not a model issue — record it in `notes` and do not average over it.

- [ ] **Step 6: Update the register and close the podman notice**

Update `harness/results.json`, then:

```bash
python -m harness.results --render
python -m pytest tests/harness/ -q
```

Replace the `STAGE STATUS` comment in `harness/oci.py` with what you measured — the runtime name,
whether it was rootless, whether SELinux relabelling was needed, and any fallback taken. Record the
verified base-image tags in `harness/build_matrix.toml`'s header comment.

- [ ] **Step 7: Write the pre-registration go/no-go paragraph**

Append to `harness/RESULTS.md` — via a `notes` entry on the relevant models plus a hand-written
section that `render_markdown` preserves, or by extending `render_markdown` to emit it from a new
`verdict` key in `results.json`. **Prefer the second**; a hand-written tail would break the
render-equality test, which is the one control keeping this file honest.

The paragraph states, in this order: how many models reached Stage 2 PASS; the Gate C spare; and
one of —

- **spare ≥ +1:** Gate C is measurable with margin. Proceed to Phase 3.5.
- **spare == 0:** Gate C is measurable with **no** margin. Any model lost during Phase 4 makes a
  frozen criterion unmeetable. Recommend adding baselines before the freeze; the spec's own §6
  already contemplates "prompted frontier VLMs emitting CadQuery" and they are cheap.
- **spare < 0:** Gate C is **not** measurable as written. Do not pre-register it in this form. The
  list must change, or the criterion must be phrased over the models that run, and either way it
  happens **before** the timestamp.

- [ ] **Step 8: Commit**

```bash
git add harness/results.json harness/RESULTS.md harness/oci.py harness/build_matrix.toml \
        tests/harness/test_stage2_completeness.py
git commit -m "feat: Stage 2 GPU verification on sm_89 and the Gate C go/no-go"
```

---

## Plan completion state

At the end of Task 11:

- Nine models have a recorded, committed Stage 1 verdict, each with a root cause where it failed
- Every model that passed Stage 1 has a Stage 2 verdict measured on **sm_89**, not on the laptop
- `harness/RESULTS.md` states the Gate C headroom as a number, rendered from `results.json` by a
  test that fails if the committed file drifts — the finding cannot live in a scrollback
- No Dockerfile bakes a CUDA or torch version; the lint has a negative fixture proving it bites
- Weights are fetchable from a tracked manifest with pinned sha256 and a count-mismatch guard, and
  none of them are committed
- Every model's licence and redistribution status is recorded, code and weights asked separately
- `crashed`, `unparseable` and `parsed` are separate columns everywhere and are never summed
- The podman/rootless/SELinux path is either verified on the RHEL box or explicitly labelled
  unverified — never quietly assumed
- The human has a go/no-go paragraph for Phase 3.5, produced by arithmetic

## Deliberately NOT done here

- **Running the research corpus through any baseline.** Spec §12 puts pre-registration before data
  generation. The smoke set is three items and exists to prove plumbing.
- **`metrics/` and `analysis/`.** Chamfer, IoU, AUC and the cluster bootstrap are Phase 4.
- **Prompted frontier VLMs emitting CadQuery** (spec §6). They need no container and are a
  different kind of baseline; if Task 10 forces the model list open, they are the cheapest addition.
- **Multi-GPU or batched inference.** One GPU, one item at a time. Throughput is a Phase 5 problem.
- **Publishing the images.** Task 8 establishes whether we *may*; actually pushing them is part of
  the Gate D artifact release.

## Self-review

**1. Spec coverage.** Nine models named at design spec:178 → all nine have a task (5, 6, 9, 10).
`harness/` from spec §5 → Tasks 1, 3. Gate C's frozen `≥6 of ≥8` → Task 7 pins it two-sided against
the spec text, Task 10 gates on it, Task 11 reports it. Spec §8.4's "no dropping failed generations"
→ Task 7's three-way classification, which keeps failures in the denominator. The CAD-Coder
disambiguation note at spec:184 → encoded in the slug `cad-coder-mit` and asserted in
`test_there_are_exactly_nine_slugs_and_they_are_unique`. Compute (spec §6, "RHEL box 4× A6000 Ada;
Windows/WSL box") → Task 11 Steps 2 and 5. **Gap found and left open deliberately:** the spec's
"Plus prompted frontier VLMs emitting CadQuery" has no task, because they need no container; it is
named under *Deliberately NOT done* and surfaced as the remedy in Task 10 Step 3.

**2. Placeholder scan.** Three `<...>` markers survive, all in Task 5 Step 6 and Task 6 Step 3
(`TORCH_SPEC`, `UPSTREAM_REPO`, `UPSTREAM_COMMIT`), plus the `<url>`/`<SPDX id>` fields in the
`LICENCES.md` template. Every one is a value a named, executable procedure produces, and
`test_an_attempted_model_has_a_complete_dockerfile` fails the suite if a `<` survives into a
committed Dockerfile. No task says "TBD", "handle errors appropriately", or "similar to Task N" —
Task 6 Step 3 and Task 9 Step 1 both name the exact four things that differ rather than saying
"like cadrille". No `pip install` line for any baseline is asserted anywhere, because none could be
verified without network access.

**3. Type consistency.** `contract.ExitCode` values (0/2/3/4) are used identically in
`entrypoint.py`, `runner.py` and both test files. `RunOutcome` fields match between `runner.py` and
`test_runner.py`. `ModelResult`'s twelve fields match between `results.py`, `test_results.py`
(`test_headroom_counts_only_stage_2_passes` constructs one by keyword) and `test_licences.py`. The
adapter triple `INPUT_MODALITY` / `load_model` / `generate` is spelled the same in `entrypoint.py`,
`test_entrypoint.py`'s three fixture adapters, `cadrille/adapter.py`, Task 6 and Task 9's table.
`classify` returns exactly the three strings `test_artifacts.py` asserts. `gate_c_headroom` returns
`(count, spare)` in both `render_markdown` and `test_results.py`. One fixed after review:
`build_args` returns `{"BASE_IMAGE", "TORCH_INDEX_URL"}` and `lint_dockerfile`'s `REQUIRED_ARGS` is
the same pair — an earlier draft had the lint also require `TORCH_SPEC`, which would have failed
`Dockerfile.good`.
