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
