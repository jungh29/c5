import pandas as pd

from openbim_viewer.cli import _summary_from_mapping, run_inspect


def test_summary_from_mapping_counts_correctly():
    df = pd.DataFrame(
        [
            {"referenced_ifc_guid": "G1", "found_in_ifc": True},
            {"referenced_ifc_guid": "G2", "found_in_ifc": False},
            {"referenced_ifc_guid": None, "found_in_ifc": False},
        ]
    )
    s = _summary_from_mapping(df, ifc_count=10, topics_count=3, viewpoints_count=2)
    assert s["ifc_products"] == 10
    assert s["bcf_topics"] == 3
    assert s["bcf_viewpoints"] == 2
    assert s["referenced_guids"] == 2
    assert s["found_guids"] == 1
    assert s["missing_guids"] == 1


def test_run_inspect_missing_files_returns_2(tmp_path):
    missing_ifc = tmp_path / "missing.ifc"
    missing_bcf = tmp_path / "missing.bcfzip"
    code = run_inspect(str(missing_ifc), str(missing_bcf), exports_dir=str(tmp_path / "exports"))
    assert code == 2
