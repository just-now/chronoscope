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

class parser:
    def __init__(self, conf_path: str):
        # type -> (dest_table, parser_func)
        self.parsers: dict[str, tuple[str, Callable]] = {}
        # the parser knows about table names
        self.tables = ["tick", "attr", "relation"]
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
            case "tick":
                return self.make_req_parser(**kwargs)
            case "relation":
                return self.make_rel_parser(**kwargs)
            case "attr":
                return self.make_attr_parser(**kwargs)
        raise NotImplementedError()

    def make_req_parser(self, type: int, time: int, event: int,
                        pid: int, id: int) -> Callable:
        def parse(line: list[str], parse_type: str):
            return {
                "time": u.ns(line[time]),
                "type": line[type], "event": line[event],
                "id": u.pack(int(line[id]), int(line[pid]))
            } if parse_type == line[type] else None
        return parse

    def make_rel_parser(self, orig_id: int, dest_id: int,
                        orig_pid: int, dest_pid: int, type: int) -> Callable:
        def parse(line: list[str], parse_type: str):
            return {
                "orig": u.pack(int(line[orig_id]), int(line[orig_pid])),
                "dest": u.pack(int(line[dest_id]), int(line[orig_pid])),
                "type": line[type]
            } if parse_type == line[type] else None
        return parse

    def make_attr_parser(self, id: int, pid: int,
                         name: int, value: int, type: int) -> Callable:
        def parse(line: list[str], parse_type: str):
            return {
                "id": u.pack(int(line[id]), int(line[pid])),
                "val": line[value],
                "name": line[name],
            } if parse_type == line[type] else None
        return parse

    def register_parser(self, dest_table: str, type: str, parse: Callable):
        self.parsers[type] = (dest_table, parse)

    def parse(self,
              fd_chunk: list[str]) -> dict[str, list[dict[str, str | int]]]:
        records: dict[str, list] = {t: [] for t in self.tables}
        for line in fd_chunk:
            for p_name, (dest_table, parser) in self.parsers.items():
                if record := parser(line.split(), p_name):
                    records[dest_table].append(record)
        return records
