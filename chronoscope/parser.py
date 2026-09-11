# -*- coding: utf-8 -*-
#
# This file is part of Chronoscope.
#
# SPDX-FileCopyrightText: 2024 Anatoliy Bilenko <anatoliy.bilenko@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

import chronoscope.utils as u
from typing import Any
import json
import sys


class parser:
    def __init__(self, verbose=False):
        from chronoscope import db # Deferred import to break circular dependency.

        tables = []
        required_fields = {}
        for model in db.TABLES:
            required = set()
            for name, field in model._meta.fields.items():
                if not field.null:
                    required.add(name)
            tables.append(model._meta.table_name)
            required_fields[model._meta.table_name] = required
        self.tables = tables
        self.required_fields = required_fields

        self.verbose = verbose

    def parse(self, fd_chunk: list[str]) -> dict[str, list[dict[str, Any]]]:
        records: dict[str, list] = {table: [] for table in self.tables}
        for line in fd_chunk:
            try:
                record_type, fields = self.parse_line(line, records)
            except Exception as e:
                if self.verbose:
                    print(f"{e}: line={line.strip()!r}", file=sys.stderr)
                continue
            records[record_type].append(fields)
        return records

    def parse_line(self, line: str, records: dict[str, list]
                   ) -> tuple[str, dict[str, Any]] | None:
        try:
            record = json.loads(line)
        except Exception:
            return None
        if not isinstance(record, dict):
            return None

        fields = record.get("extra_fields")
        if not isinstance(fields, dict):
            return None
        record_type = fields.get("type")
        if record_type not in records:
            return None

        if "timestamp" not in record:
            raise ValueError("missing required fields: timestamp")

        time = u.ns(record["timestamp"])
        fields["time"] = time
        match record_type:
            case "event" | "state_machine_relation" | "event_attribute" | "state_machine_attribute":
                pass # No special handling required.

            case "event_relation":
                # Apply placeholder time; the from_time and to_time
                # fields are slated for removal.
                if fields["from_event_id"] is not None:
                    fields["from_time"] = time
                fields["to_time"] = time

            case "state_machine":
                fields["type"] = fields["name"]

        missing_fields = self.required_fields[record_type] - fields.keys()
        if missing_fields:
            names = ", ".join(sorted(missing_fields))
            raise ValueError(f"missing required fields: {names}")

        return record_type, fields
