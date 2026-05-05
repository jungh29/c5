import pandas as pd

from openbim_viewer.mapping import map_bcf_to_ifc, group_topic_guids


def test_map_bcf_to_ifc_expected_columns_and_found_flags():
    topics = [{"topic_dir": "topicA", "topic_guid": "T1", "title": "A", "status": "Open"}]
    viewpoints = [{"topic_dir": "topicA", "viewpoint_file": "topicA/view1.bcfv", "referenced_ifc_guids": ["G1", "G2"]}]
    ifc_index = {"G1": {"ifc_type": "IfcWall", "name": "Wall", "tag": "W", "step_id": 10}}

    df = map_bcf_to_ifc(topics, viewpoints, ifc_index)
    assert {"topic_dir", "topic_guid", "topic_title", "topic_status", "viewpoint_file", "referenced_ifc_guid", "found_in_ifc", "ifc_type", "ifc_name", "ifc_tag", "ifc_step_id"}.issubset(df.columns)

    assert bool(df[df["referenced_ifc_guid"] == "G1"].iloc[0]["found_in_ifc"]) is True
    assert bool(df[df["referenced_ifc_guid"] == "G2"].iloc[0]["found_in_ifc"]) is False


def test_map_bcf_to_ifc_topic_without_guid_or_viewpoint():
    topics = [{"topic_dir": "topicX", "topic_guid": "TX", "title": "No VP", "status": "Open"}]
    df = map_bcf_to_ifc(topics, viewpoints=[], ifc_index={})
    assert len(df) == 1
    assert df.iloc[0]["referenced_ifc_guid"] is None
    assert bool(df.iloc[0]["found_in_ifc"]) is False


def test_group_topic_guids_aggregates_and_empty():
    df = pd.DataFrame(
        [
            {"topic_dir": "topicA", "topic_guid": "T1", "topic_title": "A", "topic_status": "Open", "referenced_ifc_guid": "G1", "found_in_ifc": True},
            {"topic_dir": "topicA", "topic_guid": "T1", "topic_title": "A", "topic_status": "Open", "referenced_ifc_guid": "G2", "found_in_ifc": False},
        ]
    )
    grouped = group_topic_guids(df)
    assert grouped.iloc[0]["referenced_ifc_guids"] == ["G1", "G2"]

    empty_grouped = group_topic_guids(pd.DataFrame())
    assert isinstance(empty_grouped, pd.DataFrame)
