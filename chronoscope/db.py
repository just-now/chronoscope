# -*- coding: utf-8 -*-
#
# This file is part of Chronoscope.
#
# SPDX-FileCopyrightText: 2024 Anatoliy Bilenko <anatoliy.bilenko@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

import chronoscope.parser as pr
from typing import Callable, cast
import subprocess as sp
import builtins as b
import peewee as p
import os

db = p.SqliteDatabase(None)


class state_machine(p.Model):
    id = p.IntegerField()
    name = p.TextField()
    type = p.TextField(null=True)

    class Meta:
        database = db
        primary_key = p.CompositeKey("id")


class event(p.Model):
    id = p.IntegerField()
    state_machine_id = p.IntegerField()
    time = p.IntegerField()
    name = p.TextField()

    class Meta:
        database = db
        primary_key = p.CompositeKey("id")


class event_relation(p.Model):
    from_event_id = p.IntegerField(null=True)
    to_event_id = p.IntegerField()
    from_sm_id = p.IntegerField(null=True)
    from_time = p.IntegerField(null=True)
    to_sm_id = p.IntegerField()
    to_time = p.IntegerField()
    relation = p.TextField()

    class Meta:
        database = db
        primary_key = p.CompositeKey("from_event_id", "to_event_id", "relation")


class state_machine_relation(p.Model):
    from_sm_id = p.IntegerField()
    to_sm_id = p.IntegerField()
    relation = p.TextField()

    class Meta:
        database = db
        primary_key = p.CompositeKey("from_sm_id", "to_sm_id", "relation")


class state_machine_attribute(p.Model):
    state_machine_id = p.IntegerField()
    key = p.TextField()
    value = p.TextField()

    class Meta:
        database = db
        primary_key = p.CompositeKey("state_machine_id", "key")


class event_attribute(p.Model):
    event_id = p.IntegerField()
    key = p.TextField()
    value = p.TextField()

    class Meta:
        database = db
        primary_key = p.CompositeKey("event_id", "key")


TABLES = [state_machine, event, event_relation,
          state_machine_relation, state_machine_attribute, event_attribute]
VERBOSE = False


def open(path: str, opts: None | dict[str, int | str] = None, create=False,
         verbose=False):
    global VERBOSE
    VERBOSE = verbose

    if create and os.path.exists(path):
        raise FileExistsError(f"`{path}' exists!")
    if not create and not os.path.exists(path):
        raise FileNotFoundError(f"`{path}' not found!")

    db.init(path, opts)
    db.connect()
    if create:
        with db:
            db.create_tables(TABLES)


def close():
    db.close()


def mkidx():
    db.execute_sql("CREATE INDEX event_sm_idx on event(state_machine_id);")
    db.execute_sql("CREATE INDEX event_time_idx on event(time);")
    db.execute_sql("CREATE INDEX event_relation_from_idx on event_relation(from_event_id);")
    db.execute_sql("CREATE INDEX event_relation_to_idx on event_relation(to_event_id);")
    db.execute_sql("CREATE INDEX sm_relation_from_idx on state_machine_relation(from_sm_id);")
    db.execute_sql("CREATE INDEX sm_relation_to_idx on state_machine_relation(to_sm_id);")


def line_nr(file: str) -> int:
    result = sp.run(['wc', file], stdout=sp.PIPE, text=True)
    return int(result.stdout.split()[0])


def load(pr: pr.parser, trace_path: str, fd_chunk_size=900, db_chunk_size=100):
    if not os.path.exists(trace_path):
        raise FileNotFoundError("`{trace_path}' not found!")

    with b.open(trace_path) as fd:
        for fd_chunk in p.chunked(fd, fd_chunk_size):
            records = pr.parse(fd_chunk)
            with db.atomic():
                for table in TABLES:
                    t_name: str = table._meta.name  # type: ignore
                    if t_name not in records:
                        continue
                    for db_chunk in p.chunked(records[t_name], db_chunk_size):
                        table.insert_many(
                            db_chunk,
                            fields=table._meta.sorted_fields,  # type: ignore
                        ).on_conflict_ignore().execute()


def iterate(origin: int, parent: None | int,
            visit: Callable, depth: int, depth_max: int, reverse=False):
    if depth_max < depth:
        return

    # pull events of this state machine, enriched with sm_type
    timeline = (event
                .select(event, state_machine.type.alias("sm_type"))
                .join(state_machine,
                      on=(event.state_machine_id == state_machine.id))
                .where(event.state_machine_id == origin)
                .dicts())
    visit(list(timeline), origin, parent)

    relation_column = (state_machine_relation.to_sm_id if reverse
                       else state_machine_relation.from_sm_id)
    related_column = (state_machine_relation.from_sm_id if reverse
                      else state_machine_relation.to_sm_id)
    relations = state_machine_relation.select().where(
        relation_column == origin)
    for relation in relations.dicts():
        relation_data = cast(dict[str, int], relation)
        related = relation_data[related_column.name]
        if VERBOSE:
            print(f"@[{depth}] {hex(origin)} ... {hex(related)}")
        iterate(related, origin, visit, depth + 1, depth_max, reverse)


def spans(event_begin: str, event_end: str, sm_type: str) -> list:
    sql = f"""
    SELECT (e2.time - e1.time) FROM event e1
    JOIN event e2 ON e2.state_machine_id = e1.state_machine_id
    JOIN state_machine sm ON sm.id = e1.state_machine_id
    WHERE e1.name="{event_begin}" AND e2.name="{event_end}"
    AND sm.type="{sm_type}";
    """
    return db.execute_sql(sql).fetchall()


def queues(event_begin: str, event_end: str, sm_type: str) -> list:
    sql = f"""
    SELECT (time/1000)*1000 as timer,
    COUNT(CASE WHEN name = "{event_begin}" THEN 1 END) as cc1,
    COUNT(CASE WHEN name = "{event_end}" THEN 1 END) as cc2
    FROM event JOIN state_machine sm ON sm.id = event.state_machine_id
    WHERE sm.type="{sm_type}" GROUP BY timer;
    """
    return db.execute_sql(sql).fetchall()
