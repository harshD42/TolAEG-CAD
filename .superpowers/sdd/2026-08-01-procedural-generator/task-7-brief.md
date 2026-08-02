### Task 7: Read semantic PMI from AP242

**Files:**
- Create: `validation/ap242_pmi.py`
- Test: `tests/test_ap242_pmi.py`

**Interfaces:**
- Consumes: OCP XCAF
- Produces: `read_pmi_counts(step_path) -> PmiCounts` where `PmiCounts` is a frozen dataclass with `dimensions: int`, `geometric_tolerances: int`, `datums: int`

This is the NIST oracle's read path. It lives in `validation/` because it is oracle infrastructure; the core checker must not depend on it.

**The exact call sequence below was verified by execution** against `nist_ftc_06_asme1_ap242-e2.stp`, which yields 47 dimensions, 27 geometric tolerances and 59 datums. Do not restructure it speculatively.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ap242_pmi.py
import pathlib
import pytest

pytest.importorskip("OCP", reason="requires the [gen] extra")

from validation.ap242_pmi import PmiCounts, read_pmi_counts

NIST_DIR = pathlib.Path(__file__).parent.parent / "data" / "nist_pmi"
FTC06 = NIST_DIR / "nist_ftc_06_asme1_ap242-e2.stp"

pytestmark = pytest.mark.skipif(
    not FTC06.is_file(),
    reason="NIST suite not fetched; run scripts/fetch_nist_pmi.py",
)


def test_reads_semantic_pmi_from_nist_ftc06():
    """Verified by execution 2026-08-01: 47 dimensions, 27 geotols, 59 datums.

    These are exact expected values, not bounds. If OCCT's extraction changes,
    this must fail loudly rather than silently reporting fewer tolerances.
    """
    counts = read_pmi_counts(FTC06)
    assert counts == PmiCounts(dimensions=47, geometric_tolerances=27, datums=59)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        read_pmi_counts(NIST_DIR / "does_not_exist.stp")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ap242_pmi.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'validation.ap242_pmi'` (or SKIP if the NIST suite is not yet fetched — Task 8 fetches it; if it skips, come back and re-run after Task 8)

- [ ] **Step 3: Write minimal implementation**

```python
# validation/ap242_pmi.py
"""Read semantic PMI from STEP AP242, for the NIST conformance oracle.

Oracle infrastructure: lives in validation/ so the checker core never depends
on OCP. The call sequence below was verified by execution against
nist_ftc_06_asme1_ap242-e2.stp (47 dimensions, 27 geometric tolerances,
59 datums).

Semantic PMI only. Graphical PMI (the rendered annotation symbols) needs either
OCCT's commercial visualisation component or manual tessellation, and is not
required here: the checker consumes tolerance semantics, not drawing marks.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass

from OCP.IFSelect import IFSelect_ReturnStatus
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDF import TDF_LabelSequence
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool


@dataclass(frozen=True)
class PmiCounts:
    """How many semantic PMI entities a STEP AP242 file carries."""

    dimensions: int
    geometric_tolerances: int
    datums: int


def read_pmi_counts(step_path: str | pathlib.Path) -> PmiCounts:
    """Count semantic PMI entities in an AP242 file."""
    step_path = pathlib.Path(step_path)
    if not step_path.is_file():
        raise FileNotFoundError(f"no such STEP file: {step_path}")

    doc = TDocStd_Document(TCollection_ExtendedString("tolcad"))
    reader = STEPCAFControl_Reader()
    reader.SetGDTMode(True)
    reader.SetNameMode(True)
    reader.SetColorMode(True)

    status = reader.ReadFile(str(step_path))
    if status != IFSelect_ReturnStatus.IFSelect_RetDone:
        raise ValueError(f"OCCT could not read {step_path.name}: {status}")
    if not reader.Transfer(doc):
        raise ValueError(f"OCCT could not transfer {step_path.name} into a document")

    tool = XCAFDoc_DocumentTool.DimTolTool_s(doc.Main())

    def _count(getter) -> int:
        seq = TDF_LabelSequence()
        getter(seq)
        return seq.Length()

    return PmiCounts(
        dimensions=_count(tool.GetDimensionLabels),
        geometric_tolerances=_count(tool.GetGeomToleranceLabels),
        datums=_count(tool.GetDatumLabels),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ap242_pmi.py -v`
Expected: PASS, 2 tests (run Task 8 first if they skip)

- [ ] **Step 5: Commit**

```bash
git add validation/ap242_pmi.py tests/test_ap242_pmi.py
git commit -m "feat: read semantic PMI from STEP AP242"
```

---

