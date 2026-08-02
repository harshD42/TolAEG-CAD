### Task 4: The mutation-score layer

**Files:**
- Create: `cosmic-ray.toml`
- Modify: `scripts/check_suite_integrity.py`
- Modify: `pyproject.toml`
- Test: `tests/test_suite_integrity_script.py`

**Interfaces:**
- Consumes: `scripts/check_suite_integrity.py` from Task 3
- Produces: `MUTATION_FLOOR` module constant; `run_mutation_score() -> tuple[float, bool]`

Layer 2 catches the *tautological* and *insensitive* classes in production code. A surviving mutant is the question "could this fail?" asked mechanically, once per mutable expression.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_suite_integrity_script.py`:

```python
def test_the_cosmic_ray_config_runs_the_whole_core_subset():
    """A per-file test command inflates survivors and makes the score meaningless.

    Spiked 2026-08-01 on types.py: scoping the command to tests/test_types.py
    alone gave 12 survivors of 66 (18.2%); the full core subset gave 5 of 66
    (7.58%). checker.py and y14_5.py tests exercise types.py heavily.
    """
    import tomllib

    cfg = tomllib.loads((REPO / "cosmic-ray.toml").read_text(encoding="utf-8"))
    command = cfg["cosmic-ray"]["test-command"]
    for module in ("types", "y14_5", "iso286", "montecarlo", "checker", "reliability"):
        assert f"tests/test_{module}.py" in command, (
            f"cosmic-ray's test-command omits tests/test_{module}.py; the "
            f"resulting mutation score would be inflated and meaningless"
        )


def test_the_mutation_floor_is_measured_not_aspirational():
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    assert mod.MUTATION_FLOOR not in (0, 50, 60, 70, 75, 80, 85, 90, 95, 100), (
        f"MUTATION_FLOOR {mod.MUTATION_FLOOR} looks aspirational rather than "
        f"measured. Run the layer, read the number, pin that."
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_suite_integrity_script.py -v -k "cosmic_ray or mutation_floor"`
Expected: FAIL — `cosmic-ray.toml` does not exist and `MUTATION_FLOOR` is undefined.

- [ ] **Step 3: Add the config and the layer**

Create `cosmic-ray.toml`:

```toml
# Layer 2 of the suite-integrity gate. See
# docs/superpowers/specs/2026-08-01-suite-integrity-design.md
#
# module-path is set per-run by scripts/check_suite_integrity.py, which iterates
# the six core modules -- cosmic-ray takes one module path per session.
#
# THE TEST COMMAND MUST BE THE WHOLE CORE SUBSET. Spiked 2026-08-01: scoping it
# to the single matching test file gave 12 survivors of 66 on types.py (18.2%),
# against 5 of 66 (7.58%) for the full subset, because checker.py and y14_5.py
# tests exercise types.py heavily. A per-file command measures nothing useful.
[cosmic-ray]
module-path = "src/tolcad/types.py"
timeout = 30.0
excluded-modules = []
test-command = "python -m pytest tests/test_types.py tests/test_y14_5.py tests/test_iso286.py tests/test_montecarlo.py tests/test_checker.py tests/test_reliability.py -x -q --no-header -p no:cacheprovider -m 'not slow'"

[cosmic-ray.distributor]
name = "local"
```

Add `"cosmic-ray>=8.3"` to the `dev` extra in `pyproject.toml`.

Add to `scripts/check_suite_integrity.py`:

```python
import shutil
import tempfile
import tomllib

# MEASURED, not chosen. Set from an actual run -- see Step 4.
MUTATION_FLOOR = 0.0  # replaced in Step 4 with the measured value

_CONFIG = REPO_ROOT / "cosmic-ray.toml"


def _mutate_one_module(module: str, workdir: Path) -> tuple[int, int, int]:
    """Run cosmic-ray over one core module. Returns (total, survived, incompetent)."""
    config = tomllib.loads(_CONFIG.read_text(encoding="utf-8"))
    config["cosmic-ray"]["module-path"] = f"src/tolcad/{module}.py"

    cfg_path = workdir / f"cr-{module}.toml"
    # Re-emit the config with only the field we changed; cosmic-ray reads TOML.
    cfg_path.write_text(
        "[cosmic-ray]\n"
        f'module-path = "src/tolcad/{module}.py"\n'
        f"timeout = {config['cosmic-ray']['timeout']}\n"
        "excluded-modules = []\n"
        f"test-command = \"{config['cosmic-ray']['test-command']}\"\n"
        "\n[cosmic-ray.distributor]\n"
        'name = "local"\n',
        encoding="utf-8",
    )
    session = workdir / f"{module}.sqlite"

    subprocess.run(["cosmic-ray", "init", str(cfg_path), str(session)],
                   cwd=REPO_ROOT, check=True, capture_output=True, text=True)
    subprocess.run(["cosmic-ray", "exec", str(cfg_path), str(session)],
                   cwd=REPO_ROOT, check=True, capture_output=True, text=True)
    report = subprocess.run(["cr-report", str(session)],
                            cwd=REPO_ROOT, capture_output=True, text=True).stdout

    total = int(re.search(r"total jobs:\s*(\d+)", report).group(1))
    survived = int(re.search(r"surviving mutants:\s*(\d+)", report).group(1))
    # INCOMPETENT mutants fail to execute at all (RemoveDecorator on a
    # dataclass, for instance). They are neither killed nor surviving, so
    # counting them either way distorts the score.
    incompetent = report.count("TestOutcome.INCOMPETENT")
    return total, survived, incompetent


def run_mutation_score() -> tuple[float, bool]:
    """Aggregate killed / (total - incompetent) across the six core modules."""
    if shutil.which("cosmic-ray") is None:
        # Unavailable is a FAILURE, never a skip. A silently skipped integrity
        # layer is the exact failure mode this whole exercise exists to remove.
        raise RuntimeError(
            "cosmic-ray is not installed; install the [dev] extra. This layer "
            "does not skip."
        )

    totals = survived_all = incompetent_all = 0
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        for module in CORE_MODULES:
            total, survived, incompetent = _mutate_one_module(module, workdir)
            totals += total
            survived_all += survived
            incompetent_all += incompetent

    denominator = totals - incompetent_all
    if denominator <= 0:
        raise RuntimeError("no viable mutants were generated; the config is wrong")
    killed = denominator - survived_all
    score = 100.0 * killed / denominator
    return score, score >= MUTATION_FLOOR
```

Wire it into `main()` as a second row, guarded so `--self-test-failure` skips the slow path. Session databases live in a `TemporaryDirectory`, never in the repo.

Add `"cosmic-ray>=8.3"` to the `dev` extra in `pyproject.toml`.

- [ ] **Step 4: Measure the baseline and pin it**

Run: `python scripts/check_suite_integrity.py`

This takes roughly **5 minutes** — 827 core lines at about 0.8 mutants per line, ~0.42 s each. That is expected, not a hang.

Set `MUTATION_FLOOR` to the measured aggregate, with a dated comment. Then **triage every survivor**: for each, either write a test that kills it, or record it in a comment as an equivalent mutant with the reason it cannot change behaviour. An unexamined survivor is not acceptable; an equivalent mutant is.

The `types.py` spike found 5 survivors of 66, including `if upper_dev < lower_dev` → `<=` surviving, which means **no test constructs a zero-width tolerance band** (`upper_dev == lower_dev`) — a legitimate case, a basic dimension with no tolerance. Report the full survivor list to the human with your triage.

- [ ] **Step 5: Commit**

```bash
git add cosmic-ray.toml scripts/check_suite_integrity.py tests/test_suite_integrity_script.py pyproject.toml
git commit -m "feat: mutation-score layer over the checker core"
```

---

