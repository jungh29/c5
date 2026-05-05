from openbim_viewer.ifc_loader import to_ifc_dataframe


def test_to_ifc_dataframe_from_artificial_index_and_optional_fields():
    ifc_index = {
        "G1": {
            "global_id": "G1",
            "ifc_type": "IfcWall",
            "name": "Wall A",
            "tag": None,
            "step_id": 10,
            "entity": object(),
        },
        "G2": {
            "global_id": "G2",
            "ifc_type": "IfcDoor",
            "name": None,
            "tag": "D-01",
            "step_id": None,
            "entity": object(),
        },
    }

    df = to_ifc_dataframe(ifc_index)

    assert len(df) == 2
    for col in ["global_id", "ifc_type", "name", "tag", "step_id", "entity"]:
        assert col in df.columns
