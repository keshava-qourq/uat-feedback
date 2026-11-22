"""The cohort evaluation report: sensitivity and PPV (US-003-3, AC-009).

This is the one component in the codebase permitted to read ground truth, and
it reads it only through `app.labels.evaluation_labels`. Everything else --
the engine, the routers, the timeline -- sees the two allowlisted operational
fields and nothing more (NFR-013); `tests/unit/test_evaluation_scan.py`
proves that by scanning the source.

Ground truth never leaves this module as a per-patient value: the report
carries aggregate numbers only (sensitivity, PPV, the counts behind them),
never a patient's label.

The prediction itself is a placeholder until the scoring engine lands
(US-005): a patient counts as predicted positive when their leakage-safe
pre-cutoff input set carries at least `MIN_ITEMS_FOR_POSITIVE` items. It
reads only the engine's own input set, so nothing post-cutoff and no
ground-truth column can reach it.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd
from sklearn.metrics import precision_score, recall_score

from app.engine.inputs import input_set
from app.labels import evaluation_labels, operational_labels

__all__ = ["MIN_ITEMS_FOR_POSITIVE", "cohort_frame", "latest_report", "predict", "metrics"]

#: How many pre-cutoff items make the placeholder predictor say "positive".
MIN_ITEMS_FOR_POSITIVE = 3

#: What the report calls the split when the cohort holds more than one.
MIXED_SPLIT = "mixed"


def predict(db, patient_id: str) -> bool:
    """The placeholder prediction for one patient, from leakage-safe inputs only."""
    return len(input_set(db, patient_id)["items"]) >= MIN_ITEMS_FOR_POSITIVE


def cohort_frame(db) -> pd.DataFrame:
    """One row per loaded patient: its split, its truth and its prediction.

    `split` is read through the allowlisted operational accessor; `truth`
    through the evaluation-only accessor, which no other module may call.
    """
    rows = [
        {
            "patient_id": row["patient_id"],
            # The split is an operational field, so it is read as one.
            "split": operational_labels(db, row["patient_id"])["split"],
            "truth": bool(row["axspa_label"]),
            "predicted": predict(db, row["patient_id"]),
        }
        for row in evaluation_labels(db)
    ]
    return pd.DataFrame(rows, columns=["patient_id", "split", "truth", "predicted"])


def metrics(frame: pd.DataFrame) -> dict[str, float | None]:
    """Sensitivity and PPV over the frame. None when the measure is undefined."""
    if frame.empty:
        return {"sensitivity": None, "ppv": None}
    truth = frame["truth"].astype(bool)
    predicted = frame["predicted"].astype(bool)
    sensitivity = float(recall_score(truth, predicted, zero_division=0)) if truth.any() else None
    ppv = float(precision_score(truth, predicted, zero_division=0)) if predicted.any() else None
    return {"sensitivity": sensitivity, "ppv": ppv}


def _split_label(frame: pd.DataFrame) -> str:
    splits = sorted({str(value) for value in frame["split"].tolist() if str(value)})
    if not splits:
        return ""
    return splits[0] if len(splits) == 1 else MIXED_SPLIT


def latest_report(db) -> dict[str, Any]:
    """The evaluation report `GET /api/evaluation/runs/latest` serves.

    Aggregate numbers only: no patient's ground-truth value appears here.
    """
    frame = cohort_frame(db)
    scores = metrics(frame)
    split = _split_label(frame)
    counts = (
        {str(name): int(count) for name, count in frame["split"].value_counts().items()}
        if not frame.empty
        else {}
    )
    return {
        "run": {
            "computed_at": datetime.now(UTC).isoformat(),
            "patient_count": int(len(frame)),
            "split": split,
            "split_counts": counts,
        },
        "split": split,
        "cohort": "synthetic",
        "metrics": [
            {
                "key": "sensitivity",
                "label": "Sensitivity (recall)",
                "value": scores["sensitivity"],
            },
            {
                "key": "ppv",
                "label": "PPV (positive predictive value)",
                "value": scores["ppv"],
            },
        ],
    }
