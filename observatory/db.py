# -*- coding: utf-8 -*-
#
# This file is part of Observatory.
#
# SPDX-FileCopyrightText: 2024 Anatoliy Bilenko <anatoliy.bilenko@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

import observatory.parser as pr
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


tables = [tick, attr, relation]

def open(db_path: str, db_opts: dict[str, int | str] = {}, create=False):
    if create and os.path.exists(db_path):
        raise FileExistsError("`{db_path}' exists!")

    db.init(db_path, db_opts)
    db.connect()
    if create:
        with db:
            db.create_tables(tables)

def close():
    db.close()

def mkidx():
    db.execute_sql("CREATE INDEX tick_idx on tick(id);")
    db.execute_sql("CREATE INDEX relation_idx on relation(orig);")
    db.execute_sql("CREATE INDEX attr_idx on attr(id);")

def line_nr(file: str) -> int:
    result = sp.run(['wc', file], stdout=sp.PIPE, text=True)
    return int(result.stdout.split()[0])

def load(pr: pr.parser, spans_path: str, fd_chunk_size=100, db_chunk_size=10):
    if not os.path.exists(spans_path):
        raise FileNotFoundError("`{spans_path}' not found!")

    with b.open(spans_path) as fd:
        for fd_chunk in p.chunked(fd, fd_chunk_size):
            records = pr.parse(fd_chunk)
            with db.atomic():
                for table in tables:
                    t_name: str = table._meta.name  # type: ignore
                    for db_chunk in p.chunked(records[t_name], db_chunk_size):
                        table.insert_many(db_chunk).execute()
