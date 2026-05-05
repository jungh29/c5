import xml.etree.ElementTree as ET
import zipfile

from openbim_viewer.bcf_loader import (
    strip_ns,
    flatten_xml,
    extract_all_ifc_guids_from_xml,
    list_bcf_files,
    extract_bcf_topics,
    extract_bcf_viewpoints,
)


def test_strip_ns_removes_namespace():
    assert strip_ns("{urn:test}Topic") == "Topic"
    assert strip_ns("Topic") == "Topic"


def test_flatten_xml_extracts_text_attrs_and_repeated_fields():
    root = ET.fromstring(
        """
        <Root custom="x">
            <Field>one</Field>
            <Field>two</Field>
            <Unknown foo="bar">v</Unknown>
        </Root>
        """
    )
    flat = flatten_xml(root)
    assert flat["attr:Root@custom"] == "x"
    assert flat["text:Field"] == ["one", "two"]
    assert flat["text:Unknown"] == "v"
    assert flat["attr:Unknown@foo"] == "bar"


def test_extract_all_ifc_guids_component_and_heuristics_stable_order():
    root = ET.fromstring(
        """
        <VisualizationInfo>
          <Components>
            <Component IfcGuid="G1"/>
            <Selection ifc_guid="G2"/>
            <Visibility Guid="G1"/>
            <Item GlobalId="G3"/>
          </Components>
        </VisualizationInfo>
        """
    )
    assert extract_all_ifc_guids_from_xml(root) == ["G1", "G2", "G3"]


def test_extract_topics_and_viewpoints_from_small_zip(tmp_path):
    bcf = tmp_path / "sample.bcfzip"
    with zipfile.ZipFile(bcf, "w") as zf:
        zf.writestr(
            "topicA/markup.bcf",
            """
            <Markup>
              <Topic Guid='T1'>
                <Title>Issue A</Title>
                <TopicStatus>Open</TopicStatus>
                <TopicType>Clash</TopicType>
                <Priority>High</Priority>
                <CreationAuthor>alice</CreationAuthor>
                <CreationDate>2026-01-01</CreationDate>
              </Topic>
              <Comment>Check wall</Comment>
            </Markup>
            """,
        )
        zf.writestr(
            "topicA/viewpoint.bcfv",
            """
            <VisualizationInfo>
              <Components>
                <Component IfcGuid='WALL1'/>
              </Components>
            </VisualizationInfo>
            """,
        )

    files = list_bcf_files(bcf)
    assert "topicA/markup.bcf" in files
    assert "topicA/viewpoint.bcfv" in files

    topics = extract_bcf_topics(bcf)
    assert len(topics) == 1
    t = topics[0]
    assert t["topic_dir"] == "topicA"
    assert t["title"] == "Issue A"
    assert t["status"] == "Open"
    assert t["comments"] == ["Check wall"]

    viewpoints = extract_bcf_viewpoints(bcf)
    assert len(viewpoints) == 1
    v = viewpoints[0]
    assert v["topic_dir"] == "topicA"
    assert v["referenced_ifc_guids"] == ["WALL1"]


def test_missing_optional_fields_do_not_crash(tmp_path):
    bcf = tmp_path / "missing.bcfzip"
    with zipfile.ZipFile(bcf, "w") as zf:
        zf.writestr("topicB/markup.bcf", "<Markup><Topic Guid='T2'></Topic></Markup>")
        zf.writestr("topicB/vp.bcfv", "<VisualizationInfo><Components/></VisualizationInfo>")

    topics = extract_bcf_topics(bcf)
    viewpoints = extract_bcf_viewpoints(bcf)
    assert topics[0]["title"] is None
    assert topics[0]["status"] is None
    assert viewpoints[0]["referenced_ifc_guids"] == []
