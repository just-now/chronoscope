import pytest
from chronoscope.parser import parser

RAFT_YAML = "test/raft_chronoscope.yaml"


def test_parser_file_not_found():
    with pytest.raises(FileNotFoundError):
        _ = parser("")


def test_parser_event():
    line = (
        "raft[1]: 2026-07-06T19:44:22.172542000 raft sm_id: 0x1000000000000001 "
        "eid=0x1000000000000001 role=Follower term=1 log=0 ci=0 lc=0 |"
    )
    records = parser(RAFT_YAML).parse([line])
    assert len(records["event"]) == 1
    assert len(records["state_machine"]) == 1
    assert records["event"][0]["name"] == "role=Follower"
    assert records["event"][0]["id"] == 0x1000000000000001


def test_parser_event_relation_send():
    line = (
        "raft[1]: 2026-07-06T19:44:22.175353000 event_relation sm_id: 0x1000000000000001 "
        "eid=0x1000000000000006 peid=None |"
    )
    records = parser(RAFT_YAML).parse([line])
    assert len(records["event_relation"]) == 1
    er = records["event_relation"][0]
    assert er == {
        "from_event_id": None,
        "to_event_id": 0x1000000000000006,
        "relation": "event_relation",
    }
    assert records["event"] == [{
        "id": 0x1000000000000006,
        "state_machine_id": 0x1000000000000001,
        "time": 1783359862175353000,
        "name": None,
    }]


def test_parser_event_relation_recv():
    line = (
        "raft[1]: 2026-07-06T19:44:22.175565000 event_relation sm_id: 0x1000000000000005 "
        "eid=0x100000000000000c peid=0x1000000000000007 |"
    )
    records = parser(RAFT_YAML).parse([line])
    assert len(records["event_relation"]) == 1
    er = records["event_relation"][0]
    assert er == {
        "from_event_id": 0x1000000000000007,
        "to_event_id": 0x100000000000000C,
        "relation": "event_relation",
    }
    assert records["event"] == []


def test_parser_event_attribute():
    line = (
        "raft[1]: 2026-07-22T08:28:19.113535000 event_attribute "
        "eid=0x100000000000000c raft:role=Follower |"
    )
    records = parser(RAFT_YAML).parse([line])
    assert len(records["event_attribute"]) == 1
    attribute = records["event_attribute"][0]
    assert attribute["event_id"] == 0x100000000000000C
    assert attribute["key"] == "raft:role"
    assert attribute["value"] == "Follower"


def test_parser_sm_relation():
    line = (
        "sm[1]: 2025-06-07T11:00:14.026305714 state_machine_relation "
        "from_sm_id=0x1000000000000457 to_sm_id=0x1000000000000001 "
        "relation=top-to-raft |"
    )
    records = parser(RAFT_YAML).parse([line])
    assert len(records["state_machine_relation"]) == 1
    assert len(records["state_machine"]) == 1
    smr = records["state_machine_relation"][0]
    assert smr["relation"] == "top-to-raft"


def test_parser_state_machine():
    line = (
        "sm[1]: 2026-07-14T13:12:56.473265000 state_machine "
        "sm_id=0x1000000000000018 name=DtxState state=Init "
        "eid=0x1000000000000019 |"
    )
    records = parser(RAFT_YAML).parse([line])
    assert len(records["state_machine"]) == 1
    assert len(records["event"]) == 1
    assert records["state_machine"][0]["type"] == "DtxState"
    assert records["event"][0]["name"] == "Init"


def test_parser_malformed():
    line = "raft[1]: 2026-07-06T19:44:22.667095559 raft"
    _ = parser(RAFT_YAML, verbose=True).parse([line])


def test_parser_fuzz():
    line = "a b c d"
    _ = parser(RAFT_YAML).parse([line])


def test_parser_empty():
    line = ""
    _ = parser(RAFT_YAML).parse([line])
