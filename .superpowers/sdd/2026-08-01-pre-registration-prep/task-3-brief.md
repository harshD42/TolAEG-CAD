### Task 3: Record the projected tolerance zone the B-4 verdict assumes

**Files:**
- Modify: `src/tolcad/gen/spec.py`
- Modify: `src/tolcad/gen/sampler.py`
- Test: `tests/gen/test_spec.py`, `tests/gen/test_sampler.py`

**Interfaces:**
- Consumes: nothing new
- Produces: `MateSpec.projected_zone_mm: float | None = None`, serialised in the sidecar

`src/tolcad/y14_5.py:80-81` states, as a load-bearing precondition rather than a footnote: *"This module implements B-4 only, so applying it to a drawing without a projected tolerance zone is OPTIMISTIC (unsafe); the generator must emit projected zones."* This generator is that generator, and it currently emits nothing of the kind. Every fixed-fastener verdict in the corpus is therefore optimistic by the core module's own contract.

The fix is to make the assumption explicit in the schema. The projection distance `P` is physically the thickness of the part the fastener passes through before entering the tapped feature — that is `plate_thickness_mm`.

**The checker does not consume this field, and `to_check_dict()` must not emit it.** B-4's formula has no `P` term; `P` appears only in B-5, which this plan explicitly does not implement. The field's job is to state in the published schema the condition under which the recorded verdict is valid.

- [ ] **Step 1: Write the failing tests**

Append to `tests/gen/test_spec.py`:

```python
def test_fixed_fastener_requires_a_projected_zone():
    """y14_5.py names the projected zone a precondition of its B-4 formula.

    Without one, the recorded verdict is optimistic and the schema does not
    say so. Refusing to build such a mate is how that stays true.
    """
    with pytest.raises(ValueError, match="projected_zone_mm"):
        MateSpec(
            kind="fixed_fastener", nominal_mm=8.0,
            hole_a={"nominal": 9.0, "lower_dev": 0.0, "upper_dev": 0.2},
            hole_b={"nominal": 6.8, "lower_dev": 0.0, "upper_dev": 0.2},
            fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
            designation=None, position_tol_a=0.2, position_tol_b=0.2,
        )


def test_projected_zone_must_be_positive():
    with pytest.raises(ValueError, match="projected_zone_mm"):
        MateSpec(
            kind="fixed_fastener", nominal_mm=8.0,
            hole_a={"nominal": 9.0, "lower_dev": 0.0, "upper_dev": 0.2},
            hole_b={"nominal": 6.8, "lower_dev": 0.0, "upper_dev": 0.2},
            fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
            designation=None, position_tol_a=0.2, position_tol_b=0.2,
            projected_zone_mm=0.0,
        )


def test_non_fixed_kinds_must_not_carry_a_projected_zone():
    """B-3 (floating) has no projection term; carrying one would imply it does."""
    with pytest.raises(ValueError, match="projected_zone_mm"):
        MateSpec(
            kind="floating_fastener", nominal_mm=8.0,
            hole_a={"nominal": 9.0, "lower_dev": 0.0, "upper_dev": 0.2},
            hole_b={"nominal": 9.0, "lower_dev": 0.0, "upper_dev": 0.2},
            fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
            designation=None, position_tol_a=0.2, position_tol_b=0.2,
            projected_zone_mm=8.0,
        )


def test_projected_zone_is_not_sent_to_the_checker():
    """B-4 has no P term -- that is B-5, which tolcad does not implement.

    Emitting it would imply the checker consumes it, which it does not.
    """
    mate = MateSpec(
        kind="fixed_fastener", nominal_mm=8.0,
        hole_a={"nominal": 9.0, "lower_dev": 0.0, "upper_dev": 0.2},
        hole_b={"nominal": 6.8, "lower_dev": 0.0, "upper_dev": 0.2},
        fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
        designation=None, position_tol_a=0.2, position_tol_b=0.2,
        projected_zone_mm=8.0,
    )
    assert "projected_zone_mm" not in mate.to_check_dict()
    assert check(mate.to_check_dict()).assembles is True
```

Append to `tests/gen/test_sampler.py`:

```python
def test_every_sampled_fixed_fastener_records_its_projected_zone():
    seen = 0
    for seed in range(60):
        for difficulty in (1, 2, 3, 4):
            spec = sample_assembly(seed, difficulty)
            for mate in spec.mates:
                if mate.kind != "fixed_fastener":
                    assert mate.projected_zone_mm is None
                    continue
                seen += 1
                assert mate.projected_zone_mm == pytest.approx(
                    spec.plate_thickness_mm
                ), "the projection is the thickness the fastener passes through"
    assert seen > 0, "no fixed fasteners sampled"


def test_projected_zone_survives_the_sidecar_round_trip():
    from tolcad.gen.spec import AssemblySpec
    spec = next(
        s for seed in range(60)
        for s in [sample_assembly(seed, 4)]
        if any(m.kind == "fixed_fastener" for m in s.mates)
    )
    assert AssemblySpec.from_json(spec.to_json()) == spec
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/gen/test_spec.py tests/gen/test_sampler.py -v -k "projected"`
Expected: FAIL — `TypeError: MateSpec.__init__() got an unexpected keyword argument 'projected_zone_mm'` for the tests that pass it, and the `pytest.raises` tests failing because no error is raised.

- [ ] **Step 3: Add the field, the validation, and the sampler wiring**

In `src/tolcad/gen/spec.py`, add the field immediately after `mc_n`:

```python
    # ASME Y14.5 Appendix B-4 -- the formula y14_5.fastener_assembles implements
    # for the fixed case -- is titled "...When Projected Tolerance Zone Is Used"
    # and assumes exactly that. y14_5.py states the precondition outright: apply
    # B-4 without a projected zone and the margin is OPTIMISTIC, i.e. unsafe.
    # B-5 covers the non-projected case with a (1 + 2P/D) multiplier on T2, and
    # tolcad does NOT implement it. Recording the projection here is how the
    # published schema states the condition its verdict is valid under.
    # The projection is the thickness of the part the fastener crosses before
    # reaching the tapped feature. Required and positive for fixed_fastener;
    # None for every other kind, since no other formula has a projection term.
    projected_zone_mm: float | None = None
```

In the same file, add to `__post_init__`, inside the `else:` branch that already handles `floating_fastener` / `fixed_fastener`, and add a guard for the other kinds. Replace the whole `__post_init__` validation body after the `mc_n` check with:

```python
        if self.kind not in VALID_KINDS:
            raise ValueError(
                f"unknown mate kind {self.kind!r}; have {sorted(VALID_KINDS)}"
            )
        if self.kind != "fixed_fastener" and self.projected_zone_mm is not None:
            raise ValueError(
                f"projected_zone_mm applies only to fixed_fastener (Y14.5 B-4); "
                f"{self.kind} carries no projection term, got "
                f"{self.projected_zone_mm}"
            )
        if self.kind == "iso_fit":
            if not self.designation:
                raise ValueError("iso_fit mate requires a designation such as 'H7/g6'")
        elif self.kind == "virtual_condition":
            if self.fastener is None:
                raise ValueError("virtual_condition mate requires a fastener")
            if self.hole_a is None:
                raise ValueError("virtual_condition mate requires hole_a")
        else:  # floating_fastener or fixed_fastener
            if self.fastener is None:
                raise ValueError(f"{self.kind} mate requires a fastener")
            if self.hole_a is None:
                raise ValueError(f"{self.kind} mate requires hole_a")
            if self.hole_b is None:
                raise ValueError(f"{self.kind} mate requires hole_b")
            if self.kind == "fixed_fastener" and not (
                self.projected_zone_mm is not None and self.projected_zone_mm > 0.0
            ):
                raise ValueError(
                    "fixed_fastener requires a positive projected_zone_mm: "
                    "y14_5 implements ASME Y14.5 B-4, which assumes a projected "
                    "tolerance zone, and is optimistic without one. Got "
                    f"{self.projected_zone_mm}"
                )
```

In `src/tolcad/gen/sampler.py`, add a module constant next to `_MC_SAMPLES`:

```python
# The plate thickness the sampler builds to. Also the projection distance for a
# fixed fastener: the fastener crosses part_a's full thickness before it reaches
# the tapped feature in part_b. Kept as one constant so the recorded projected
# zone and the built geometry cannot drift apart.
_PLATE_THICKNESS_MM = 8.0
```

Change `_tier1_mate`'s returned `MateSpec` to add one argument after `position_tol_b=tol_b,`:

```python
        projected_zone_mm=(
            _PLATE_THICKNESS_MM if kind == "fixed_fastener" else None
        ),
```

and change the `AssemblySpec(...)` construction at the end of `sample_assembly` to set the thickness explicitly:

```python
    return AssemblySpec(
        seed=seed,
        difficulty=difficulty,
        mates=mates,
        plate_size_mm=plate_size_for_mates(mates),
        plate_thickness_mm=_PLATE_THICKNESS_MM,
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/gen/test_spec.py tests/gen/test_sampler.py -v`
Expected: PASS.

Then the full suite: `python -m pytest -q -m "not slow"`.

**Existing `MateSpec(kind="fixed_fastener", ...)` constructions in the test suite will now raise.** Grep for them and add `projected_zone_mm=8.0`:

```bash
grep -rn "fixed_fastener" tests/
```

Do not work around the new validation by switching those fixtures to `floating_fastener` — that would silently delete fixed-case coverage.

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/gen/spec.py src/tolcad/gen/sampler.py tests/gen/test_spec.py tests/gen/test_sampler.py
git commit -m "feat: record the projected tolerance zone B-4 assumes"
```

---

