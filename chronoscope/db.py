# -*- coding: utf-8 -*-
#
# This file is part of Chronoscope.
#
# SPDX-FileCopyrightText: 2024 Anatoliy Bilenko <anatoliy.bilenko@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

import chronoscope.parser as pr
from typing import Callable
import subprocess as sp
import builtins as b
import peewee as p
import os

db = p.SqliteDatabase(None)

class T(p.Model):
    class Meta:
        database = db
        primary_key = False

class tick(T):
    id = p.IntegerField()
    time = p.IntegerField()
    event = p.TextField()
    type = p.TextField()

class attr(T):
    id = p.IntegerField()
    name = p.TextField()
    val = p.TextField()

class relation(T):
    orig = p.IntegerField()
    dest = p.IntegerField()
    type = p.TextField()


TABLES = [tick, attr, relation]

def open(path: str, opts: None | dict[str, int | str] = None, create=False):
    if create and os.path.exists(path):
        raise FileExistsError("`{path}' exists!")
    if not create and not os.path.exists(path):
        raise FileNotFoundError("`{path}' not found!")

    db.init(path, opts)
    db.connect()
    if create:
        with db:
            db.create_tables(TABLES)

def close():
    db.close()

def mkidx():
    db.execute_sql("CREATE INDEX tick_idx on tick(id);")
    db.execute_sql("CREATE INDEX relation_idx on relation(orig);")
    db.execute_sql("CREATE INDEX attr_idx on attr(id);")

def line_nr(file: str) -> int:
    result = sp.run(['wc', file], stdout=sp.PIPE, text=True)
    return int(result.stdout.split()[0])

def load(pr: pr.parser, trace_path: str, fd_chunk_size=100, db_chunk_size=10):
    if not os.path.exists(trace_path):
        raise FileNotFoundError("`{trace_path}' not found!")

    with b.open(trace_path) as fd:
        for fd_chunk in p.chunked(fd, fd_chunk_size):
            records = pr.parse(fd_chunk)
            with db.atomic():
                for table in TABLES:
                    t_name: str = table._meta.name  # type: ignore
                    for db_chunk in p.chunked(records[t_name], db_chunk_size):
                        table.insert_many(db_chunk).execute()

def iterate(origin: int, parent: None | int, samples: type[tick] | type[attr],
            visit: Callable, depth: int, depth_max: int):
    if depth_max < depth:
        return

    # pull origin
    if timeline := samples.select().where((samples.id == origin)):
        visit(timeline.dicts(), origin, parent)

    # pull children
    orig_to_children = relation.select().where((relation.orig == origin))
    for child in orig_to_children.dicts():
        print(f"@[{depth}] {hex(child['orig'])} ... {hex(child['dest'])} ...")
        iterate(child["dest"], origin, samples, visit, depth + 1, depth_max)
