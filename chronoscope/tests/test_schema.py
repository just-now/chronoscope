# -*- coding: utf-8 -*-
#
# This file is part of Chronoscope.
#
# SPDX-FileCopyrightText: 2024 Anatoliy Bilenko <anatoliy.bilenko@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#
# Cross-validation between log-entry-schema.json and the chronoscope
# pipeline (parser + database models), plus schema conformance of the
# golden fixture.

import json
from pathlib import Path

import chronoscope.db as models
import jsonschema
from chronoscope.parser import parser

REPO = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = REPO / "log-entry-schema.json"
FIXTURE_PATH = REPO / "test" / "raft_trace.jsonl"

# Fields the parser derives from the envelope timestamp: present in the
# database, never present in a trace record.
DERIVED_FIELDS = {"time", "from_time", "to_time"}

# $defs entries that describe reusable fragments, not record types.
helper_defs = {"identifier"}
DERIVED_FIELDS = {"time", "from_time", "to_time"}

COLUMNS = {model._meta.table_name: set(model._meta.fields)
           for model in models.TABLES}


def load_schema() -> dict:
    with open(SCHEMA_PATH) as fd:
        return json.load(fd)


def load_validator() -> jsonschema.Draft202012Validator:
    schema = load_schema()
    validator = jsonschema.validators.validator_for(schema)(schema)
    validator.check_schema(schema)
    return validator


def test_schema_database_conformity():
    # The schema and the database models must describe the same record
    # types and agree on which record fields are required.
    schema_types = set(load_schema()["$defs"]) - helper_defs
    assert schema_types == set(COLUMNS), \
        (f"schema and database disagree on record types: "
         f"schema-only={sorted(schema_types - set(COLUMNS))} "
         f"database-only={sorted(set(COLUMNS) - schema_types)}")

    required = parser().required_fields
    for name, defn in load_schema()["$defs"].items():
        if name in helper_defs:
            continue
        schema_required = set(defn["required"]) - {"type"}
        parser_required = required[name] - DERIVED_FIELDS

        missing = parser_required - schema_required
        assert not missing, \
            f"{name}: parser requires {sorted(missing)}; schema does not"

        unstorable = schema_required - COLUMNS[name] - DERIVED_FIELDS
        assert not unstorable, \
            f"{name}: schema requires unstorable {sorted(unstorable)}"


def test_test_data_conformity():
    # Ensure that the sample log file conforms to the schema.
    validator = load_validator()
    with open(FIXTURE_PATH) as fd:
        for n, line in enumerate(fd, 1):
            errors = sorted(validator.iter_errors(json.loads(line)),
                            key=lambda e: e.json_path)
            assert not errors, \
                f"line {n}: " + "; ".join(e.message for e in errors[:3])
