# -*- coding: utf-8 -*-
#
# This file is part of Observatory.
#
# SPDX-FileCopyrightText: 2024 Anatoliy Bilenko <anatoliy.bilenko@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

from datetime import datetime as t
import sys

fmt_ms = "%Y-%m-%dT%H:%M:%S.%f"
fmt_ms_compact = ":%S.%f"
max_int = sys.maxsize
min_int = -sys.maxsize - 1
bits_per_pid = 8
db_int_size = 64


def pack_unpack_init(p_bits_per_pid: int, p_db_int_size: int):
    global bits_per_pid, db_int_size
    bits_per_pid = p_bits_per_pid
    db_int_size = p_db_int_size

def pack(id: int, pid: int) -> int:
    masked_pid = ((1 << bits_per_pid) - 1) & pid
    packed_pid = masked_pid << (db_int_size - bits_per_pid)
    packed_id = ((1 << (db_int_size - bits_per_pid)) - 1) & id
    return (packed_pid | packed_id)

def unpack(id_pid: int) -> tuple[int, int]:
    pid = id_pid >> (db_int_size - bits_per_pid)
    id = ((1 << (db_int_size - bits_per_pid)) - 1) & id_pid
    return id, pid

def ns(time: str) -> int:
    ms = int(t.strptime(time[:-3], fmt_ms).timestamp() * 1e6)
    return ms * 1_000 + int(time[-3:])

def strns(unix_time: int, compact=False) -> str:
    dt = t.utcfromtimestamp(unix_time / 1e9)
    if compact:
        return dt.strftime(fmt_ms_compact)
    return dt.strftime(fmt_ms)
