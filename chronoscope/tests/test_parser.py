from chronoscope.parser import parser
import chronoscope.utils as u


TIMESTAMP = "2026-07-06T19:44:22.172542000"


def test_parser_event():
    line = (
        '{"timestamp":"2026-07-06T19:44:22.172542000","thread_id":1,'
        '"extra_fields":{"type":"event","id":1152921504606846977,'
        '"state_machine_id":1152921504606846977,"name":"role=Follower"}}'
    )
    records = parser().parse([line])
    assert len(records["event"]) == 1
    assert records["event"][0]["name"] == "role=Follower"
    assert records["event"][0]["id"] == 0x1000000000000001


def test_parser_state_machine_record():
    line = (
        '{"timestamp":"2026-07-06T19:44:22.172542000",'
        '"extra_fields":{"type":"state_machine",'
        '"id":1152921504606846979,"name":"FirstRecordState"}}'
    )
    records = parser().parse([line])
    assert records["state_machine"] == [{
        "type": "FirstRecordState",
        "id": 1152921504606846979,
        "name": "FirstRecordState",
        "time": u.ns("2026-07-06T19:44:22.172542000"),
    }]

def test_parser_event_relation_send():
    line = (
        '{"timestamp":"2026-07-06T19:44:22.175353000",'
        '"extra_fields":{"type":"event_relation","from_event_id":null,'
        '"to_event_id":1152921504606846982,"from_sm_id":null,"from_time":null,'
        '"to_sm_id":1152921504606846977,"to_time":1783367062175353000,'
        '"relation":"event_relation"}}'
    )
    records = parser().parse([line])
    assert len(records["event_relation"]) == 1
    er = records["event_relation"][0]
    assert er["from_event_id"] is None
    assert er["to_event_id"] == 0x1000000000000006
    assert er["from_sm_id"] is None
    assert er["from_time"] is None
    assert er["to_time"] == u.ns("2026-07-06T19:44:22.175353000")


def test_parser_fuzz():
    line = "a b c d"
    _ = parser().parse([line])


def test_parser_empty():
    line = ""
    _ = parser().parse([line])


def test_parser_state_machine_attribute():
    line = (
        '{"timestamp":"2026-07-14T13:12:56.473265000",'
        '"extra_fields":{"type":"state_machine_attribute",'
        '"state_machine_id":1152921504606846977,"key":"node","value":1}}'
    )
    records = parser().parse([line])
    assert len(records["state_machine_attribute"]) == 1
    assert records["state_machine_attribute"][0]["value"] == 1


def test_parser_reads_only_extra_fields():
    line = (
        '{"timestamp":"2026-07-06T19:44:22.172542000",'
        '"extra_fields":{"type":"event","id":1152921504606846977,'
        '"state_machine_id":1152921504606846977,"name":"role=Follower",'
        '"file":"raft.rs"}}'
    )
    record = parser().parse([line])["event"][0]
    assert record["file"] == "raft.rs"
