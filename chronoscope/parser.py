# -*- coding: utf-8 -*-
#
# This file is part of Chronoscope.
#
# SPDX-FileCopyrightText: 2024 Anatoliy Bilenko <anatoliy.bilenko@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

import chronoscope.utils as u
from typing import Callable
import yaml
import sys


class parser:
    def __init__(self, conf_path: str, verbose=False):
        # type -> (dest_table, parser_func)
        self.parsers: dict[str, tuple[str, Callable]] = {}
        # the parser knows about table names
        self.tables = ["state_machine", "event", "event_relation",
                       "state_machine_relation", "event_attribute"]
        self.verbose = verbose
        self.load_config(conf_path)

    def load_config(self, conf_path: str):
        with open(conf_path) as fd:
            conf = yaml.safe_load(fd)
            conf_tables = [t for t in conf.keys() if t[0] != '.']
            if not all(t in self.tables for t in conf_tables):
                raise SyntaxError(f"a few of {conf_tables} aren't known!")

            for table in conf_tables:
                for trace in conf[table]:
                    self.register_parser(table, trace["type"],
                                         self.make_parser(table, trace["pos"]))

    def make_parser(self, table: str, kwargs: dict[str, int]) -> Callable:
        match table:
            case "state_machine":
                return self.make_state_machine_parser(**kwargs)
            case "event":
                return self.make_event_parser(**kwargs)
            case "event_relation":
                return self.make_event_rel_parser(**kwargs)
            case "state_machine_relation":
                return self.make_sm_rel_parser(**kwargs)
            case "event_attribute":
                return self.make_event_attribute_parser(**kwargs)
        raise NotImplementedError()

    def make_event_parser(self, type: int, time: int, event: int,
                           sm_id: int) -> Callable:
        def parse(line: list[str], parse_type: str):
            if type >= len(line) or parse_type != line[type]:
                return None
            eid = None
            for token in line:
                if token.startswith("eid="):
                    eid = int(token.split("=", 1)[1], 16)
                    break
            if eid is None:
                return None
            sm = int(line[sm_id], 0)
            return {
                "state_machine": {"id": sm, "name": parse_type, "type": parse_type},
                "event": {"id": eid, "state_machine_id": sm,
                          "time": u.ns(line[time]), "name": line[event]},
            }
        return parse

    def make_event_rel_parser(self, type: int, sm_id: int,
                              peid: int, eid: int, time: int) -> Callable:
        def parse(line: list[str], parse_type: str):
            if type >= len(line) or parse_type != line[type]:
                return None
            raw_peid = line[peid].split("=", 1)[1]
            from_eid = None if raw_peid == "None" else int(raw_peid, 16)
            to_eid = int(line[eid].split("=", 1)[1], 16)
            record = {
                "event_relation": {
                    "from_event_id": from_eid,
                    "to_event_id": to_eid,
                    "relation": parse_type,
                },
            }
            if from_eid is None:
                record["event"] = {
                    "id": to_eid,
                    "state_machine_id": int(line[sm_id], 0),
                    "time": u.ns(line[time]),
                    "name": None,
                }
            return record
        return parse

    def make_state_machine_parser(self, type: int, time: int,
                                  sm_id: int, name: int, state: int) -> Callable:
        def parse(line: list[str], parse_type: str):
            if type >= len(line) or parse_type != line[type]:
                return None
            sm = int(line[sm_id].split("=", 1)[1], 0)
            raw_name = line[name].split("=", 1)[1]
            raw_state = line[state].split("=", 1)[1]
            eid = None
            for token in line:
                if token.startswith("eid="):
                    eid = int(token.split("=", 1)[1], 16)
                    break
            if eid is None:
                return None
            return {
                "state_machine": {"id": sm, "name": raw_name, "type": raw_name},
                "event": {"id": eid, "state_machine_id": sm,
                          "time": u.ns(line[time]), "name": raw_state},
            }
        return parse

    def make_sm_rel_parser(self, type: int,
                           from_sm_id: int, to_sm_id: int,
                           relation: int) -> Callable:
        def parse(line: list[str], parse_type: str):
            if type >= len(line) or parse_type != line[type]:
                return None
            from_sm = int(line[from_sm_id].split("=", 1)[1], 0)
            to_sm = int(line[to_sm_id].split("=", 1)[1], 0)
            rel = line[relation].split("=", 1)[1]
            record = {
                "state_machine_relation": {
                    "from_sm_id": from_sm,
                    "to_sm_id": to_sm,
                    "relation": rel,
                }
            }
            if rel == "top-to-raft":
                record["state_machine"] = {"id": from_sm, "name": "top", "type": "top"}
            return record
        return parse

    def make_event_attribute_parser(self, type: int,
                                    eid: int, attribute: int) -> Callable:
        def parse(line: list[str], parse_type: str):
            if type >= len(line) or parse_type != line[type]:
                return None
            event_id = int(line[eid].split("=", 1)[1], 16)
            key, value = line[attribute].split("=", 1)
            return {
                "event_attribute": {
                    "event_id": event_id,
                    "key": key,
                    "value": value,
                },
            }
        return parse

    def register_parser(self, dest_table: str, type: str, parse: Callable):
        self.parsers[type] = (dest_table, parse)

    def parse(self,
              fd_chunk: list[str]) -> dict[str, list[dict[str, str | int]]]:
        records: dict[str, list] = {t: [] for t in self.tables}
        for line in fd_chunk:
            for p_name, (dest_table, parser) in self.parsers.items():
                try:
                    if record := parser(line.split(), p_name):
                        self._merge_record(records, record)
                except Exception as e:
                    if self.verbose:
                        print(f"{e}: {line=}", file=sys.stderr)
        return records

    def _merge_record(self, records: dict, record: dict):
        for table, payload in record.items():
            if isinstance(payload, list):
                records[table].extend(payload)
            else:
                records[table].append(payload)
