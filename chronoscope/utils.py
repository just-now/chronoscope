# -*- coding: utf-8 -*-
#
# This file is part of Chronoscope.
#
# SPDX-FileCopyrightText: 2024 Anatoliy Bilenko <anatoliy.bilenko@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

from datetime import datetime as t
import sys

NS_TIME_LEN = len("2055-11-29T20:57:56.489282133")
FMT_MS = "%Y-%m-%dT%H:%M:%S.%f"
FMT_MS_COMPACT = ":%S.%f"
MAX_INT = sys.maxsize
MIN_INT = -sys.maxsize - 1
BITS_PER_PID = 8
DB_INT_SIZE = 64


def pack_unpack_init(p_bits_per_pid: int, p_db_int_size: int):
    global BITS_PER_PID, DB_INT_SIZE
    BITS_PER_PID = p_bits_per_pid
    DB_INT_SIZE = p_db_int_size

def pack(id: int, pid: int) -> int:
    masked_pid = ((1 << BITS_PER_PID) - 1) & pid
    packed_pid = masked_pid << (DB_INT_SIZE - BITS_PER_PID)
    packed_id = ((1 << (DB_INT_SIZE - BITS_PER_PID)) - 1) & id
    return (packed_pid | packed_id)

def unpack(id_pid: int) -> tuple[int, int]:
    pid = id_pid >> (DB_INT_SIZE - BITS_PER_PID)
    id = ((1 << (DB_INT_SIZE - BITS_PER_PID)) - 1) & id_pid
    return pid, id

def ns(time: str) -> int:
    if len(time) != NS_TIME_LEN:
        raise ValueError("Not a nanosecond time format")
    ms = int(t.strptime(time[:-3], FMT_MS).timestamp() * 1e6)
    return ms * 1_000 + int(time[-3:])

def str_ns(unix_time_ns: int, compact=False) -> str:
    dt = t.utcfromtimestamp(unix_time_ns / 1e9)
    if compact:
        return dt.strftime(FMT_MS_COMPACT)
    return dt.strftime(FMT_MS)

def str_ns_diff(unix_time_ns: int) -> str:
    return str(unix_time_ns) + "ns"
