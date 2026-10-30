import pandas as pd
import pytest

from richclub_explorer.target_discovery import rank_upstream_regulators


def test_coverage_and_directional_reversal():
    rel = pd.DataFrame([
        {"regulator": "C3", "target": "A", "effect": 1, "confidence": .8},
        {"regulator": "C3", "target": "B", "effect": -1, "confidence": .9},
        {"regulator": "TNF", "target": "A", "effect": 1, "confidence": .5},
    ])
    exp = pd.DataFrame([
        {"gene": "A", "log2_fold_change": 2.0},
        {"gene": "B", "log2_fold_change": -1.0},
    ])
    out = rank_upstream_regulators({"A", "B", "C"}, rel, exp)
    c3 = out.set_index("regulator").loc["C3"]
    assert c3["direct_targets"] == 2
    assert c3["coverage"] == pytest.approx(2 / 3)
    assert c3["reversal_fraction"] == pytest.approx(1.0)
    assert c3["proposed_action"] == "inhibit"


def test_unknown_direction_never_predicts_reversal():
    out = rank_upstream_regulators(
        ["A"],
        pd.DataFrame([{"regulator": "R", "target": "A", "effect": 0}]),
        pd.DataFrame([{"gene": "A", "log2_fold_change": 1.0}]),
    )
    assert pd.isna(out.loc[0, "reversal_fraction"])
    assert out.loc[0, "proposed_action"] == "unresolved"


def test_invalid_effect_fails_loudly():
    with pytest.raises(ValueError, match="effect"):
        rank_upstream_regulators(
            ["A"], pd.DataFrame([{"regulator": "R", "target": "A", "effect": 2}])
        )


def test_missing_gene_matches_empty_result():
    out = rank_upstream_regulators(
        ["B"], pd.DataFrame([{"regulator": "R", "target": "A", "effect": 1}])
    )
    assert out.empty
